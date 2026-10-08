"""Copy the contract files the backend reads at RUNTIME from the repo-root
shared-contracts/ (source of truth) into backend/contracts/ (what gets deployed).

Run after editing shared-contracts/schema.json or mock-candidates.json:
    python scripts/sync_contracts.py          # copy
    python scripts/sync_contracts.py --check  # exit 1 if the copies are stale
"""
import filecmp
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "..", "shared-contracts"))
DST = os.path.abspath(os.path.join(HERE, "..", "contracts"))
FILES = ["schema.json", "mock-candidates.json"]


def main() -> int:
    check = "--check" in sys.argv
    os.makedirs(DST, exist_ok=True)
    stale = []
    for name in FILES:
        src, dst = os.path.join(SRC, name), os.path.join(DST, name)
        if not os.path.exists(dst) or not filecmp.cmp(src, dst, shallow=False):
            stale.append(name)
            if not check:
                shutil.copyfile(src, dst)
    if check:
        print("stale: " + ", ".join(stale) if stale else "contracts in sync")
        return 1 if stale else 0
    print("synced: " + (", ".join(stale) if stale else "nothing to do"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
