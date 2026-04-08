import base64
from io import BytesIO
from urllib import request as urllib_request

import pytest
from PIL import Image

from ai_gif_skill.providers import grok_image


def _make_png_bytes(color: str = "#00FF00") -> bytes:
    buffer = BytesIO()
    Image.new("RGBA", (4, 4), color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_generate_image_prefers_b64_json_response_over_url_download(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    encoded_image = base64.b64encode(_make_png_bytes()).decode("utf-8")
    captured: dict[str, object] = {}

    def _fake_post_json(endpoint: str, payload: dict[str, object], api_key: str) -> dict[str, object]:
        captured["endpoint"] = endpoint
        captured["payload"] = payload
        captured["api_key"] = api_key
        return {
            "data": [
                {
                    "b64_json": encoded_image,
                    "mime_type": "image/png",
                }
            ]
        }

    def _unexpected_download(image_url: str) -> Image.Image:
        raise AssertionError(f"Unexpected image URL download: {image_url}")

    monkeypatch.setattr(grok_image, "_post_json", _fake_post_json)
    monkeypatch.setattr(grok_image, "_download_image", _unexpected_download)

    result = grok_image.generate_image(
        prompt="make a fox spirit",
        model="grok-imagine-image",
        api_key="test-key",
    )

    assert captured["endpoint"] == "/v1/images/generations"
    assert captured["api_key"] == "test-key"
    assert captured["payload"] == {
        "model": "grok-imagine-image",
        "prompt": "make a fox spirit",
        "response_format": "b64_json",
    }
    assert result.image.size == (4, 4)
    assert result.payload["model"] == "grok-imagine-image"


def test_generate_image_falls_back_to_url_download_with_browser_user_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    png_bytes = _make_png_bytes()

    def _fake_post_json(endpoint: str, payload: dict[str, object], api_key: str) -> dict[str, object]:
        captured["endpoint"] = endpoint
        captured["payload"] = payload
        captured["api_key"] = api_key
        return {
            "data": [
                {
                    "url": "https://imgen.x.ai/example.png",
                    "mime_type": "image/png",
                }
            ]
        }

    class _FakeResponse:
        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return png_bytes

    def _fake_urlopen(req: object) -> _FakeResponse:
        assert isinstance(req, urllib_request.Request)
        captured["download_url"] = req.full_url
        captured["user_agent"] = req.get_header("User-agent")
        return _FakeResponse()

    monkeypatch.setattr(grok_image, "_post_json", _fake_post_json)
    monkeypatch.setattr(grok_image.request, "urlopen", _fake_urlopen)

    result = grok_image.generate_image(
        prompt="make a fox spirit",
        model="grok-imagine-image",
        api_key="test-key",
    )

    assert captured["endpoint"] == "/v1/images/generations"
    assert captured["download_url"] == "https://imgen.x.ai/example.png"
    assert captured["user_agent"] == "Mozilla/5.0"
    assert result.image.size == (4, 4)
    assert result.payload["source_kind"] == "url"
