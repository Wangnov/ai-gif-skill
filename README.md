# AI GIF Skill Repo

This repository is structured as a `skills.sh`-style skills collection.

Install the skill with:

```bash
npx skills add <owner>/<repo> --skill ai-gif-skill
```

The installable skill lives at:

```text
skills/ai-gif-skill
```

## What v2 Adds

The skill is now a provider-agnostic media-to-GIF toolkit with two supported workflows:

1. `sheet -> cutout -> gif`
2. `image -> video -> frames -> cutout -> gif`

Generation stages can use Gemini or Grok independently. Local post-processing stages stay provider-neutral.

## Main Commands

- `template`
- `generate-sheet`
- `generate-image`
- `generate-video`
- `extract-frames`
- `cutout`
- `cutout-frames`
- `gif-from-sheet`
- `gif-from-frames`
- `sheet-pipeline`
- `video-pipeline`

Legacy aliases are still supported:

- `generate` -> `generate-sheet`
- `gif` -> `gif-from-sheet`

## Practical Notes

- The default `template.png` still uses darker green guide lines on top of the chroma background so sheet generation stays layout-stable.
- The template, generated sheet, and cutout sheet PNGs still carry layout metadata. `generate-sheet` and `gif-from-sheet` validate it.
- Frame-based workflows write a `frames_manifest.json` next to the extracted or cutout frame directory.
- Inside the skill project root, you can run `uv run ai-gif-skill ...`.
- From an arbitrary working directory after installation, prefer `uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill ...`.
- In `codex exec`, use one shell command per exec call and keep artifacts on disk instead of doing multi-step cleanup.

## Sheet Workflow Example

```bash
mkdir -p /tmp/ai-gif-demo/out
cd /tmp/ai-gif-demo

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill template \
  --rows 2 \
  --cols 4 \
  --output-svg ./out/template.svg \
  --output-png ./out/template.png

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill generate-sheet \
  --provider gemini \
  --input-image ./out/template.png \
  --output-image ./out/generated.png \
  --rows 2 \
  --cols 4 \
  --prompt 'one original cute beast, pokemon-inspired, 2D cel-shaded, non-pixel-art'

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill cutout \
  --input-image ./out/generated.png \
  --output-image ./out/cutout.png

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill gif-from-sheet \
  --input-sheet ./out/cutout.png \
  --output-gif ./out/final.gif \
  --rows 2 \
  --cols 4
```

## Video Workflow Example

```bash
mkdir -p /tmp/ai-gif-video/out
cd /tmp/ai-gif-video

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill generate-image \
  --provider grok \
  --output-image ./out/character.png \
  --prompt 'an orange crab game asset on pure green background'

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill generate-video \
  --provider gemini \
  --output-video ./out/attack.mp4 \
  --prompt 'animate the crab performing a quick attack move' \
  --reference-image ./out/character.png \
  --duration-seconds 2 \
  --aspect-ratio 1:1

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill extract-frames \
  --input-video ./out/attack.mp4 \
  --output-dir ./out/frames

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill cutout-frames \
  --input-dir ./out/frames \
  --output-dir ./out/cutout-frames

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill gif-from-frames \
  --input-dir ./out/cutout-frames \
  --output-gif ./out/final.gif
```

## Validation

```bash
uv run --project skills/ai-gif-skill --extra dev pytest tests -q
uv run --project skills/ai-gif-skill --with pyyaml python /Users/wangnov/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/ai-gif-skill
```
