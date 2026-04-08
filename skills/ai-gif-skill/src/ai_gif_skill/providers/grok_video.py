from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from urllib import error, request

from .base import ProviderVideoResult
from .grok_image import resolve_api_key

DEFAULT_GROK_VIDEO_MODEL = "grok-imagine-video"
_BASE_URL = "https://api.x.ai"
_POLL_INTERVAL_SECONDS = 5


def _image_to_data_url(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".") or "png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/{suffix};base64,{encoded}"


def _request_json(method: str, endpoint: str, api_key: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    req = request.Request(f"{_BASE_URL}{endpoint}", data=body, headers=headers, method=method)
    try:
        with request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:  # pragma: no cover - network error path
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"xAI video request failed: HTTP {exc.code}: {detail}") from exc


def _extract_request_id(payload: dict[str, object]) -> str:
    request_id = payload.get("request_id") or payload.get("id")
    if not isinstance(request_id, str):
        raise RuntimeError("xAI video response did not include a request id.")
    return request_id


def _extract_video_url(payload: dict[str, object]) -> str:
    video = payload.get("video")
    if isinstance(video, dict) and isinstance(video.get("url"), str):
        return video["url"]
    if isinstance(payload.get("url"), str):
        return payload["url"]  # type: ignore[return-value]
    raise RuntimeError("xAI video status response did not contain a video URL.")


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
    resolved_model = model or DEFAULT_GROK_VIDEO_MODEL
    resolved_api_key = resolve_api_key(api_key)
    payload: dict[str, object] = {
        "model": resolved_model,
        "prompt": prompt,
        "duration": duration_seconds,
    }
    if aspect_ratio:
        payload["aspect_ratio"] = aspect_ratio
    if resolution:
        payload["resolution"] = resolution
    if reference_image_path is not None:
        payload["image"] = {"url": _image_to_data_url(reference_image_path)}

    submit_payload = _request_json("POST", "/v1/videos/generations", resolved_api_key, payload)
    request_id = _extract_request_id(submit_payload)

    while True:
        status_payload = _request_json("GET", f"/v1/videos/{request_id}", resolved_api_key)
        status = str(status_payload.get("status", "")).lower()
        if status in {"done", "completed", "success", "succeeded"}:
            break
        if status in {"failed", "error", "canceled", "cancelled"}:
            raise RuntimeError(f"xAI video generation failed: {status_payload}")
        time.sleep(_POLL_INTERVAL_SECONDS)

    video_url = _extract_video_url(status_payload)
    with request.urlopen(video_url) as response:
        video_bytes = response.read()

    return ProviderVideoResult(
        video_bytes=video_bytes,
        payload={
            "model": resolved_model,
            "request_id": request_id,
            "source_url": video_url,
        },
    )
