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

Local verification examples:

```bash
uv run --project skills/ai-gif-skill --extra dev pytest tests
uv run --project skills/ai-gif-skill --with pyyaml python /Users/wangnov/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/ai-gif-skill
```

Practical usage notes:

- The default `template.png` now includes darker green guide lines on top of the chroma background. This makes image models much more likely to keep the requested `rows x cols` layout, and the color-key cutout still removes it well.
- The template, generated, and cutout PNG files now carry layout metadata. `generate` and `gif` validate that metadata so a mismatched grid fails loudly instead of silently drifting to the wrong layout.
- Inside the skill project root, you can run `uv run ai-gif-skill ...`.
- From an arbitrary working directory after installation, prefer `uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill ...`.
- For layout-sensitive runs, pass `--rows` and `--cols` explicitly to `template`, `generate`, and `gif`. `3x3` is valid when that is the requested layout; the important thing is strict consistency across the whole chain.
- `ai-gif-skill generate` is a local CLI command. You do not need separate browser or `web-access` setup for it.
- In `codex exec`, use one shell command per exec call. Avoid `&&`, cleanup scripts, and `rm`-style post-run deletion; overwrite the known output paths and only make sure `./out` holds the final five files.
- For color-key cleanup, keep it conservative: default cutout first, then at most one small `tolerance` retry if the edge still shows green. Do not iterate through many trial PNGs in the working directory.

Example from an empty output directory:

```bash
mkdir -p /tmp/ai-gif-demo/out
cd /tmp/ai-gif-demo

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill template \
  --rows 2 \
  --cols 4 \
  --output-svg ./out/template.svg \
  --output-png ./out/template.png

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill generate \
  --input-image ./out/template.png \
  --output-image ./out/generated.png \
  --rows 2 \
  --cols 4 \
  --prompt 'one original cute beast, pokemon-inspired, 2D cel-shaded, non-pixel-art'

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill cutout \
  --input-image ./out/generated.png \
  --output-image ./out/cutout.png

uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill gif \
  --input-sheet ./out/cutout.png \
  --output-gif ./out/final.gif \
  --rows 2 \
  --cols 4
```
