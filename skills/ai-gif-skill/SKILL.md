---
name: ai-gif-skill
description: Use when building sprite-sheet animation assets from AI-generated frames that need a pure key-color template, reliable solid-color background removal, or final GIF assembly.
---

# Overview

Use this skill to turn an animation idea into a keyed sprite sheet and final GIF with a predictable four-step workflow:

1. Generate a keyed SVG/PNG template.
2. Generate the sprite sheet with Gemini.
3. Remove the solid-color background with color keying.
4. Slice the sheet and assemble a GIF.

The default grid is `2x8` with `768x768` cells. The default key color is chroma green (`#00FF00`). The default PNG template also includes slightly darker green guide lines so image models are more likely to respect the requested layout while still keeping the whole sheet easy to key out later. Switch to chroma blue only when the subject itself contains a lot of green.

# Workflow

## 1. Gather Requirements

Ask only for the parameters that materially change output:

- asset prompt
- rows / cols if not the default `2x8`
- cell size if not the default `768x768`
- background key color if chroma green would clash with the subject

Do not ask the user to think in low-level CLI flags if you can translate their intent yourself.

## 2. Generate the Template

If you are already inside the skill root, run:

```bash
uv run ai-gif-skill template \
  --rows 2 \
  --cols 8 \
  --cell-width 768 \
  --cell-height 768 \
  --background '#00FF00' \
  --output-svg outputs/template.svg \
  --output-png outputs/template.png
```

From an arbitrary output directory after installation, use:

```bash
uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill template \
  --rows 2 \
  --cols 8 \
  --cell-width 768 \
  --cell-height 768 \
  --background '#00FF00' \
  --output-svg ./out/template.svg \
  --output-png ./out/template.png
```

The PNG now contains visible green-on-green guide lines by default. Keep them on unless you have a strong reason to disable them with `--no-guide-grid`; they materially improve layout adherence in real image generation runs. The SVG still carries invisible cell metadata.

## 3. Generate the Sprite Sheet with Gemini

Run:

```bash
uv run ai-gif-skill generate \
  --input-image outputs/template.png \
  --output-image outputs/generated.png \
  --prompt 'YOUR ASSET PROMPT HERE'
```

Behavior:

- Prefer `GEMINI_API_KEY` from the environment.
- If it is missing, the script prompts for it.
- The built-in prompt template locks the background color, locks the exact `rows x cols` frame count, and tells the model to follow the visible guide grid from the input template image.

If you need longer prompts, write them to a file and pass `--prompt-file`.

When using `codex exec` from a throwaway work directory, explicitly tell the agent to call the installed project with `uv run --project ~/.agents/skills/ai-gif-skill ai-gif-skill ...`. Otherwise `uv run ai-gif-skill ...` may fail because the current directory is not the skill project.

## 4. Remove the Background

Run:

```bash
uv run ai-gif-skill cutout \
  --input-image outputs/generated.png \
  --output-image outputs/cutout.png
```

Default behavior is `--mode color`, which samples the border color and removes that keyed background. This is the best default for AI frames generated from a pure-color sheet.

Use extra flags only when you need them:

- leave `--background-color` unset when the generated background drifted slightly and you want auto-detection
- pass `--background-color '#00FF00'` when you know the exact key color
- raise `--tolerance` when a little fringe remains around the subject
- switch to `--mode rembg --model isnet-anime` only when the background is no longer a reliable solid color

Real-world fallback pattern:

- if the first generation ignores the requested layout, regenerate from the same template with a stricter prompt that repeats the exact `rows x cols` requirement
- if the first cutout leaves a faint green fringe, raise `--tolerance` slightly before considering any other approach

## 5. Assemble the GIF

Run:

```bash
uv run ai-gif-skill gif \
  --input-sheet outputs/cutout.png \
  --output-gif outputs/final.gif \
  --rows 2 \
  --cols 8 \
  --duration-ms 120
```

This slices frames in row-major order.

# CLI Contract

The CLI is agent-first:

- standard output: stable JSON payloads
- standard error: human-readable logs and errors
- explicit flags only
- no hidden jobs, no sessions, no daemon state

Read [references/cli-contract.md](references/cli-contract.md) only when you need the exact payload shape or command-by-command contract.

# Resources

## scripts/

- `uv run ai-gif-skill ...`: primary entrypoint for every command
- `scripts/template_sheet.py`: compatibility wrapper for template generation
- `scripts/generate_with_gemini.py`: compatibility wrapper for Gemini generation
- `scripts/cutout_with_rembg.py`: legacy compatibility wrapper for the `cutout` command
- `scripts/assemble_gif.py`: compatibility wrapper for GIF assembly

## references/

- `references/cli-contract.md`: command-level JSON and behavior contract
