from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Mapping

from PIL import Image
from PIL.PngImagePlugin import PngInfo

_ROWS_KEY = "ai_gif_skill_rows"
_COLS_KEY = "ai_gif_skill_cols"
_CELL_WIDTH_KEY = "ai_gif_skill_cell_width"
_CELL_HEIGHT_KEY = "ai_gif_skill_cell_height"
_BACKGROUND_KEY = "ai_gif_skill_background"


@dataclass(frozen=True)
class SheetLayoutMetadata:
    rows: int
    cols: int
    cell_width: int | None = None
    cell_height: int | None = None
    background: str | None = None


def _parse_required_int(info: Mapping[str, object], key: str) -> int:
    value = info.get(key)
    if value is None:
        raise ValueError(f"Missing required layout metadata field: {key}")
    return int(str(value))


def _parse_optional_int(info: Mapping[str, object], key: str) -> int | None:
    value = info.get(key)
    if value is None:
        return None
    return int(str(value))


def read_sheet_layout_metadata(source: Path | Image.Image) -> SheetLayoutMetadata | None:
    if isinstance(source, Path):
        with Image.open(source) as image:
            info = dict(image.info)
    else:
        info = dict(source.info)

    if _ROWS_KEY not in info or _COLS_KEY not in info:
        return None

    return SheetLayoutMetadata(
        rows=_parse_required_int(info, _ROWS_KEY),
        cols=_parse_required_int(info, _COLS_KEY),
        cell_width=_parse_optional_int(info, _CELL_WIDTH_KEY),
        cell_height=_parse_optional_int(info, _CELL_HEIGHT_KEY),
        background=str(info[_BACKGROUND_KEY]) if _BACKGROUND_KEY in info else None,
    )


def build_pnginfo(metadata: SheetLayoutMetadata) -> PngInfo:
    pnginfo = PngInfo()
    pnginfo.add_text(_ROWS_KEY, str(metadata.rows))
    pnginfo.add_text(_COLS_KEY, str(metadata.cols))
    if metadata.cell_width is not None:
        pnginfo.add_text(_CELL_WIDTH_KEY, str(metadata.cell_width))
    if metadata.cell_height is not None:
        pnginfo.add_text(_CELL_HEIGHT_KEY, str(metadata.cell_height))
    if metadata.background is not None:
        pnginfo.add_text(_BACKGROUND_KEY, metadata.background)
    return pnginfo


def save_png_with_layout_metadata(
    image: Image.Image | object,
    path: Path,
    metadata: SheetLayoutMetadata | None,
) -> None:
    pil_image = _coerce_to_pil_image(image)
    if metadata is None:
        pil_image.save(path)
        return
    pil_image.save(path, pnginfo=build_pnginfo(metadata))


def _coerce_to_pil_image(image: Image.Image | object) -> Image.Image:
    if isinstance(image, Image.Image):
        return image

    buffer = BytesIO()
    save = getattr(image, "save", None)
    if save is None:
        raise TypeError(f"Unsupported image object: {type(image)!r}")

    try:
        save(buffer, format="PNG")
    except TypeError:
        try:
            save(buffer)
        except TypeError:
            with NamedTemporaryFile(suffix=".png", delete=False) as handle:
                temp_path = Path(handle.name)
            try:
                try:
                    save(temp_path, format="PNG")
                except TypeError:
                    save(str(temp_path))
                with Image.open(temp_path) as coerced:
                    return coerced.copy()
            finally:
                temp_path.unlink(missing_ok=True)
    buffer.seek(0)
    with Image.open(buffer) as coerced:
        return coerced.copy()
