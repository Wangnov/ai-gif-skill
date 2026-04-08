from __future__ import annotations

from importlib import import_module
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .layout_metadata import SheetLayoutMetadata, read_sheet_layout_metadata, save_png_with_layout_metadata
from .providers.base import DEFAULT_PROVIDER_NAME, normalize_provider_name
from .template import normalize_hex_color


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    background: str
    rows: int
    cols: int
    cell_width: int
    cell_height: int


def resolve_provider_name(provider: str | None = None) -> str:
    return normalize_provider_name(provider or DEFAULT_PROVIDER_NAME)


def build_generation_prompt(request: GenerationRequest) -> str:
    frame_count = request.rows * request.cols
    return (
        "You are generating a full sprite sheet image.\n"
        f"The sheet layout is {request.rows} rows and {request.cols} columns.\n"
        f"The sheet must contain EXACTLY {frame_count} frames, arranged as {request.rows} rows by {request.cols} columns.\n"
        f"Each frame should read as approximately {request.cell_width}x{request.cell_height} pixels.\n"
        f"The background color must stay exactly {request.background}.\n"
        "Do not change the background color.\n"
        "Do not output a different panel count or grid layout than the template.\n"
        "Do not add gradients, shadows, floor planes, props, or extra background elements.\n"
        "Keep one consistent character identity and one coherent animation progression across the whole sheet.\n"
        "Keep the character centered in each cell with the same camera angle, framing, and scale.\n"
        "The animation must come from pose changes between frames, not from moving the whole character across the sheet.\n"
        "Use readable frame-to-frame motion beats such as breathing, blinking, tail motion, limb motion, anticipation, action, follow-through, and recovery when they fit the requested action.\n"
        "Do not limit the animation to blinking, eye changes, or tiny facial changes alone.\n"
        "Make sure multiple frames show visible silhouette or body-part changes in the torso, head tilt, ears, tail, arms, legs, or clothing shapes when those parts exist.\n"
        "Keep the same facing direction and view orientation across frames.\n"
        "Do not turn the character into a different camera view or profile unless the asset request explicitly asks for that.\n"
        "Do not animate by sliding the whole character sideways.\n"
        "No horizontal drift. No vertical drift.\n"
        "Avoid duplicate frames or near-identical frames when the requested action should visibly loop.\n"
        "Place one frame inside each visible guided cell from the input template image.\n"
        "Respect the visible frame layout from the input template image.\n"
        f"Asset request: {request.prompt}\n"
    )


def validate_template_layout_metadata(
    image: Image.Image,
    request: GenerationRequest,
) -> SheetLayoutMetadata | None:
    metadata = read_sheet_layout_metadata(image)
    if metadata is None:
        return None

    mismatches: list[str] = []
    if metadata.rows != request.rows:
        mismatches.append(f"rows metadata={metadata.rows} request={request.rows}")
    if metadata.cols != request.cols:
        mismatches.append(f"cols metadata={metadata.cols} request={request.cols}")
    if metadata.cell_width is not None and metadata.cell_width != request.cell_width:
        mismatches.append(
            f"cell_width metadata={metadata.cell_width} request={request.cell_width}"
        )
    if metadata.cell_height is not None and metadata.cell_height != request.cell_height:
        mismatches.append(
            f"cell_height metadata={metadata.cell_height} request={request.cell_height}"
        )
    if metadata.background is not None and normalize_hex_color(metadata.background) != normalize_hex_color(request.background):
        mismatches.append(
            f"background metadata={normalize_hex_color(metadata.background)} request={normalize_hex_color(request.background)}"
        )
    if mismatches:
        raise ValueError("Template layout metadata mismatch: " + ", ".join(mismatches))
    return metadata


def _load_provider_module(provider: str):
    normalized_provider = resolve_provider_name(provider)
    return import_module(f".providers.{normalized_provider}_image", package=__package__)


def generate_sheet(
    *,
    input_image_path: Path,
    output_image_path: Path,
    request: GenerationRequest,
    provider: str = DEFAULT_PROVIDER_NAME,
    model: str | None = None,
    api_key: str | None = None,
) -> dict[str, object]:
    with Image.open(input_image_path) as template_image:
        validate_template_layout_metadata(template_image, request)

    provider_module = _load_provider_module(provider)
    result = provider_module.generate_sheet(
        input_image_path=input_image_path,
        prompt=build_generation_prompt(request),
        model=model,
        api_key=api_key,
    )

    output_image_path.parent.mkdir(parents=True, exist_ok=True)
    save_png_with_layout_metadata(
        result.image,
        output_image_path,
        SheetLayoutMetadata(
            rows=request.rows,
            cols=request.cols,
            background=normalize_hex_color(request.background),
        ),
    )
    return {
        **result.payload,
        "provider": resolve_provider_name(provider),
        "input_image_path": str(input_image_path),
        "output_image_path": str(output_image_path),
        "rows": request.rows,
        "cols": request.cols,
        "background": request.background,
    }


def generate_image(
    *,
    output_image_path: Path,
    prompt: str,
    provider: str = DEFAULT_PROVIDER_NAME,
    model: str | None = None,
    api_key: str | None = None,
    input_image_path: Path | None = None,
) -> dict[str, object]:
    provider_module = _load_provider_module(provider)
    result = provider_module.generate_image(
        prompt=prompt,
        input_image_path=input_image_path,
        model=model,
        api_key=api_key,
    )
    output_image_path.parent.mkdir(parents=True, exist_ok=True)
    save_png_with_layout_metadata(result.image, output_image_path, metadata=None)
    return {
        **result.payload,
        "provider": resolve_provider_name(provider),
        "input_image_path": str(input_image_path) if input_image_path is not None else None,
        "output_image_path": str(output_image_path),
    }


def generate_sheet_with_gemini(
    *,
    input_image_path: Path,
    output_image_path: Path,
    request: GenerationRequest,
    model: str = "gemini-2.5-flash-image",
    api_key: str | None = None,
) -> dict[str, object]:
    return generate_sheet(
        input_image_path=input_image_path,
        output_image_path=output_image_path,
        request=request,
        provider="gemini",
        model=model,
        api_key=api_key,
    )
