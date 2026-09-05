# Implementation Plan: Expanding Voice Options

This is the packs-repo plan for shipping more than the current character-only
catalogue. Voice *runtime* work lives in
[Master-Harness](https://github.com/wrc2tuning/Master-Harness); this repo is
the signed catalogue, text-side manifests, and release assets.

## Overview

`packs-v0` ships two character packs (`scary-optimus`, `stylized-boy`) and
zero voice packs. The installer and `voice packs install` already read
`packs/index.json`, and the voice contract is already in
`schema/voice.schema.json`. Expanding voice options means publishing
redistributable GPT-SoVITS packs that pair with those figures, then teaching
the harness to treat installed packs as the catalogue instead of a hardcoded
Mabel/system list.

The first public voices cannot be the existing Fish-distilled Mabel. That
checkpoint is a private offline copy of a hosted voice and fails the
`license.redistributable: true` gate this repo enforces.

## Specification link

| Source | What it defines |
|---|---|
| [README.md](../README.md) | Pack layout, publish steps, `voice packs install` / `use` |
| [schema/voice.schema.json](../schema/voice.schema.json) | `voice.json` contract (engine, persona, fillers, preview) |
| [schema/index.schema.json](../schema/index.schema.json) | Catalogue row (`kind: voice`) |
| [scripts/validate.py](../scripts/validate.py) | Requires `voices/<id>/voice.json` for every voice index row |
| Master-Harness `tooling/voice-companion` | Live TTS, hardcoded catalog, Mabel `local.json` |

## Current state

**This repo**

- `characters/` has two 1.0.0 packs on `packs-v0`.
- `voices/` is empty (scaffold `.gitkeep` only).
- Index `kind` already allows `"voice"`. Adding a row without
  `voices/<id>/voice.json` fails CI.
- Binaries stay out of git. A voice zip is checkpoints + reference clip +
  rendered fillers; git holds `voice.json`, `fillers.json`, `preview.wav`,
  `LICENSE`, `ATTRIBUTION.md`.

**Master-Harness (as of `a9cac7e`)**

- Catalogue is hardcoded in `tooling/voice-companion/config/defaults.json`:
  macOS `say` (System, Sandy, Kathy), Fish custom, `mabel-local`, Kokoro,
  MLX Audio; Linux Piper, Fish, Mabel, Kokoro.
- Overlay context menu lists those same ids in
  `tooling/voice-companion/overlay/src/main.ts`.
- `local_voice.py` and `gpt-sovits-speak.py` assume a single voice home:
  `~/.local/share/master-harness/voices/mabel`.
- `voice.py` exposes `status` / `start` / `stop` / `toggle` / `preview` /
  `tune`. The README commands `voice packs install|use|build|index` are
  specified here and are not implemented there yet.
- Talk persona is a single `VOICE_SYSTEM_PROMPT` in `session.py`. Pack
  `persona.system_prompt` / `click_lines` / `modelfile_system` are unused.
- Schema `engine.name` is locked to `gpt-sovits`. Other engines stay as
  host fallbacks, not catalogue packs, until a later schema bump.

**What already works as the swap point**

```
master-harness voice packs install <id>
master-harness voice packs use --character <id> --voice <id>
```

Install verifies sha256/size from this index. Use writes the active pair
without touching overlay code or the talk model.

## Goals

1. Ship at least two public voice packs on a `packs-v*` release, one that
   reads as a match for Scary Optimus and one for Stylized Boy, independently
   selectable.
2. Keep Mabel as a private/builtin pack (`engine.legacy_local_json`), never
   as a public index row, unless the owner later grants a redistributable
   license that is not Fish-derived.
3. Make the harness catalogue dynamic: installed pack ids appear in
   `voice status`, `voice tune --voice <id>`, and the overlay menu.
4. Load persona, fillers, and reference clip from the active pack so swapping
   a voice changes how the figure talks, not only the timbre.
5. Keep the Windows installer "Character and voice" page sourced from this
   index so new voices show up without an installer rebuild beyond a
   catalogue refresh.

Non-goals for the first expansion: new TTS engines in `voice.json`,
training on Apple Silicon, vendoring GPT-SoVITS pretrained weights, or
shipping Fish/Kokoro/Piper as pack zips.

## Technical approach

A voice pack is a persona + a GPT-SoVITS v2 checkpoint pair + a 1–15 s
reference clip + pre-rendered fillers. The figure (GLB) stays a character
pack. The two zip independently; `use` binds one of each.

```
voices/<id>/                         # git (text side)
  voice.json
  fillers.json
  preview.wav                        # ≤ 2 MB (check-no-large-binaries)
  LICENSE
  ATTRIBUTION.md

voice-<id>-<version>.zip             # GitHub Release asset
  voice.json
  <id>-gpt.ckpt
  <id>-sovits.pth
  ref.wav + transcript (engine.ref_text)
  fillers/*.wav
  fillers.lock.json                  # wav ↔ text ↔ checkpoint hash
```

Install destination on a host:

```
~/.local/share/master-harness/voices/<id>/
```

`local.json` (or the pack's `engine` block) must become per-id, not
Mabel-only. `gpt-sovits-speak.py` already takes `--local-json`; the missing
piece is resolving that path from the active `voice.id`.

Suggested first public roster (ids fit `^[a-z0-9-]{2,32}$`):

| id | Pairs with | Timbre | Source requirement |
|---|---|---|---|
| `optimus-desk` | `scary-optimus` | adult male, dry, slightly metallic | owner-recorded or commissioned; not a third-party actor without a grant |
| `stylized-boy` | `stylized-boy` | younger male, clear, mid | same |
| *(private)* `mabel` | any | existing Fish distill | `legacy_local_json`; omit from `packs/index.json` |

Character and voice may share an id (`stylized-boy`) because the index keys
on `(kind, id)`. Do not reuse an id across two voices.

## Phases

### Phase 0 — License and source gate

Nothing is trained or indexed until the owner confirms source material.

- [ ] Confirm Scary Optimus / Stylized Boy model licenses (still marked
      pre-release in `character.json`).
- [ ] Record or commission two English reference performances (several
      minutes of clean speech, plus a 4–10 s reference line). Prefer the
      owner or a contractor with a written redistribution grant.
- [ ] Refuse any corpus distilled from Fish, ElevenLabs, or another hosted
      TTS as a public pack. Private local copies stay under
      `legacy_local_json`.
- [ ] Write `ATTRIBUTION.md` + `license.source` *before* training so the
      zip cannot ship without provenance.
- [ ] Decide SPDX: owner-original work can stay `LicenseRef-Owner` to match
      the character packs; third-party work needs the actual license.

Acceptance: two source folders exist with wavs, transcripts, and a license
paragraph an outsider can audit.

### Phase 1 — Generalize training off the Mabel paths

Harness work (Master-Harness), not this repo.

- [ ] Parameterize `train-mabel-gptsovits.sh` / `distill-mabel-voice.sh` as
      `train-gptsovits.sh --voice <id>` writing
      `~/.local/share/master-harness/voices/<id>/`.
- [ ] Keep the desktop-CUDA-only rule. No Mac MPS train path.
- [ ] Few-shot defaults can stay near the Mabel recipe (SoVITS ~8 epochs,
      GPT ~15) until a pack fails quality review.
- [ ] Write `local.json` with `engine`, `gpt_path`, `sovits_path`,
      `ref_wav`, `ref_text`, `python`, `speak_script`.
- [ ] Audition with `master-harness voice preview --text "…" --out /tmp/x.wav`.
      Target: intelligible English, stable pitch, no long silence padding.

Acceptance: a non-Mabel id trains, writes `local.json`, and previews on
desktop without editing Mabel's tree.

### Phase 2 — First text-side voice packs in this repo

- [ ] Add `voices/optimus-desk/` and `voices/stylized-boy/` (or the chosen
      ids) with `voice.json` that passes `scripts/validate.py`.
- [ ] Required `voice.json` fields: `schema_version`, `kind`, `id`, `name`,
      `version` (`1.0.0`), `license`, `engine` (`gpt-sovits` + checkpoint
      filenames + `ref_wav` + `ref_text`), `persona` (`name` +
      `system_prompt` ≥ 20 chars).
- [ ] Fill persona for each pack:
      - `system_prompt` — spoken style (length, tone, no markup).
      - `modelfile_system` — optional Ollama/Modelfile overlay.
      - `click_lines.head|hand|torso` — one-liners for overlay click zones.
      - `style.max_words` / `max_sentences` — keep turns short (2–4
        sentences, matching the current companion).
- [ ] Add `fillers.json` (thinking / ack lines) and a short `preview.wav`.
- [ ] Add `LICENSE` and `ATTRIBUTION.md`.
- [ ] Do **not** add index rows until the release zip exists (Phase 4).
      `validate.py` will fail an index row whose `voices/<id>/voice.json`
      is missing, and `verify-release.py` will fail a row whose asset 404s.

Acceptance: `python3 scripts/validate.py` stays green with the new
manifests present and no index rows yet (or with rows only after the
release exists).

### Phase 3 — Harness pack install / use / build

Harness work. This is what makes "expanding options" show up in the UI.

- [ ] Implement `master-harness voice packs`:
      - `index` — emit `packs/index.json` rows from `dist/*.zip`.
      - `build voice <dir>` — zip checkpoints + ref + fillers; refuse
        missing `voice.json` / license.
      - `install <id>` — download the index URL, verify sha256 and bytes,
        unpack under `voices/<id>/`.
      - `use --character <id> --voice <id>` — write user
        `~/.config/master-harness/voice.json` plus the active character.
      - `list` — union of index, installed, and builtin/private.
- [ ] Replace the hardcoded overlay menu with `voice_catalog()` plus
      installed pack labels.
- [ ] Point `tts._gpt_sovits` at the active pack's `local.json` / engine
      block, not `voices/mabel`.
- [ ] Apply `persona.system_prompt` (and optional `modelfile_system`) in
      `session.system_prompt` when a pack is active. Keep the offline-facts
      appendix.
- [ ] Play `fillers` while the talk model is thinking; lock file must match
      the installed checkpoint hash or fillers are skipped.
- [ ] Windows installer "Character and voice" page reads this repo's
      `packs/index.json` (characters *and* voices). Preview uses
      `preview.wav` / `preview.png`.

Acceptance: after `install` + `use`, `voice status` reports the new id,
`preview` speaks it, overlay lists it, and Mabel still works as builtin.

### Phase 4 — Release `packs-v1` (or next tag)

- [ ] Build `voice-optimus-desk-1.0.0.zip` and
      `voice-stylized-boy-1.0.0.zip` on desktop.
- [ ] Attach both to a `packs-v*` GitHub Release (keep character zips or
      retarget their URLs if the tag changes).
- [ ] Add both rows to `packs/index.json` (`kind: voice`, sha256, bytes,
      preview URL, license).
- [ ] Bump `generated` / `release`.
- [ ] Tag; CI `verify-release` must download and match every row.

Acceptance: a clean host can
`voice packs install optimus-desk` and
`voice packs use --character scary-optimus --voice optimus-desk`.

### Phase 5 — Catalogue growth (after the first two)

Only after Phase 4 is boring.

- [ ] Third public voice with a distinct timbre (adult female or neutral)
      so the two characters are not the only pairing.
- [ ] Optional `aliases` on `voice.json` for installer search.
- [ ] Suggested pairings as non-binding metadata (e.g. index
      `requires.suggested_character`) — never a hard lock; `use` stays a
      free pair.
- [ ] Schema v2 only if a non-GPT-SoVITS engine needs to be a pack
      (Piper/Kokoro as tiny fallbacks). Until then those stay host engines.
- [ ] Filler coverage: greet, think, ack, click, error. Re-render and
      relock when the checkpoint changes.

## Dependencies

| Need | Where | Blocks |
|---|---|---|
| Redistributable speech source | owner | Phase 0–4 |
| Desktop CUDA + GPT-SoVITS checkout | fleet `desktop` | Phase 1, 4 |
| Harness `voice packs` CLI | Master-Harness | Phase 3–5 (install/use) |
| `packs-v*` release permissions | this GitHub repo | Phase 4 |
| Character license confirmation | owner | public installer listing |

This repo can land Phase 2 manifests and this plan without the harness CLI.
It cannot land index rows or a useful installer page without Phase 3–4.

## Risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| Fish-derived Mabel leaks into the public index | License + hosted-TTS ToS | `validate.py` already requires `redistributable: true`; keep Mabel on `legacy_local_json` only |
| Checkpoint zips are large | Release bandwidth, installer time | One v2 pair per pack; no pretrained SoVITS tree; document size in the index `bytes` field |
| Hardcoded Mabel paths | New packs install but never speak | Phase 3 must land before calling the catalogue "expanded" |
| Persona ignored | Voice changes timbre but not character | Load `persona` in `session.system_prompt`; test click lines |
| Filler lock drift | Wrong wav after a retrain | Skip fillers when lock ≠ installed sha256; rebuild fillers with the zip |
| Schema engine lock | Temptation to pack Piper/Kokoro | Leave them as host fallbacks; bump `schema_version` only with a harness reader |
| Index row before the asset exists | `verify-release` / install fail | Add git manifests first; add index rows in the same commit as the tag |
| Shared id confusion | `stylized-boy` as both kinds | Allowed; UI must show kind. Never two voices with the same id |

## Suggested implementation order for a follow-up agent

1. This repo: text-side `voices/<id>/` for the two public packs (Phase 2)
   once Phase 0 source exists.
2. Master-Harness: per-id `local.json` + `voice packs` CLI + dynamic
   catalogue (Phase 3).
3. This repo: build zips, tag, index rows (Phase 4).
4. Stop. Do not add a third voice until install/use is proven on a clean
   host.

## Out of scope notes

- Notion task board was requested by the planning skill but the Notion MCP
  session is unauthenticated; this document is the plan of record.
- No voice binaries or checkpoints are added by this plan.
