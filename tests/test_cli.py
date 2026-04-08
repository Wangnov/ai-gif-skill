import io
import json
from pathlib import Path

import pytest

from ai_gif_skill.cli import build_parser, main


def test_template_command_emits_json_summary(tmp_path: Path) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    svg_path = tmp_path / "sheet.svg"
    png_path = tmp_path / "sheet.png"

    exit_code = main(
        [
            "template",
            "--output-svg",
            str(svg_path),
            "--output-png",
            str(png_path),
        ],
        stdout=stdout,
        stderr=stderr,
    )

    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["command"] == "template"
    assert payload["rows"] == 2
    assert payload["cols"] == 8
    assert svg_path.exists()
    assert png_path.exists()


def test_cutout_command_exposes_color_mode_options(tmp_path: Path) -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "cutout",
            "--input-image",
            str(tmp_path / "input.png"),
            "--output-image",
            str(tmp_path / "output.png"),
        ]
    )

    assert args.mode == "color"
    assert args.background_color is None
    assert args.tolerance > 0


def test_template_command_enables_guide_grid_by_default(tmp_path: Path) -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "template",
            "--output-svg",
            str(tmp_path / "sheet.svg"),
        ]
    )

    assert args.guide_grid is True


def test_template_command_can_disable_guide_grid(tmp_path: Path) -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "template",
            "--output-svg",
            str(tmp_path / "sheet.svg"),
            "--no-guide-grid",
        ]
    )

    assert args.guide_grid is False


def test_generate_command_requires_explicit_rows_and_cols(tmp_path: Path) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "generate",
                "--input-image",
                str(tmp_path / "template.png"),
                "--output-image",
                str(tmp_path / "generated.png"),
                "--prompt",
                "test",
            ]
        )


def test_generate_sheet_command_accepts_provider_flag(tmp_path: Path) -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "generate-sheet",
            "--input-image",
            str(tmp_path / "template.png"),
            "--output-image",
            str(tmp_path / "generated.png"),
            "--prompt",
            "test",
            "--rows",
            "2",
            "--cols",
            "4",
            "--provider",
            "gemini",
        ]
    )

    assert args.command == "generate-sheet"
    assert args.command_impl == "generate-sheet"
    assert args.provider == "gemini"


def test_generate_image_command_accepts_provider_flag_without_grid(tmp_path: Path) -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "generate-image",
            "--output-image",
            str(tmp_path / "generated.png"),
            "--prompt",
            "test",
            "--provider",
            "gemini",
        ]
    )

    assert args.command == "generate-image"
    assert args.command_impl == "generate-image"
    assert args.provider == "gemini"


def test_generate_alias_maps_to_generate_sheet_mode(tmp_path: Path) -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "generate",
            "--input-image",
            str(tmp_path / "template.png"),
            "--output-image",
            str(tmp_path / "generated.png"),
            "--prompt",
            "test",
            "--rows",
            "2",
            "--cols",
            "4",
        ]
    )

    assert args.command == "generate"
    assert args.command_impl == "generate-sheet"


def test_gif_command_requires_explicit_rows_and_cols(tmp_path: Path) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "gif",
                "--input-sheet",
                str(tmp_path / "cutout.png"),
                "--output-gif",
                str(tmp_path / "final.gif"),
            ]
        )
