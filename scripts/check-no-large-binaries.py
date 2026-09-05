#!/usr/bin/env python3
"""Refuse model binaries and large files in git: they belong in GitHub Releases."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {".glb", ".gltf", ".fbx", ".ckpt", ".pth", ".pt", ".safetensors", ".bin", ".zip", ".7z", ".tar", ".gz"}
ALLOWED_AUDIO_BYTES = 2 * 1024 * 1024  # preview.wav / filler wavs stay small
MAX_BYTES = 5 * 1024 * 1024


def tracked() -> list[Path]:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    return [ROOT / name for name in out.split("\0") if name]


def main() -> int:
    bad = []
    for path in tracked():
        if not path.is_file():
            continue
        size = path.stat().st_size
        if path.suffix.lower() in FORBIDDEN:
            bad.append(f"{path.relative_to(ROOT)}: {path.suffix} files are release assets, not git content")
        elif path.suffix.lower() == ".wav" and size > ALLOWED_AUDIO_BYTES:
            bad.append(f"{path.relative_to(ROOT)}: wav over 2 MB")
        elif size > MAX_BYTES:
            bad.append(f"{path.relative_to(ROOT)}: {size} bytes over the 5 MB limit")
    for line in bad:
        print(line, file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
