from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from PIL import Image

ProviderName = Literal["gemini", "grok"]
DEFAULT_PROVIDER_NAME: ProviderName = "gemini"
_SUPPORTED_PROVIDER_NAMES = frozenset({"gemini", "grok"})


def normalize_provider_name(name: str) -> ProviderName:
    normalized = name.strip().lower()
    if normalized not in _SUPPORTED_PROVIDER_NAMES:
        supported = ", ".join(sorted(_SUPPORTED_PROVIDER_NAMES))
        raise ValueError(f"Unknown provider: {name!r}. Supported providers: {supported}")
    return normalized  # type: ignore[return-value]


@dataclass(frozen=True)
class ImageGenerationRequest:
    prompt: str
    background: str | None = None
    input_image_path: Path | None = None


@dataclass(frozen=True)
class SheetGenerationRequest:
    prompt: str
    background: str
    rows: int
    cols: int
    cell_width: int
    cell_height: int


@dataclass(frozen=True)
class ProviderImageResult:
    image: Image.Image | object
    payload: dict[str, object]


class ProviderProtocol(Protocol):
    def provider_name(self) -> ProviderName: ...
