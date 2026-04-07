from pathlib import Path

from PIL import Image

from ai_gif_skill.gif import assemble_gif_from_sheet


def test_assemble_gif_from_sheet_slices_frames_in_row_major_order(tmp_path: Path) -> None:
    sheet_path = tmp_path / "sheet.png"
    gif_path = tmp_path / "sheet.gif"
    sheet = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    colors = [
        (255, 0, 0, 255),
        (0, 255, 0, 255),
        (0, 0, 255, 255),
        (255, 255, 0, 255),
    ]
    positions = [(0, 0), (10, 0), (0, 10), (10, 10)]
    for color, (x, y) in zip(colors, positions, strict=True):
        tile = Image.new("RGBA", (10, 10), color)
        sheet.alpha_composite(tile, (x, y))
    sheet.save(sheet_path)

    metadata = assemble_gif_from_sheet(
        sheet_path=sheet_path,
        output_path=gif_path,
        rows=2,
        cols=2,
        duration_ms=90,
    )

    gif = Image.open(gif_path)
    gif.seek(0)
    first = gif.convert("RGBA")
    gif.seek(1)
    second = gif.convert("RGBA")

    assert metadata["frames"] == 4
    assert metadata["duration_ms"] == 90
    assert gif.n_frames == 4
    assert first.getpixel((5, 5))[:3] == (255, 0, 0)
    assert second.getpixel((5, 5))[:3] == (0, 255, 0)
