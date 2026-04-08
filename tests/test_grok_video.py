from pathlib import Path
from urllib import request as urllib_request

import pytest

from ai_gif_skill.providers import grok_video


def test_generate_video_downloads_result_with_browser_user_agent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "generated.mp4"
    captured: dict[str, object] = {}

    responses = iter(
        [
            {"request_id": "req-123"},
            {"status": "completed", "video": {"url": "https://video.x.ai/example.mp4"}},
        ]
    )

    def _fake_request_json(
        method: str,
        endpoint: str,
        api_key: str,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        captured.setdefault("calls", []).append(
            {
                "method": method,
                "endpoint": endpoint,
                "api_key": api_key,
                "payload": payload,
            }
        )
        return next(responses)

    class _FakeResponse:
        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b"fake-video"

    def _fake_urlopen(req: object) -> _FakeResponse:
        assert isinstance(req, urllib_request.Request)
        captured["download_url"] = req.full_url
        captured["user_agent"] = req.get_header("User-agent")
        return _FakeResponse()

    monkeypatch.setattr(grok_video, "_request_json", _fake_request_json)
    monkeypatch.setattr(grok_video.request, "urlopen", _fake_urlopen)
    monkeypatch.setattr(grok_video.time, "sleep", lambda _: None)

    result = grok_video.generate_video(
        prompt="animate the fox spirit",
        reference_image_path=None,
        model="grok-imagine-video",
        api_key="test-key",
        duration_seconds=2,
        aspect_ratio="1:1",
        resolution=None,
    )

    assert captured["download_url"] == "https://video.x.ai/example.mp4"
    assert captured["user_agent"] == "Mozilla/5.0"
    assert result.video_bytes == b"fake-video"
