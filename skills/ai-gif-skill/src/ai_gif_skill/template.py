from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from .layout_metadata import SheetLayoutMetadata, save_png_with_layout_metadata

DEFAULT_ROWS = 2
DEFAULT_COLS = 8
DEFAULT_CELL_WIDTH = 768
DEFAULT_CELL_HEIGHT = 768
DEFAULT_KEY_COLOR = "#00FF00"
DEFAULT_GUIDE_GRID = True
_GUIDE_SHADE_FACTOR = 0.84


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = normalize_hex_color(color)
    return (
        int(value[1:3], 16),
        int(value[3:5], 16),
        int(value[5:7], 16),
    )


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


@dataclass(frozen=True)
class GridSpec:
    rows: int = DEFAULT_ROWS
    cols: int = DEFAULT_COLS
    cell_width: int = DEFAULT_CELL_WIDTH
    cell_height: int = DEFAULT_CELL_HEIGHT
    gutter: int = 0
    margin: int = 0

    @property
    def sheet_width(self) -> int:
        return self.cols * self.cell_width + (self.cols - 1) * self.gutter + self.margin * 2

    @property
    def sheet_height(self) -> int:
        return self.rows * self.cell_height + (self.rows - 1) * self.gutter + self.margin * 2


def normalize_hex_color(color: str) -> str:
    value = color.strip().upper()
    if not value.startswith("#"):
        value = f"#{value}"
    if len(value) != 7:
        raise ValueError(f"Expected #RRGGBB color, got {color!r}")
    return value


def derive_guide_color(background: str) -> str:
    red, green, blue = _hex_to_rgb(background)
    return _rgb_to_hex(
        (
            int(round(red * _GUIDE_SHADE_FACTOR)),
            int(round(green * _GUIDE_SHADE_FACTOR)),
            int(round(blue * _GUIDE_SHADE_FACTOR)),
        )
    )


def default_guide_thickness(spec: GridSpec) -> int:
    return max(2, int(round(min(spec.cell_width, spec.cell_height) * 0.015)))


def draw_guide_grid(
    image: Image.Image,
    *,
    spec: GridSpec,
    guide_color: str,
    guide_thickness: int,
) -> None:
    draw = ImageDraw.Draw(image)
    half_low = guide_thickness // 2
    half_high = guide_thickness - half_low

    for col in range(1, spec.cols):
        x = spec.margin + col * spec.cell_width + (col - 1) * spec.gutter
        draw.rectangle(
            [x - half_low, 0, x + half_high - 1, spec.sheet_height - 1],
            fill=guide_color,
        )
    for row in range(1, spec.rows):
        y = spec.margin + row * spec.cell_height + (row - 1) * spec.gutter
        draw.rectangle(
            [0, y - half_low, spec.sheet_width - 1, y + half_high - 1],
            fill=guide_color,
        )


def render_template_svg(spec: GridSpec, background: str = DEFAULT_KEY_COLOR) -> str:
    color = normalize_hex_color(background)
    cells: list[str] = []
    for row in range(spec.rows):
        for col in range(spec.cols):
            x = spec.margin + col * (spec.cell_width + spec.gutter)
            y = spec.margin + row * (spec.cell_height + spec.gutter)
            cells.append(
                f'    <!-- cell row={row} col={col} -->\n'
                f'    <rect x="{x}" y="{y}" width="{spec.cell_width}" height="{spec.cell_height}" '
                'fill="none" stroke="none" />'
            )
    cells_text = "\n".join(cells)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{spec.sheet_width}" '
        f'height="{spec.sheet_height}" viewBox="0 0 {spec.sheet_width} {spec.sheet_height}">\n'
        f'  <rect width="{spec.sheet_width}" height="{spec.sheet_height}" fill="{color}" />\n'
        '  <g id="grid" fill="none" stroke="none">\n'
        f"{cells_text}\n"
        "  </g>\n"
        "</svg>\n"
    )


def write_template_assets(
    *,
    spec: GridSpec,
    background: str,
    svg_path: Path,
    png_path: Path | None = None,
    guide_grid: bool = DEFAULT_GUIDE_GRID,
) -> dict[str, object]:
    normalized_background = normalize_hex_color(background)
    svg_text = render_template_svg(spec=spec, background=normalized_background)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(svg_text, encoding="utf-8")
    guide_color = derive_guide_color(normalized_background) if guide_grid else None
    guide_thickness = default_guide_thickness(spec) if guide_grid else None
    if png_path is not None:
        png_path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGB", (spec.sheet_width, spec.sheet_height), normalized_background)
        if guide_grid and guide_color is not None and guide_thickness is not None:
            draw_guide_grid(
                image,
                spec=spec,
                guide_color=guide_color,
                guide_thickness=guide_thickness,
            )
        save_png_with_layout_metadata(
            image,
            png_path,
            SheetLayoutMetadata(
                rows=spec.rows,
                cols=spec.cols,
                cell_width=spec.cell_width,
                cell_height=spec.cell_height,
                background=normalized_background,
            ),
        )
    return {
        "sheet_width": spec.sheet_width,
        "sheet_height": spec.sheet_height,
        "background": normalized_background,
        "rows": spec.rows,
        "cols": spec.cols,
        "cell_width": spec.cell_width,
        "cell_height": spec.cell_height,
        "gutter": spec.gutter,
        "margin": spec.margin,
        "guide_grid": guide_grid,
        "guide_color": guide_color,
        "guide_thickness": guide_thickness,
        "svg_path": str(svg_path),
        "png_path": str(png_path) if png_path is not None else None,
    }
