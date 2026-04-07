import io
import json
from pathlib import Path

from ai_gif_skill.cli import main


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
