from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from .cutout import DEFAULT_CUTOUT_MODE, DEFAULT_CUTOUT_TOLERANCE, run_cutout, run_cutout_frames
from .frames import extract_frames
from .generate import GenerationRequest, generate_image, generate_sheet, resolve_provider_name
from .gif import assemble_gif_from_frames, assemble_gif_from_sheet
from .providers.base import DEFAULT_PROVIDER_NAME
from .pipelines import SheetPipelineRequest, VideoPipelineRequest, run_sheet_pipeline, run_video_pipeline
from .template import (
    DEFAULT_CELL_HEIGHT,
    DEFAULT_CELL_WIDTH,
    DEFAULT_COLS,
    DEFAULT_GUIDE_GRID,
    DEFAULT_KEY_COLOR,
    DEFAULT_ROWS,
    GridSpec,
    write_template_assets,
)
from .video import VideoGenerationRequest, generate_video


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-gif-skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    template_parser = subparsers.add_parser("template")
    template_parser.set_defaults(command_impl="template")
    template_parser.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    template_parser.add_argument("--cols", type=int, default=DEFAULT_COLS)
    template_parser.add_argument("--cell-width", type=int, default=DEFAULT_CELL_WIDTH)
    template_parser.add_argument("--cell-height", type=int, default=DEFAULT_CELL_HEIGHT)
    template_parser.add_argument("--gutter", type=int, default=0)
    template_parser.add_argument("--margin", type=int, default=0)
    template_parser.add_argument("--background", default=DEFAULT_KEY_COLOR)
    template_parser.add_argument("--no-guide-grid", action="store_false", dest="guide_grid", default=DEFAULT_GUIDE_GRID)
    template_parser.add_argument("--output-svg", type=Path, required=True)
    template_parser.add_argument("--output-png", type=Path)

    generate_sheet_parser = subparsers.add_parser("generate-sheet", aliases=["generate"])
    generate_sheet_parser.set_defaults(command_impl="generate-sheet")
    generate_sheet_parser.add_argument("--input-image", type=Path, required=True)
    generate_sheet_parser.add_argument("--output-image", type=Path, required=True)
    generate_sheet_parser.add_argument("--prompt")
    generate_sheet_parser.add_argument("--prompt-file", type=Path)
    generate_sheet_parser.add_argument("--background", default=DEFAULT_KEY_COLOR)
    generate_sheet_parser.add_argument("--rows", type=int, required=True)
    generate_sheet_parser.add_argument("--cols", type=int, required=True)
    generate_sheet_parser.add_argument("--cell-width", type=int, default=DEFAULT_CELL_WIDTH)
    generate_sheet_parser.add_argument("--cell-height", type=int, default=DEFAULT_CELL_HEIGHT)
    generate_sheet_parser.add_argument("--provider", default=DEFAULT_PROVIDER_NAME)
    generate_sheet_parser.add_argument("--model")
    generate_sheet_parser.add_argument("--api-key")

    generate_image_parser = subparsers.add_parser("generate-image")
    generate_image_parser.set_defaults(command_impl="generate-image")
    generate_image_parser.add_argument("--output-image", type=Path, required=True)
    generate_image_parser.add_argument("--prompt")
    generate_image_parser.add_argument("--prompt-file", type=Path)
    generate_image_parser.add_argument("--background", default=DEFAULT_KEY_COLOR)
    generate_image_parser.add_argument("--provider", default=DEFAULT_PROVIDER_NAME)
    generate_image_parser.add_argument("--input-image", type=Path)
    generate_image_parser.add_argument("--model")
    generate_image_parser.add_argument("--api-key")

    generate_video_parser = subparsers.add_parser("generate-video")
    generate_video_parser.set_defaults(command_impl="generate-video")
    generate_video_parser.add_argument("--output-video", type=Path, required=True)
    generate_video_parser.add_argument("--prompt")
    generate_video_parser.add_argument("--prompt-file", type=Path)
    generate_video_parser.add_argument("--provider", default=DEFAULT_PROVIDER_NAME)
    generate_video_parser.add_argument("--model")
    generate_video_parser.add_argument("--api-key")
    generate_video_parser.add_argument("--duration-seconds", type=int, default=2)
    generate_video_parser.add_argument("--reference-image", type=Path)
    generate_video_parser.add_argument("--aspect-ratio")
    generate_video_parser.add_argument("--resolution")

    cutout_parser = subparsers.add_parser("cutout")
    cutout_parser.set_defaults(command_impl="cutout")
    cutout_parser.add_argument("--input-image", type=Path, required=True)
    cutout_parser.add_argument("--output-image", type=Path, required=True)
    cutout_parser.add_argument("--mode", choices=("color", "rembg"), default=DEFAULT_CUTOUT_MODE)
    cutout_parser.add_argument("--model", default="isnet-anime")
    cutout_parser.add_argument("--background-color")
    cutout_parser.add_argument("--tolerance", type=int, default=DEFAULT_CUTOUT_TOLERANCE)

    extract_frames_parser = subparsers.add_parser("extract-frames")
    extract_frames_parser.set_defaults(command_impl="extract-frames")
    extract_frames_parser.add_argument("--input-video", type=Path, required=True)
    extract_frames_parser.add_argument("--output-dir", type=Path, required=True)
    extract_frames_parser.add_argument("--fps", type=float)

    cutout_frames_parser = subparsers.add_parser("cutout-frames")
    cutout_frames_parser.set_defaults(command_impl="cutout-frames")
    cutout_frames_parser.add_argument("--input-dir", type=Path, required=True)
    cutout_frames_parser.add_argument("--output-dir", type=Path, required=True)
    cutout_frames_parser.add_argument("--mode", choices=("color", "rembg"), default=DEFAULT_CUTOUT_MODE)
    cutout_frames_parser.add_argument("--model", default="isnet-anime")
    cutout_frames_parser.add_argument("--background-color")
    cutout_frames_parser.add_argument("--tolerance", type=int, default=DEFAULT_CUTOUT_TOLERANCE)

    gif_sheet_parser = subparsers.add_parser("gif-from-sheet", aliases=["gif"])
    gif_sheet_parser.set_defaults(command_impl="gif-from-sheet")
    gif_sheet_parser.add_argument("--input-sheet", type=Path, required=True)
    gif_sheet_parser.add_argument("--output-gif", type=Path, required=True)
    gif_sheet_parser.add_argument("--rows", type=int, required=True)
    gif_sheet_parser.add_argument("--cols", type=int, required=True)
    gif_sheet_parser.add_argument("--duration-ms", type=int, default=120)
    gif_sheet_parser.add_argument("--loop", type=int, default=0)

    gif_frames_parser = subparsers.add_parser("gif-from-frames")
    gif_frames_parser.set_defaults(command_impl="gif-from-frames")
    gif_frames_parser.add_argument("--input-dir", type=Path, required=True)
    gif_frames_parser.add_argument("--output-gif", type=Path, required=True)
    gif_frames_parser.add_argument("--duration-ms", type=int, default=120)
    gif_frames_parser.add_argument("--loop", type=int, default=0)

    sheet_pipeline_parser = subparsers.add_parser("sheet-pipeline")
    sheet_pipeline_parser.set_defaults(command_impl="sheet-pipeline")
    sheet_pipeline_parser.add_argument("--template-image", type=Path, required=True)
    sheet_pipeline_parser.add_argument("--generated-image", type=Path, required=True)
    sheet_pipeline_parser.add_argument("--cutout-image", type=Path, required=True)
    sheet_pipeline_parser.add_argument("--output-gif", type=Path, required=True)
    sheet_pipeline_parser.add_argument("--prompt")
    sheet_pipeline_parser.add_argument("--prompt-file", type=Path)
    sheet_pipeline_parser.add_argument("--rows", type=int, required=True)
    sheet_pipeline_parser.add_argument("--cols", type=int, required=True)
    sheet_pipeline_parser.add_argument("--cell-width", type=int, default=DEFAULT_CELL_WIDTH)
    sheet_pipeline_parser.add_argument("--cell-height", type=int, default=DEFAULT_CELL_HEIGHT)
    sheet_pipeline_parser.add_argument("--background", default=DEFAULT_KEY_COLOR)
    sheet_pipeline_parser.add_argument("--provider", default=DEFAULT_PROVIDER_NAME)
    sheet_pipeline_parser.add_argument("--model")
    sheet_pipeline_parser.add_argument("--api-key")
    sheet_pipeline_parser.add_argument("--duration-ms", type=int, default=120)
    sheet_pipeline_parser.add_argument("--loop", type=int, default=0)

    video_pipeline_parser = subparsers.add_parser("video-pipeline")
    video_pipeline_parser.set_defaults(command_impl="video-pipeline")
    video_pipeline_parser.add_argument("--generated-image", type=Path, required=True)
    video_pipeline_parser.add_argument("--generated-video", type=Path, required=True)
    video_pipeline_parser.add_argument("--frames-dir", type=Path, required=True)
    video_pipeline_parser.add_argument("--cutout-frames-dir", type=Path, required=True)
    video_pipeline_parser.add_argument("--output-gif", type=Path, required=True)
    video_pipeline_parser.add_argument("--image-prompt")
    video_pipeline_parser.add_argument("--image-prompt-file", type=Path)
    video_pipeline_parser.add_argument("--video-prompt")
    video_pipeline_parser.add_argument("--video-prompt-file", type=Path)
    video_pipeline_parser.add_argument("--provider")
    video_pipeline_parser.add_argument("--image-provider")
    video_pipeline_parser.add_argument("--video-provider")
    video_pipeline_parser.add_argument("--image-model")
    video_pipeline_parser.add_argument("--video-model")
    video_pipeline_parser.add_argument("--image-api-key")
    video_pipeline_parser.add_argument("--video-api-key")
    video_pipeline_parser.add_argument("--duration-seconds", type=int, default=2)
    video_pipeline_parser.add_argument("--aspect-ratio")
    video_pipeline_parser.add_argument("--resolution")
    video_pipeline_parser.add_argument("--fps", type=float)
    video_pipeline_parser.add_argument("--duration-ms", type=int, default=120)
    video_pipeline_parser.add_argument("--loop", type=int, default=0)

    return parser


