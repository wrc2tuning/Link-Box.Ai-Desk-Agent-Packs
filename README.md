# Link-Box.Ai Desk Agent Packs

Character and voice packs for the Master Harness desk companion (the transparent
figure that stands on your desktop, listens on a hotkey and talks back through a
local model). Packs are the swap points: install one and the companion changes
its look or its voice without touching anything else.

```
master-harness voice packs install <id>            # from packs/index.json (sha256 verified)
master-harness voice packs use --character <id> --voice <id>
```

The Windows installer offers the packs listed here on its "Character and voice"
page; macOS and Linux hosts install them with the same command.

## Layout

| Path | What |
|---|---|
| `packs/index.json` | the catalogue the installer and `voice packs install` read (id, kind, version, release asset URL, sha256, bytes) |
| `schema/*.schema.json` | the manifest contracts (`character.json`, `voice.json`, `index.json`) |
| `characters/<id>/` | the text side of a character pack: `character.json`, `preview.png`, `LICENSE` |
| `voices/<id>/` | the text side of a voice pack: `voice.json`, `fillers.json`, `preview.wav`, `LICENSE`, `ATTRIBUTION.md` |
| GitHub Releases | the binaries: `character-<id>-<version>.zip` (rigged GLB) and `voice-<id>-<version>.zip` (GPT-SoVITS checkpoints, reference clip, rendered fillers) |

Binaries never live in git (`scripts/check-no-large-binaries.py` refuses them);
the zips are release assets and `packs/index.json` pins their sha256 and size.

## Formats

**Character pack**: a rigged GLB plus `character.json` (clip catalogue, pools,
click zones, look-at bone weights, rig bone map, edge/scale constants). Tripo
biped rigs with the 21 `preset:biped:*` animations work out of the box;
`scripts/character-from-glb.py` in the harness drafts the manifest for other
rigs (Mixamo, Biped, Reallusion names are mapped) and
`blender/transplant_clips.py` copies clips between rigs that share a skeleton.

**Voice pack**: GPT-SoVITS v2 checkpoints (`*-gpt.ckpt`, `*-sovits.pth`), a 1-15 s
reference clip with its transcript, the persona (system prompt, Modelfile
system text, click lines) and the pre-rendered filler lines with a lock that
ties every wav to its text and checkpoint.

`packs-v0` ships characters only. The plan for the first public voice packs
(and the harness work they need) is [docs/expand-voice-options.md](docs/expand-voice-options.md).

## Publishing a pack

1. Build the zip with the harness: `master-harness voice packs build character <dir> --glb <glb>` or `... build voice <dir>`.
2. Attach the zip to a release tagged `packs-v<N>`.
3. Add the text side under `characters/<id>/` or `voices/<id>/`, and the row to
   `packs/index.json` (`master-harness voice packs index dist/*.zip --base-url <release download prefix>`).
4. CI validates the manifests on every PR and, on a `packs-v*` tag, verifies each
   index row against the release asset (sha256 and size).

## Licensing

Every manifest carries `license.spdx`, `license.redistributable` and
`license.source`. Only packs whose source material allows redistribution are
listed here; the rest stay private (`redistributable: false`) and are
installed from a local zip.
