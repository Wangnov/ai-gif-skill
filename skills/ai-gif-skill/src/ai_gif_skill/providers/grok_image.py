from __future__ import annotations

import base64
import getpass
import json
import os
from io import BytesIO
from pathlib import Path
from urllib import error, request

from PIL import Image

from .base import ProviderImageResult

DEFAULT_GROK_IMAGE_MODEL = "grok-imagine-image"
_BASE_URL = "https://api.x.ai"
_DOWNLOAD_USER_AGENT = "Mozilla/5.0"


def resolve_api_key(explicit_api_key: str | None = None) -> str:
    if explicit_api_key:
        return explicit_api_key
    env_value = os.environ.get("XAI_API_KEY")
    if env_value:
        return env_value
    entered = getpass.getpass("XAI_API_KEY: ").strip()
    if not entered:
        raise ValueError("XAI_API_KEY is required.")
    return entered


def _image_to_data_url(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".") or "png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/{suffix};base64,{encoded}"


def _post_json(endpoint: str, payload: dict[str, object], api_key: str) -> dict[str, object]:
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    req = request.Request(f"{_BASE_URL}{endpoint}", data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:  # pragma: no cover - network error path
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"xAI image request failed: HTTP {exc.code}: {detail}") from exc


def _extract_image_url(payload: dict[str, object]) -> str:
    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and isinstance(item.get("url"), str):
                return item["url"]
    if isinstance(payload.get("url"), str):
        return payload["url"]  # type: ignore[return-value]
    raise RuntimeError("xAI image response did not contain an image URL.")


def _extract_image_b64_json(payload: dict[str, object]) -> str | None:
    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and isinstance(item.get("b64_json"), str):
                return item["b64_json"]
    if isinstance(payload.get("b64_json"), str):
        return payload["b64_json"]  # type: ignore[return-value]
    return None


def _decode_image(b64_json: str) -> Image.Image:
    image_bytes = base64.b64decode(b64_json)
    with Image.open(BytesIO(image_bytes)) as image:
        return image.copy()


def _download_bytes(url: str) -> bytes:
    req = request.Request(url, headers={"User-Agent": _DOWNLOAD_USER_AGENT})
    with request.urlopen(req) as response:
        return response.read()


def _download_image(image_url: str) -> Image.Image:
    body = _download_bytes(image_url)
    with Image.open(BytesIO(body)) as image:
        return image.copy()


def generate_image(
    *,
    prompt: str,
    input_image_path: Path | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> ProviderImageResult:
    resolved_model = model or DEFAULT_GROK_IMAGE_MODEL
    resolved_api_key = resolve_api_key(api_key)

    if input_image_path is None:
        payload = {
            "model": resolved_model,
            "prompt": prompt,
            "response_format": "b64_json",
        }
        response = _post_json("/v1/images/generations", payload, resolved_api_key)
    else:
        payload = {
            "model": resolved_model,
            "prompt": prompt,
            "response_format": "b64_json",
            "images": [
                {
                    "url": _image_to_data_url(input_image_path),
                    "type": "image_url",
                }
            ],
        }
        response = _post_json("/v1/images/edits", payload, resolved_api_key)

    image_b64_json = _extract_image_b64_json(response)
    if image_b64_json is not None:
        image = _decode_image(image_b64_json)
        source_url = None
        source_kind = "b64_json"
    else:
        source_url = _extract_image_url(response)
        image = _download_image(source_url)
        source_kind = "url"

    return ProviderImageResult(
        image=image,
        payload={
            "model": resolved_model,
            "source_kind": source_kind,
            "source_url": source_url,
        },
    )


def generate_sheet(
    *,
    input_image_path: Path,
    prompt: str,
    model: str | None = None,
    api_key: str | None = None,
) -> ProviderImageResult:
    return generate_image(
        prompt=prompt,
        input_image_path=input_image_path,
        model=model,
        api_key=api_key,
    )
