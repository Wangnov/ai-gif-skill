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


def _download_image(image_url: str) -> Image.Image:
    with request.urlopen(image_url) as response:
        body = response.read()
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
        }
        response = _post_json("/v1/images/generations", payload, resolved_api_key)
    else:
        payload = {
            "model": resolved_model,
            "prompt": prompt,
            "images": [
                {
                    "url": _image_to_data_url(input_image_path),
                    "type": "image_url",
                }
            ],
        }
        response = _post_json("/v1/images/edits", payload, resolved_api_key)

    image_url = _extract_image_url(response)
    return ProviderImageResult(
        image=_download_image(image_url),
        payload={
            "model": resolved_model,
            "source_url": image_url,
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
