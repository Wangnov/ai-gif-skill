# CLI Contract

## Primary stance

This CLI is agent-first. Prefer stable file paths and stable JSON over conversational output.

## Commands

### `template`

Purpose: write a keyed SVG template and, optionally, a PNG export.

Primary outputs:

- `command`
- `rows`
- `cols`
- `cell_width`
- `cell_height`
- `sheet_width`
- `sheet_height`
- `background`
- `svg_path`
- `png_path`

### `generate`

Purpose: call Gemini image generation with the template image and built-in prompt rules.

Primary outputs:

- `command`
- `model`
- `input_image_path`
- `output_image_path`
- `rows`
- `cols`
- `background`

### `cutout`

Purpose: remove the solid-color background with rembg.

Primary outputs:

- `command`
- `input_path`
- `output_path`
- `model`
- `width`
- `height`
- `mode`

### `gif`

Purpose: slice a sheet in row-major order and assemble a GIF.

Primary outputs:

- `command`
- `sheet_path`
- `output_path`
- `frames`
- `duration_ms`
- `loop`
- `frame_width`
- `frame_height`
