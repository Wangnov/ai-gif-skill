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

### `generate-sheet`

Purpose: call the selected image provider with a template image and built-in sheet prompt rules. `rows` and `cols` are explicit required inputs for this command. If the input template PNG contains embedded layout metadata, this command validates it before the provider call. The written `generated.png` also carries layout metadata forward.

Primary outputs:

- `command`
- `provider`
- `model`
- `input_image_path`
- `output_image_path`
- `rows`
- `cols`
- `background`

Legacy alias: `generate`

### `generate-image`

Purpose: call the selected image provider to write one prompt-driven PNG without requiring sheet metadata.

Primary outputs:

- `command`
- `provider`
- `model`
- `input_image_path`
- `output_image_path`

### `generate-video`

Purpose: call the selected video provider to write one MP4, optionally conditioned on a reference image.

Primary outputs:

- `command`
- `provider`
- `model`
- `output_path`
- `reference_image_path`
- `duration_seconds`
- `aspect_ratio`
- `resolution`

### `extract-frames`

Purpose: turn one input video into a frame directory plus `frames_manifest.json`.

Primary outputs:

- `command`
- `video_path`
- `output_dir`
- `frame_count`
- `fps`
- `source_type`
- `source_path`
- `width`
- `height`

### `cutout`

Purpose: remove the solid-color background from one image with color keying by default, or with `rembg` when explicitly requested. If the input PNG carries layout metadata, the output PNG preserves it.

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

### `cutout-frames`

Purpose: remove keyed backgrounds from every frame in an input directory and write a matching output frame directory plus manifest.

Primary outputs:

- `command`
- `input_dir`
- `output_dir`
- `frame_count`
- `fps`
- `mode`
- `background_color`
- `tolerance`

### `gif-from-sheet`

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

Legacy alias: `gif`

### `gif-from-frames`

Purpose: assemble a GIF from a frame directory in lexical frame order.

Primary outputs:

- `command`
- `frames_dir`
- `output_path`
- `frames`
- `duration_ms`
- `loop`
- `frame_width`
- `frame_height`

### `sheet-pipeline`

Purpose: run `generate-sheet -> cutout -> gif-from-sheet` as one wrapper command.

Primary outputs:

- `command`
- `provider`
- `stages`
- `artifacts`
- `final_output_path`

### `video-pipeline`

Purpose: run `generate-image -> generate-video -> extract-frames -> cutout-frames -> gif-from-frames` as one wrapper command.

Primary outputs:

- `command`
- `image_provider`
- `video_provider`
- `stages`
- `artifacts`
- `final_output_path`
