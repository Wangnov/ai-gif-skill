# CLI Contract

## Primary stance

This CLI is agent-first. Prefer stable file paths and stable JSON over conversational output.

## Commands

### `template`

Purpose: write a keyed SVG template and, optionally, a PNG export with guide lines enabled by default.

Primary outputs:

- `command`
- `rows`
- `cols`
- `cell_width`
- `cell_height`
- `sheet_width`
- `sheet_height`
- `background`
- `guide_grid`
- `guide_color`
- `guide_thickness`
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

Purpose: remove the solid-color background with color keying by default, or with `rembg` when explicitly requested.

Primary outputs:

- `command`
- `input_path`
- `output_path`
- `mode`
- `model`
- `background_color`
- `tolerance`
- `width`
- `height`
- `image_mode`

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
