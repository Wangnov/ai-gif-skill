# CLI Contract

## Primary stance

This CLI is agent-first. Prefer stable file paths and stable JSON over conversational output.

## Commands

### `template`

Purpose: write a keyed SVG template and, optionally, a PNG export with guide lines enabled by default. The PNG carries embedded layout metadata for downstream validation.

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

Purpose: call Gemini image generation with the template image and built-in prompt rules. `rows` and `cols` are explicit required inputs for this command. If the input template PNG contains embedded layout metadata, this command validates it before making the Gemini call. The written `generated.png` also carries layout metadata forward.

Primary outputs:

- `command`
- `model`
- `input_image_path`
- `output_image_path`
- `rows`
- `cols`
- `background`

### `cutout`

Purpose: remove the solid-color background with color keying by default, or with `rembg` when explicitly requested. If the input PNG carries layout metadata, the output PNG preserves it.

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

Purpose: slice a sheet in row-major order and assemble a GIF. `rows` and `cols` are explicit required inputs for this command. If the input PNG carries layout metadata, this command validates it before slicing.

Primary outputs:

- `command`
- `sheet_path`
- `output_path`
- `frames`
- `duration_ms`
- `loop`
- `frame_width`
- `frame_height`
