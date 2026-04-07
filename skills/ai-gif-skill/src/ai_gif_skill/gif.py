from __future__ import annotations

from pathlib import Path

from PIL import Image


def _slice_sheet(sheet: Image.Image, *, rows: int, cols: int) -> list[Image.Image]:
    width, height = sheet.size
    if width % cols != 0 or height % rows != 0:
        raise ValueError("Sheet dimensions must divide evenly by rows and cols.")
    frame_width = width // cols
    frame_height = height // rows
    frames: list[Image.Image] = []
    for row in range(rows):
        for col in range(cols):
            left = col * frame_width
            top = row * frame_height
            frames.append(sheet.crop((left, top, left + frame_width, top + frame_height)))
    return frames


def assemble_gif_from_sheet(
    *,
    sheet_path: Path,
    output_path: Path,
    rows: int,
    cols: int,
    duration_ms: int = 120,
    loop: int = 0,
) -> dict[str, object]:
    sheet = Image.open(sheet_path).convert("RGBA")
    frames = _slice_sheet(sheet, rows=rows, cols=cols)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=loop,
        disposal=2,
        optimize=True,
    )
    return {
        "sheet_path": str(sheet_path),
        "output_path": str(output_path),
        "frames": len(frames),
        "duration_ms": duration_ms,
        "loop": loop,
        "frame_width": frames[0].width,
        "frame_height": frames[0].height,
    }
