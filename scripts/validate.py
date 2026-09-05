#!/usr/bin/env python3
"""Validate packs/index.json and every characters/*/character.json, voices/*/voice.json.

Mirrors the hand-rolled validators in the Master Harness (voice_companion/packs.py)
so this repo needs no dependency beyond the standard library.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^[a-z0-9-]{2,32}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
POOLS = ("rest", "listen", "watching", "think", "speak", "work")


def common(doc: dict, kind: str, label: str) -> list[str]:
    errors = []
    if doc.get("schema_version") != 1:
        errors.append(f"{label}: schema_version must be 1")
    if doc.get("kind") != kind:
        errors.append(f"{label}: kind must be {kind}")
    if not ID_RE.match(str(doc.get("id") or "")):
        errors.append(f"{label}: bad id")
    if not SEMVER_RE.match(str(doc.get("version") or "")):
        errors.append(f"{label}: version must be semver")
    license_ = doc.get("license") or {}
    if not license_.get("spdx") or "redistributable" not in license_:
        errors.append(f"{label}: license needs spdx and redistributable")
    elif license_.get("redistributable") is not True:
        errors.append(f"{label}: only redistributable packs belong in this repo")
    return errors


def validate_character(doc: dict, label: str) -> list[str]:
    errors = common(doc, "character", label)
    clips = doc.get("clips") or {}
    loops = list(clips.get("loops") or [])
    known = set(loops) | set(clips.get("one_shots") or [])
    if not loops:
        errors.append(f"{label}: clips.loops is empty")
    for key in POOLS:
        members = (clips.get("pools") or {}).get(key) or []
        if not members:
            errors.append(f"{label}: clips.pools.{key} missing")
        elif any(m not in loops for m in members):
            errors.append(f"{label}: clips.pools.{key} uses non-loops")
    for zone, names in (clips.get("click") or {}).items():
        if any(n not in known for n in names):
            errors.append(f"{label}: clips.click.{zone} names unknown clips")
    rig = doc.get("rig") or {}
    for key in ("root", "pelvis", "feet", "arms", "look"):
        if not rig.get(key):
            errors.append(f"{label}: rig.{key} missing")
    if not str((doc.get("model") or {}).get("file") or "").endswith(".glb"):
        errors.append(f"{label}: model.file must be a .glb")
    return errors


def validate_voice(doc: dict, label: str) -> list[str]:
    errors = common(doc, "voice", label)
    engine = doc.get("engine") or {}
    if engine.get("name") != "gpt-sovits":
        errors.append(f"{label}: engine.name must be gpt-sovits")
    for key in ("gpt", "sovits", "ref_wav", "ref_text"):
        if not engine.get(key):
            errors.append(f"{label}: engine.{key} missing")
    if len(str((doc.get("persona") or {}).get("system_prompt") or "")) < 20:
        errors.append(f"{label}: persona.system_prompt too short")
    return errors


def validate_index(doc: dict) -> list[str]:
    errors = []
    if doc.get("schema_version") != 1:
        errors.append("index: schema_version must be 1")
    seen = set()
    for item in doc.get("packs") or []:
        label = f"index {item.get('kind')}/{item.get('id')}"
        if item.get("kind") not in ("character", "voice"):
            errors.append(f"{label}: bad kind")
        if not ID_RE.match(str(item.get("id") or "")):
            errors.append(f"{label}: bad id")
        if (item.get("kind"), item.get("id")) in seen:
            errors.append(f"{label}: duplicate")
        seen.add((item.get("kind"), item.get("id")))
        if not SEMVER_RE.match(str(item.get("version") or "")):
            errors.append(f"{label}: version must be semver")
        if not str(item.get("url") or "").startswith("https://"):
            errors.append(f"{label}: url must be https")
        if not SHA_RE.match(str(item.get("sha256") or "")):
            errors.append(f"{label}: sha256 must be 64 hex")
        if not isinstance(item.get("bytes"), int) or item["bytes"] <= 0:
            errors.append(f"{label}: bytes must be positive")
        folder = ROOT / ("characters" if item.get("kind") == "character" else "voices") / str(item.get("id"))
        manifest = folder / ("character.json" if item.get("kind") == "character" else "voice.json")
        if not manifest.is_file():
            errors.append(f"{label}: {manifest.relative_to(ROOT)} missing")
        else:
            doc_ = json.loads(manifest.read_text(encoding="utf-8"))
            if doc_.get("version") != item.get("version"):
                errors.append(f"{label}: index version {item.get('version')} != manifest {doc_.get('version')}")
    return errors


def main() -> int:
    errors: list[str] = []
    index = json.loads((ROOT / "packs" / "index.json").read_text(encoding="utf-8"))
    errors += validate_index(index)
    for path in sorted((ROOT / "characters").glob("*/character.json")):
        errors += validate_character(json.loads(path.read_text(encoding="utf-8")), str(path.relative_to(ROOT)))
    for path in sorted((ROOT / "voices").glob("*/voice.json")):
        errors += validate_voice(json.loads(path.read_text(encoding="utf-8")), str(path.relative_to(ROOT)))
    for line in errors:
        print(line, file=sys.stderr)
    print(f"{len(index.get('packs') or [])} index rows, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
