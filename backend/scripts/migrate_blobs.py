"""One-off: copy resume blobs from one Azure storage account to another and
rewrite the DB paths that point at them (F1).

Use this only if CVs were already uploaded into Inteltion's company storage
account before we moved to our own. Resume paths are referenced by candidate_id
and by `resume_versions.blob_path`, so hand-copying the container leaves the DB
pointing at blobs that are no longer where it thinks they are.

    cd backend
    python scripts/migrate_blobs.py \
        --source-connection-string "DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;..." \
        --source-container resumes \
        --dry-run

Drop --dry-run to actually copy. The source account is read-only here; nothing
is ever deleted from it.

The DESTINATION is whatever the app is configured for
(AZURE_STORAGE_CONNECTION_STRING / AZURE_STORAGE_CONTAINER_NAME), so the copy
lands exactly where the running API will look for it.
"""
from __future__ import annotations

import argparse
import sys

from app.config import settings
from app.database import SessionLocal
from app.models_db import Candidate, ResumeVersion
from app.storage import parse_account_name


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-connection-string", required=True,
                   help="Connection string for the account blobs are copied FROM.")
    p.add_argument("--source-container", default="resumes")
    p.add_argument("--dry-run", action="store_true",
                   help="List what would be copied and rewritten; change nothing.")
    return p


def main() -> int:
    args = build_argparser().parse_args()

    if not settings.azure_storage_connection_string:
        print("ERROR: AZURE_STORAGE_CONNECTION_STRING is not set - there is no "
              "destination account to copy into. Point .env at OUR account first.",
              file=sys.stderr)
        return 2

    src_account = parse_account_name(args.source_connection_string)
    dst_account = parse_account_name(settings.azure_storage_connection_string)
    if src_account == dst_account and args.source_container == settings.azure_storage_container_name:
        print(f"ERROR: source and destination are the same container "
              f"({src_account}/{args.source_container}). Nothing to do.", file=sys.stderr)
        return 2

    from azure.storage.blob import BlobServiceClient

    src = BlobServiceClient.from_connection_string(args.source_connection_string)
    dst = BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)
    src_container = src.get_container_client(args.source_container)
    dst_container = dst.get_container_client(settings.azure_storage_container_name)

    print(f"FROM {src_account}/{args.source_container}")
    print(f"TO   {dst_account}/{settings.azure_storage_container_name}")
    print(f"mode {'DRY RUN' if args.dry_run else 'COPY'}\n")

    if not args.dry_run:
        from azure.core.exceptions import ResourceExistsError
        try:
            dst_container.create_container()  # private, as always
        except ResourceExistsError:
            pass

    copied = skipped = 0
    for blob in src_container.list_blobs():
        target = dst_container.get_blob_client(blob.name)
        if target.exists():
            print(f"  skip (already there)  {blob.name}")
            skipped += 1
            continue
        print(f"  copy                  {blob.name}  ({blob.size} bytes)")
        copied += 1
        if not args.dry_run:
            data = src_container.get_blob_client(blob.name).download_blob().readall()
            target.upload_blob(data, overwrite=False)

    # `resume_url` is a SAS URL against the OLD account and expires anyway; it is
    # rewritten so nothing in the DB still names the company account. blob_path
    # is account-independent, so it does not change - which is exactly why the
    # copy must preserve blob names.
    db = SessionLocal()
    rewritten = 0
    try:
        for version in db.query(ResumeVersion).all():
            candidate = db.get(Candidate, version.candidate_id)
            if candidate is None:
                continue
            if src_account and src_account in (candidate.resume_url or ""):
                print(f"  rewrite resume_url    candidate={candidate.candidate_id}")
                rewritten += 1
                if not args.dry_run:
                    # Cleared rather than re-signed: GET /api/candidates/{id}/resume-url
                    # resolves a fresh SAS from blob_path on every call.
                    candidate.resume_url = ""
        if not args.dry_run:
            db.commit()
    finally:
        db.close()

    print(f"\n{copied} copied, {skipped} already present, {rewritten} resume_url cleared"
          f"{'  (dry run - nothing changed)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
