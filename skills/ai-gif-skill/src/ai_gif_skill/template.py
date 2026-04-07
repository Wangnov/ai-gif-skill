from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

DEFAULT_ROWS = 2
DEFAULT_COLS = 8
DEFAULT_CELL_WIDTH = 768
DEFAULT_CELL_HEIGHT = 768
DEFAULT_KEY_COLOR = "#00FF00"


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
) -> dict[str, object]:
    svg_text = render_template_svg(spec=spec, background=background)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(svg_text, encoding="utf-8")
    if png_path is not None:
        png_path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGB", (spec.sheet_width, spec.sheet_height), normalize_hex_color(background))
        image.save(png_path)
    return {
        "sheet_width": spec.sheet_width,
        "sheet_height": spec.sheet_height,
        "background": normalize_hex_color(background),
        "rows": spec.rows,
        "cols": spec.cols,
        "cell_width": spec.cell_width,
        "cell_height": spec.cell_height,
        "gutter": spec.gutter,
        "margin": spec.margin,
        "svg_path": str(svg_path),
        "png_path": str(png_path) if png_path is not None else None,
    }
