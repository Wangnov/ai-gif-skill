from __future__ import annotations

import base64
import time
from pathlib import Path

from PIL import Image

from .base import ProviderVideoResult
from .gemini_image import resolve_api_key

DEFAULT_GEMINI_VIDEO_MODEL = "veo-3.1-generate-preview"
_POLL_INTERVAL_SECONDS = 5


def _build_image_payload(reference_image_path: Path) -> dict[str, str]:
    with Image.open(reference_image_path) as source_image:
        mime_type = Image.MIME.get(source_image.format or "", "image/png")
    return {
        "imageBytes": base64.b64encode(reference_image_path.read_bytes()).decode("utf-8"),
        "mimeType": mime_type,
    }


def generate_video(
    *,
    prompt: str,
    reference_image_path: Path | None,
    model: str | None = None,
    api_key: str | None = None,
    duration_seconds: int,
    aspect_ratio: str | None = None,
    resolution: str | None = None,
) -> ProviderVideoResult:
    from google import genai

    resolved_model = model or DEFAULT_GEMINI_VIDEO_MODEL
    client = genai.Client(api_key=resolve_api_key(api_key))
    image_payload = None
    if reference_image_path is not None:
        image_payload = _build_image_payload(reference_image_path)

    config: dict[str, object] = {
        "duration_seconds": duration_seconds,
    }
    if aspect_ratio:
        config["aspect_ratio"] = aspect_ratio
    if resolution:
        config["resolution"] = resolution

    operation = client.models.generate_videos(
        model=resolved_model,
        prompt=prompt,
        image=image_payload,
        config=config,
    )
    while not operation.done:
        time.sleep(_POLL_INTERVAL_SECONDS)
        operation = client.operations.get(operation)

    if operation.error is not None:
        raise RuntimeError(f"Gemini video generation failed: {operation.error}")

    response = operation.response or operation.result
    generated_videos = list(getattr(response, "generated_videos", None) or [])
    if not generated_videos:
        raise RuntimeError("Gemini video response did not contain a generated video.")

    video_bytes = client.files.download(file=generated_videos[0].video)
    return ProviderVideoResult(
        video_bytes=video_bytes,
        payload={
            "model": resolved_model,
            "operation_name": getattr(operation, "name", None),
        },
    )
