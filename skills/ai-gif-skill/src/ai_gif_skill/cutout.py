from __future__ import annotations

from pathlib import Path
from statistics import median
from typing import Callable

from PIL import Image

from .template import DEFAULT_KEY_COLOR, normalize_hex_color

DEFAULT_CUTOUT_MODE = "color"
DEFAULT_CUTOUT_TOLERANCE = 48
_EDGE_SOFTNESS = 24


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = normalize_hex_color(color)
    return (
        int(value[1:3], 16),
        int(value[3:5], 16),
        int(value[5:7], 16),
    )


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def estimate_background_color(image: Image.Image, border: int = 2) -> str:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    border_x = min(max(border, 1), width)
    border_y = min(max(border, 1), height)
    pixels = rgba.load()
    samples: list[tuple[int, int, int]] = []

    for y in range(height):
        for x in range(width):
            if border_x <= x < width - border_x and border_y <= y < height - border_y:
                continue
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue
            samples.append((red, green, blue))

    if not samples:
        return DEFAULT_KEY_COLOR

    channels = list(zip(*samples, strict=True))
    return _rgb_to_hex(tuple(int(round(median(channel))) for channel in channels))


def _resolve_alpha(distance: int, *, tolerance: int, softness: int) -> float:
    if distance <= tolerance:
        return 0.0
    if distance >= tolerance + softness:
        return 1.0
    return (distance - tolerance) / softness


def _restore_channel(value: int, background: int, alpha_scale: float) -> int:
    if alpha_scale <= 0:
        return 0
    restored = (value - background * (1.0 - alpha_scale)) / alpha_scale
    return max(0, min(255, int(round(restored))))


def remove_solid_background(
    image: Image.Image,
    *,
    background_color: str | None = None,
    tolerance: int = DEFAULT_CUTOUT_TOLERANCE,
) -> Image.Image:
    if tolerance < 0:
        raise ValueError("Tolerance must be >= 0.")

    rgba = image.convert("RGBA")
    resolved_background = normalize_hex_color(background_color) if background_color else estimate_background_color(rgba)
    background_rgb = _hex_to_rgb(resolved_background)
    width, height = rgba.size
    source = rgba.load()
    result = Image.new("RGBA", rgba.size)
    target = result.load()

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = source[x, y]
            if alpha == 0:
                target[x, y] = (0, 0, 0, 0)
                continue

            distance = max(
                abs(red - background_rgb[0]),
                abs(green - background_rgb[1]),
                abs(blue - background_rgb[2]),
            )
            alpha_scale = _resolve_alpha(distance, tolerance=tolerance, softness=_EDGE_SOFTNESS)
            new_alpha = max(0, min(255, int(round(alpha * alpha_scale))))

            if new_alpha == 0:
                target[x, y] = (0, 0, 0, 0)
                continue
            if new_alpha == alpha:
                target[x, y] = (red, green, blue, alpha)
                continue

            target[x, y] = (
                _restore_channel(red, background_rgb[0], alpha_scale),
                _restore_channel(green, background_rgb[1], alpha_scale),
                _restore_channel(blue, background_rgb[2], alpha_scale),
                new_alpha,
            )

    return result


def run_cutout(
    *,
    input_path: Path,
    output_path: Path,
    mode: str = DEFAULT_CUTOUT_MODE,
    model: str = "isnet-anime",
    background_color: str | None = None,
    tolerance: int = DEFAULT_CUTOUT_TOLERANCE,
    remove_background: Callable[..., bytes] | None = None,
) -> dict[str, object]:
    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"color", "rembg"}:
        raise ValueError(f"Unsupported cutout mode: {mode!r}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if normalized_mode == "color":
        with Image.open(input_path) as image:
            resolved_background = normalize_hex_color(background_color) if background_color else estimate_background_color(image)
            result = remove_solid_background(
                image,
                background_color=resolved_background,
                tolerance=tolerance,
            )
            result.save(output_path)
            width, height = result.size
            image_mode = result.mode
    else:
        source_bytes = input_path.read_bytes()
        if remove_background is None:
            from rembg import new_session, remove

            session = new_session(model)
            result_bytes = remove(source_bytes, session=session)
        else:
            result_bytes = remove_background(source_bytes, model=model)
        output_path.write_bytes(result_bytes)
        with Image.open(output_path) as image:
            width, height = image.size
            image_mode = image.mode
        resolved_background = None

    return {
        "input_path": str(input_path),
        "output_path": str(output_path),
        "mode": normalized_mode,
        "model": model if normalized_mode == "rembg" else None,
        "background_color": resolved_background,
        "tolerance": tolerance if normalized_mode == "color" else None,
        "width": width,
        "height": height,
        "image_mode": image_mode,
    }