def _read_prompt(args: argparse.Namespace) -> str:
    if args.prompt:
        return args.prompt
    if args.prompt_file:
        return args.prompt_file.read_text(encoding="utf-8").strip()
    raise ValueError("Either --prompt or --prompt-file is required.")


def _read_named_prompt(args: argparse.Namespace, text_attr: str, file_attr: str) -> str:
    text_value = getattr(args, text_attr, None)
    if text_value:
        return text_value
    file_value = getattr(args, file_attr, None)
    if file_value:
        return file_value.read_text(encoding="utf-8").strip()
    raise ValueError(f"Either --{text_attr.replace('_', '-')} or --{file_attr.replace('_', '-')} is required.")


def main(argv: list[str] | None = None, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        command_impl = getattr(args, "command_impl", args.command)
        if command_impl == "template":
            spec = GridSpec(
                rows=args.rows,
                cols=args.cols,
                cell_width=args.cell_width,
                cell_height=args.cell_height,
                gutter=args.gutter,
                margin=args.margin,
            )
            payload = write_template_assets(
                spec=spec,
                background=args.background,
                svg_path=args.output_svg,
                png_path=args.output_png,
                guide_grid=args.guide_grid,
            )
            payload["command"] = "template"
        elif command_impl == "generate-sheet":
            provider = resolve_provider_name(args.provider)
            request = GenerationRequest(
                prompt=_read_prompt(args),
                background=args.background,
                rows=args.rows,
                cols=args.cols,
                cell_width=args.cell_width,
                cell_height=args.cell_height,
            )
            payload = generate_sheet(
                input_image_path=args.input_image,
                output_image_path=args.output_image,
                request=request,
                provider=provider,
                model=args.model,
                api_key=args.api_key,
            )
            payload["command"] = command_impl
            payload["provider"] = provider
        elif command_impl == "generate-image":
            provider = resolve_provider_name(args.provider)
            payload = generate_image(
                output_image_path=args.output_image,
                prompt=_read_prompt(args),
                provider=provider,
                model=args.model,
                api_key=args.api_key,
                input_image_path=args.input_image,
            )
            payload["command"] = command_impl
            payload["provider"] = provider
        elif command_impl == "generate-video":
            provider = resolve_provider_name(args.provider)
            payload = generate_video(
                request=VideoGenerationRequest(
                    prompt=_read_prompt(args),
                    duration_seconds=args.duration_seconds,
                    output_path=args.output_video,
                    reference_image_path=args.reference_image,
                    aspect_ratio=args.aspect_ratio,
                    resolution=args.resolution,
                ),
                provider=provider,
                model=args.model,
                api_key=args.api_key,
            )
            payload["command"] = command_impl
            payload["provider"] = provider
        elif command_impl == "cutout":
            payload = run_cutout(
                input_path=args.input_image,
                output_path=args.output_image,
                mode=args.mode,
                model=args.model,
                background_color=args.background_color,
                tolerance=args.tolerance,
            )
            payload["command"] = "cutout"
        elif command_impl == "extract-frames":
            payload = extract_frames(
                video_path=args.input_video,
                output_dir=args.output_dir,
                fps=args.fps,
            )
            payload["command"] = command_impl
        elif command_impl == "cutout-frames":
            payload = run_cutout_frames(
                input_dir=args.input_dir,
                output_dir=args.output_dir,
                mode=args.mode,
                model=args.model,
                background_color=args.background_color,
                tolerance=args.tolerance,
            )
            payload["command"] = command_impl
        elif command_impl == "gif-from-frames":
            payload = assemble_gif_from_frames(
                frames_dir=args.input_dir,
                output_path=args.output_gif,
                duration_ms=args.duration_ms,
                loop=args.loop,
            )
            payload["command"] = command_impl
        elif command_impl == "sheet-pipeline":
            provider = resolve_provider_name(args.provider)
            payload = run_sheet_pipeline(
                request=SheetPipelineRequest(
                    template_image_path=args.template_image,
                    generated_image_path=args.generated_image,
                    cutout_image_path=args.cutout_image,
                    output_gif_path=args.output_gif,
                    generation=GenerationRequest(
                        prompt=_read_prompt(args),
                        background=args.background,
                        rows=args.rows,
                        cols=args.cols,
                        cell_width=args.cell_width,
                        cell_height=args.cell_height,
                    ),
                    duration_ms=args.duration_ms,
                    loop=args.loop,
                ),
                provider=provider,
                model=args.model,
                api_key=args.api_key,
            )
            payload["command"] = command_impl
        elif command_impl == "video-pipeline":
            payload = run_video_pipeline(
                request=VideoPipelineRequest(
                    generated_image_path=args.generated_image,
                    generated_video_path=args.generated_video,
                    frames_dir=args.frames_dir,
                    cutout_frames_dir=args.cutout_frames_dir,
                    output_gif_path=args.output_gif,
                    image_prompt=_read_named_prompt(args, "image_prompt", "image_prompt_file"),
                    video_prompt=_read_named_prompt(args, "video_prompt", "video_prompt_file"),
                    duration_seconds=args.duration_seconds,
                    aspect_ratio=args.aspect_ratio,
                    resolution=args.resolution,
                    fps=args.fps,
                    duration_ms=args.duration_ms,
                    loop=args.loop,
                ),
                provider=args.provider,
                image_provider=args.image_provider,
                video_provider=args.video_provider,
                image_model=args.image_model,
                video_model=args.video_model,
                image_api_key=args.image_api_key,
                video_api_key=args.video_api_key,
            )
            payload["command"] = command_impl
        else:
            payload = assemble_gif_from_sheet(
                sheet_path=args.input_sheet,
                output_path=args.output_gif,
                rows=args.rows,
                cols=args.cols,
                duration_ms=args.duration_ms,
                loop=args.loop,
            )
            payload["command"] = command_impl
        json.dump(payload, stdout, ensure_ascii=False)
        stdout.write("\n")
        return 0
    except Exception as exc:  # pragma: no cover - exercised in integration use
        stderr.write(f"{type(exc).__name__}: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
