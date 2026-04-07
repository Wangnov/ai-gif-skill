from pathlib import Path

from PIL import Image

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


def test_write_template_assets_defaults_to_guided_png_grid(tmp_path: Path) -> None:
    svg_path = tmp_path / "sheet.svg"
    png_path = tmp_path / "sheet.png"
    spec = GridSpec(rows=2, cols=4, cell_width=100, cell_height=80, gutter=0, margin=0)

    metadata = write_template_assets(
        spec=spec,
        background="#00FF00",
        svg_path=svg_path,
        png_path=png_path,
    )

    image = Image.open(png_path).convert("RGB")

    assert metadata["guide_grid"] is True
    assert metadata["guide_color"] != "#00FF00"
    assert image.getpixel((0, 0)) == (0, 255, 0)
    assert image.getpixel((100, 40)) != (0, 255, 0)
    assert image.getpixel((200, 40)) != (0, 255, 0)
    assert image.getpixel((50, 80)) != (0, 255, 0)


def test_write_template_assets_can_disable_guided_png_grid(tmp_path: Path) -> None:
    svg_path = tmp_path / "sheet.svg"
    png_path = tmp_path / "sheet.png"
    spec = GridSpec(rows=2, cols=4, cell_width=100, cell_height=80, gutter=0, margin=0)

    metadata = write_template_assets(
        spec=spec,
        background="#00FF00",
        svg_path=svg_path,
        png_path=png_path,
        guide_grid=False,
    )

    image = Image.open(png_path).convert("RGB")

    assert metadata["guide_grid"] is False
    assert metadata["guide_color"] is None
    assert image.getpixel((100, 40)) == (0, 255, 0)
    assert image.getpixel((50, 80)) == (0, 255, 0)


def test_write_template_assets_embeds_layout_metadata_in_png(tmp_path: Path) -> None:
    svg_path = tmp_path / "sheet.svg"
    png_path = tmp_path / "sheet.png"
    spec = GridSpec(rows=3, cols=3, cell_width=96, cell_height=64, gutter=0, margin=0)

    write_template_assets(
        spec=spec,
        background="#00FF00",
        svg_path=svg_path,
        png_path=png_path,
    )

    with Image.open(png_path) as image:
        assert image.info["ai_gif_skill_rows"] == "3"
        assert image.info["ai_gif_skill_cols"] == "3"
        assert image.info["ai_gif_skill_cell_width"] == "96"
        assert image.info["ai_gif_skill_cell_height"] == "64"
        assert image.info["ai_gif_skill_background"] == "#00FF00"
