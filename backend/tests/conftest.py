"""Test isolation.

Runs BEFORE any `app.*` import (pytest loads conftest first), so `Settings()` in
app/config.py picks these up instead of the real values. Without this, `pytest`
writes into the dev database: it leaves rows behind, renames seeded candidates,
and - worst - the high candidate_ids the delete tests insert become the new
max, so the next real upload jumps from 0000013 to 8000002.
"""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="inteltion-tests-")

os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["UPLOAD_DIR"] = os.path.join(_tmp, "uploads")
