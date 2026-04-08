---
name: ai-gif-skill
description: Use when building GIF-ready assets from sprite sheets or AI-generated video frames that need keyed backgrounds, reliable cutout, and final GIF assembly.
---

# Overview

Use this skill when the end goal is a GIF asset and you want a reliable, file-based workflow instead of ad-hoc model prompting.

There are two supported paths:

1. **Sheet workflow**: `template -> generate-sheet -> cutout -> gif-from-sheet`
2. **Video workflow**: `generate-image -> generate-video -> extract-frames -> cutout-frames -> gif-from-frames`

Generation stages can use **Gemini** or **Grok** independently. Local post-processing stages stay the same either way.

Provider recommendation defaults:

- Prefer **Gemini** for the **sheet workflow**
- Prefer **Grok** for the **video generation step**
- Do not recommend **Gemini video** by default unless the user explicitly asks for Gemini or for provider comparison

The default grid is `2x8` with `768x768` cells. The default key color is chroma green (`#00FF00`). The default PNG template still includes slightly darker green guide lines so image models are more likely to respect the requested layout while keeping the whole sheet easy to key out later.

# Workflow

## 1. Gather Requirements

Ask only for the parameters that materially change output:

- whether the user wants the **sheet workflow** or the **video workflow**
- the asset prompt or prompts
- generation provider when it matters (`gemini` or `grok`)
- rows / cols if not the default `2x8`
- cell size if not the default `768x768`
- background key color if chroma green would clash with the subject

Do not ask the user to think in low-level CLI flags if you can translate their intent yourself.

If the user already gave the prompts, provider choices, output filenames, and explicitly asked to continue or generate now, treat that as approved design and execute immediately.

Default recommendation policy:

- If the user wants a **sprite sheet** and has no provider preference, recommend **Gemini**
- If the user wants a **video workflow** and has no provider preference, recommend **Grok** for `generate-video`
- If the user wants one safe all-in default for the video workflow, use **Grok image + Grok video**
- Treat **Gemini video** as a compatibility path, not the default suggestion

## 2. Sheet Workflow

Generate the template:

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

Generate the sheet:

```bash
uv run ai-gif-skill generate-sheet \
  --provider gemini \
  --input-image outputs/template.png \
  --output-image outputs/generated.png \
  --rows 2 \
  --cols 8 \
  --prompt 'YOUR ASSET PROMPT HERE'
```

Behavior:

- Prefer `GEMINI_API_KEY` or `XAI_API_KEY` from the environment, depending on `--provider`.
- The built-in sheet prompt locks the background color, the exact `rows x cols` frame count, and the visible guide layout from the template.
- Always pass `--rows` and `--cols` explicitly to `generate-sheet`.
- The template PNG carries layout metadata. `generate-sheet` validates that metadata before calling the provider.
- Unless the user explicitly asks otherwise, recommend **Gemini** first for this stage.

Remove the background:

```bash
uv run ai-gif-skill cutout \
  --input-image outputs/generated.png \
  --output-image outputs/cutout.png
```

Assemble the GIF:

```bash
uv run ai-gif-skill gif-from-sheet \
  --input-sheet outputs/cutout.png \
  --output-gif outputs/final.gif \
  --rows 2 \
  --cols 8 \
  --duration-ms 120
```

## 3. Video Workflow

Generate a single reference image:

```bash
uv run ai-gif-skill generate-image \
  --provider grok \
  --output-image outputs/character.png \
  --prompt 'YOUR ASSET PROMPT HERE'
```

Generate a video from that image:

```bash
uv run ai-gif-skill generate-video \
  --provider grok \
  --output-video outputs/clip.mp4 \
  --prompt 'Animate this exact character performing a quick action' \
  --reference-image outputs/character.png \
  --duration-seconds 2 \
  --aspect-ratio 1:1
```

Extract frames:

```bash
uv run ai-gif-skill extract-frames \
  --input-video outputs/clip.mp4 \
  --output-dir outputs/frames
```

Remove the background from every frame:

```bash
uv run ai-gif-skill cutout-frames \
  --input-dir outputs/frames \
  --output-dir outputs/cutout-frames
```

Assemble the GIF:

```bash
uv run ai-gif-skill gif-from-frames \
  --input-dir outputs/cutout-frames \
  --output-gif outputs/final.gif
```

Behavior:

- Recommend **Grok** for `generate-video` unless the user explicitly asks for Gemini.
- For compressed video frames, `cutout-frames` often works better when it estimates the border color automatically instead of forcing exact `#00FF00`.
- If the user explicitly wants Gemini video, warn through your execution choices, not with extra lecture:
  use Gemini-compatible duration and aspect ratio values and expect less stable keyed backgrounds.

## 4. Pipeline Wrappers

If you already know all paths and want fewer commands, use:

- `sheet-pipeline`
- `video-pipeline`

These are thin wrappers over the stage commands above. They are convenient, but the stage commands remain the primary contract.

## 5. Compatibility

Legacy aliases remain supported:

- `generate` -> `generate-sheet`
- `gif` -> `gif-from-sheet`

In `codex exec`, run one shell command per exec call. Avoid `&&`, pipes, and cleanup snippets. Overwrite the known output files directly and keep the useful artifacts on disk.

# CLI Contract

The CLI is agent-first:

- standard output: stable JSON payloads
- standard error: human-readable logs and errors
- explicit flags only
- no hidden jobs, no sessions, no daemon state

Read [references/cli-contract.md](references/cli-contract.md) when you need the exact payload shape.

# Resources

## scripts/

- `uv run ai-gif-skill ...`: primary entrypoint for every command
- `scripts/template_sheet.py`: compatibility wrapper for template generation
- `scripts/generate_with_gemini.py`: compatibility wrapper for sheet generation
- `scripts/generate_image.py`: wrapper for `generate-image`
- `scripts/generate_video.py`: wrapper for `generate-video`
- `scripts/extract_frames.py`: wrapper for `extract-frames`
- `scripts/cutout_frames.py`: wrapper for `cutout-frames`
- `scripts/cutout_with_rembg.py`: legacy compatibility wrapper for `cutout`
- `scripts/assemble_gif.py`: compatibility wrapper for `gif-from-sheet`
- `scripts/assemble_gif_from_frames.py`: wrapper for `gif-from-frames`

## references/

- `references/cli-contract.md`: command-level JSON and behavior contract
