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
- Inside the skill project root, you can run `uv run ai-gif-skill ...`.
- From an arbitrary working directory after installation, prefer `uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill ...`.

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
