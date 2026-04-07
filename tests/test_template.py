from pathlib import Path

from ai_gif_skill.template import GridSpec, write_template_assets


def test_write_template_assets_uses_requested_grid_and_key_color(tmp_path: Path) -> None:
    svg_path = tmp_path / "sheet.svg"
    png_path = tmp_path / "sheet.png"
    spec = GridSpec(rows=2, cols=8, cell_width=768, cell_height=768, gutter=0, margin=0)

    metadata = write_template_assets(
        spec=spec,
        background="#00FF00",
        svg_path=svg_path,
        png_path=png_path,
    )

    svg_text = svg_path.read_text(encoding="utf-8")

    assert metadata["sheet_width"] == 6144
    assert metadata["sheet_height"] == 1536
    assert metadata["background"] == "#00FF00"
    assert 'width="6144"' in svg_text
    assert 'height="1536"' in svg_text
    assert "#00FF00" in svg_text
    assert png_path.exists()
