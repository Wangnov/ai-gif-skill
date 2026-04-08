from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

from .providers.base import DEFAULT_PROVIDER_NAME, normalize_provider_name


@dataclass(frozen=True)
class VideoGenerationRequest:
    prompt: str
    duration_seconds: int
    output_path: Path
    reference_image_path: Path | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None


def _load_provider_module(provider: str):
    normalized_provider = normalize_provider_name(provider)
    return import_module(f".providers.{normalized_provider}_video", package=__package__)


def generate_video(
    *,
    request: VideoGenerationRequest,
    provider: str = DEFAULT_PROVIDER_NAME,
    model: str | None = None,
    api_key: str | None = None,
) -> dict[str, object]:
    normalized_provider = normalize_provider_name(provider)
    provider_module = _load_provider_module(normalized_provider)
    result = provider_module.generate_video(
        prompt=request.prompt,
        reference_image_path=request.reference_image_path,
        model=model,
        api_key=api_key,
        duration_seconds=request.duration_seconds,
        aspect_ratio=request.aspect_ratio,
        resolution=request.resolution,
    )
    request.output_path.parent.mkdir(parents=True, exist_ok=True)
    request.output_path.write_bytes(result.video_bytes)
    return {
        **result.payload,
        "provider": normalized_provider,
        "output_path": str(request.output_path),
        "reference_image_path": str(request.reference_image_path) if request.reference_image_path else None,
        "duration_seconds": request.duration_seconds,
        "aspect_ratio": request.aspect_ratio,
        "resolution": request.resolution,
    }
