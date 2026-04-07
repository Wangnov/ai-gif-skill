from __future__ import annotations

from pathlib import Path
from typing import Callable

from PIL import Image


def run_cutout(
    *,
    input_path: Path,
    output_path: Path,
    model: str = "isnet-anime",
    remove_background: Callable[..., bytes] | None = None,
) -> dict[str, object]:
    source_bytes = input_path.read_bytes()
    if remove_background is None:
        from rembg import new_session, remove

        session = new_session(model)
        result_bytes = remove(source_bytes, session=session)
    else:
        result_bytes = remove_background(source_bytes, model=model)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result_bytes)
    with Image.open(output_path) as image:
        width, height = image.size
        mode = image.mode
    return {
        "input_path": str(input_path),
        "output_path": str(output_path),
        "model": model,
        "width": width,
        "height": height,
        "mode": mode,
    }
