from __future__ import annotations

import getpass
import os
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    background: str
    rows: int
    cols: int
    cell_width: int
    cell_height: int


def build_generation_prompt(request: GenerationRequest) -> str:
    return (
        "You are generating a full sprite sheet image.\n"
        f"The sheet layout is {request.rows} rows and {request.cols} columns.\n"
        f"Each frame should read as approximately {request.cell_width}x{request.cell_height} pixels.\n"
        f"The background color must stay exactly {request.background}.\n"
        "Do not change the background color.\n"
        "Do not add gradients, shadows, floor planes, props, or extra background elements.\n"
        "Keep one consistent character identity and one coherent animation progression across the whole sheet.\n"
        "Respect the visible frame layout from the input template image.\n"
        f"Asset request: {request.prompt}\n"
    )


def resolve_api_key(explicit_api_key: str | None = None) -> str:
    if explicit_api_key:
        return explicit_api_key
    env_value = os.environ.get("GEMINI_API_KEY")
    if env_value:
        return env_value
    entered = getpass.getpass("GEMINI_API_KEY: ").strip()
    if not entered:
        raise ValueError("GEMINI_API_KEY is required.")
    return entered


def generate_sheet_with_gemini(
    *,
    input_image_path: Path,
    output_image_path: Path,
    request: GenerationRequest,
    model: str = "gemini-2.5-flash-image",
    api_key: str | None = None,
) -> dict[str, object]:
    from google import genai

    client = genai.Client(api_key=resolve_api_key(api_key))
    prompt = build_generation_prompt(request)
    template_image = Image.open(input_image_path)
    response = client.models.generate_content(
        model=model,
        contents=[prompt, template_image],
    )
    parts = getattr(response, "parts", None)
    if parts is None and getattr(response, "candidates", None):
        parts = response.candidates[0].content.parts

    saved = False
    for part in parts or []:
        if hasattr(part, "as_image"):
            image = part.as_image()
            if image is not None:
                output_image_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(output_image_path)
                saved = True
                break
    if not saved:
        raise RuntimeError("Gemini response did not contain an image part.")
    return {
        "model": model,
        "input_image_path": str(input_image_path),
        "output_image_path": str(output_image_path),
        "rows": request.rows,
        "cols": request.cols,
        "background": request.background,
    }
