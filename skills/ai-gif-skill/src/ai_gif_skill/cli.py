from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from .cutout import DEFAULT_CUTOUT_MODE, DEFAULT_CUTOUT_TOLERANCE, run_cutout
from .generate import GenerationRequest, generate_sheet_with_gemini
from .gif import assemble_gif_from_sheet
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-gif-skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    template_parser = subparsers.add_parser("template")
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

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--input-image", type=Path, required=True)
    generate_parser.add_argument("--output-image", type=Path, required=True)
    generate_parser.add_argument("--prompt")
    generate_parser.add_argument("--prompt-file", type=Path)
    generate_parser.add_argument("--background", default=DEFAULT_KEY_COLOR)
    generate_parser.add_argument("--rows", type=int, required=True)
    generate_parser.add_argument("--cols", type=int, required=True)
    generate_parser.add_argument("--cell-width", type=int, default=DEFAULT_CELL_WIDTH)
    generate_parser.add_argument("--cell-height", type=int, default=DEFAULT_CELL_HEIGHT)
    generate_parser.add_argument("--model", default="gemini-2.5-flash-image")
    generate_parser.add_argument("--api-key")

    cutout_parser = subparsers.add_parser("cutout")
    cutout_parser.add_argument("--input-image", type=Path, required=True)
    cutout_parser.add_argument("--output-image", type=Path, required=True)
    cutout_parser.add_argument("--mode", choices=("color", "rembg"), default=DEFAULT_CUTOUT_MODE)
    cutout_parser.add_argument("--model", default="isnet-anime")
    cutout_parser.add_argument("--background-color")
    cutout_parser.add_argument("--tolerance", type=int, default=DEFAULT_CUTOUT_TOLERANCE)

    gif_parser = subparsers.add_parser("gif")
    gif_parser.add_argument("--input-sheet", type=Path, required=True)
    gif_parser.add_argument("--output-gif", type=Path, required=True)
    gif_parser.add_argument("--rows", type=int, required=True)
    gif_parser.add_argument("--cols", type=int, required=True)
    gif_parser.add_argument("--duration-ms", type=int, default=120)
    gif_parser.add_argument("--loop", type=int, default=0)

    return parser


def _read_prompt(args: argparse.Namespace) -> str:
    if args.prompt:
        return args.prompt
    if args.prompt_file:
        return args.prompt_file.read_text(encoding="utf-8").strip()
    raise ValueError("Either --prompt or --prompt-file is required.")


def main(argv: list[str] | None = None, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "template":
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
        elif args.command == "generate":
            request = GenerationRequest(
                prompt=_read_prompt(args),
                background=args.background,
                rows=args.rows,
                cols=args.cols,
                cell_width=args.cell_width,
                cell_height=args.cell_height,
            )
            payload = generate_sheet_with_gemini(
                input_image_path=args.input_image,
                output_image_path=args.output_image,
                request=request,
                model=args.model,
                api_key=args.api_key,
            )
            payload["command"] = "generate"
        elif args.command == "cutout":
            payload = run_cutout(
                input_path=args.input_image,
                output_path=args.output_image,
                mode=args.mode,
                model=args.model,
                background_color=args.background_color,
                tolerance=args.tolerance,
            )
            payload["command"] = "cutout"
        else:
            payload = assemble_gif_from_sheet(
                sheet_path=args.input_sheet,
                output_path=args.output_gif,
                rows=args.rows,
                cols=args.cols,
                duration_ms=args.duration_ms,
                loop=args.loop,
            )
            payload["command"] = "gif"
        json.dump(payload, stdout, ensure_ascii=False)
        stdout.write("\n")
        return 0
    except Exception as exc:  # pragma: no cover - exercised in integration use
        stderr.write(f"{type(exc).__name__}: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
