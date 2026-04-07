import io
import json
from pathlib import Path

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
