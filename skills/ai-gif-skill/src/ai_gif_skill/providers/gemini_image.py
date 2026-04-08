from __future__ import annotations

import getpass
import os
from pathlib import Path

from PIL import Image

from .base import ProviderImageResult

DEFAULT_GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"


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


def _extract_response_parts(response: object) -> list[object]:
    parts = getattr(response, "parts", None)
    if parts is None and getattr(response, "candidates", None):
        parts = response.candidates[0].content.parts
    return list(parts or [])


def _extract_first_image(response: object) -> Image.Image | object:
    for part in _extract_response_parts(response):
        if hasattr(part, "as_image"):
            image = part.as_image()
            if image is not None:
                return image
    raise RuntimeError("Gemini response did not contain an image part.")


def _generate(
    *,
    prompt: str,
    input_image_path: Path | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> ProviderImageResult:
    from google import genai

    resolved_model = model or DEFAULT_GEMINI_IMAGE_MODEL
    client = genai.Client(api_key=resolve_api_key(api_key))
    contents: list[object] = [prompt]
    if input_image_path is not None:
        with Image.open(input_image_path) as input_image:
            contents.append(input_image.copy())
    response = client.models.generate_content(
        model=resolved_model,
        contents=contents,
    )
    return ProviderImageResult(
        image=_extract_first_image(response),
        payload={"model": resolved_model},
    )


def generate_sheet(
    *,
    input_image_path: Path,
    prompt: str,
    model: str | None = None,
    api_key: str | None = None,
) -> ProviderImageResult:
    return _generate(
        prompt=prompt,
        input_image_path=input_image_path,
        model=model,
        api_key=api_key,
    )


def generate_image(
    *,
    prompt: str,
    input_image_path: Path | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> ProviderImageResult:
    return _generate(
        prompt=prompt,
        input_image_path=input_image_path,
        model=model,
        api_key=api_key,
    )
