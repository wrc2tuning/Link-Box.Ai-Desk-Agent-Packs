#!/usr/bin/env python3
"""Verify every packs/index.json row against its release asset (sha256 and size).

    scripts/verify-release.py [--tag packs-v1]

Downloads each asset URL to a temporary file, hashes it and compares with the
index; with --tag it also refuses URLs that do not point at that release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256_url(url: str) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(url, timeout=60) as response, tempfile.TemporaryFile() as _:
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag")
    args = parser.parse_args()
    index = json.loads((ROOT / "packs" / "index.json").read_text(encoding="utf-8"))
    failures = 0
    for item in index.get("packs") or []:
        url = str(item["url"])
        if args.tag and f"/releases/download/{args.tag}/" not in url:
            print(f"{item['kind']}/{item['id']}: url is not under release {args.tag}: {url}", file=sys.stderr)
            failures += 1
            continue
        try:
            digest, size = sha256_url(url)
        except Exception as exc:  # noqa: BLE001
            print(f"{item['kind']}/{item['id']}: download failed: {exc}", file=sys.stderr)
            failures += 1
            continue
        ok = digest == item["sha256"] and size == int(item["bytes"])
        print(f"{item['kind']}/{item['id']}: {'ok' if ok else 'MISMATCH'} sha256={digest[:16]} bytes={size}")
        if not ok:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
