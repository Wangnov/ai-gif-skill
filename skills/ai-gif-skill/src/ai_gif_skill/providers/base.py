from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

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
    output_image_path: Path
    background: str | None = None


@dataclass(frozen=True)
class SheetGenerationRequest:
    prompt: str
    input_image_path: Path
    output_image_path: Path
    background: str
    rows: int
    cols: int
    cell_width: int
    cell_height: int


class ProviderProtocol(Protocol):
    def provider_name(self) -> ProviderName: ...
