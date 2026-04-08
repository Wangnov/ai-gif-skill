from pathlib import Path

import pytest

from ai_gif_skill.providers.base import ProviderVideoResult
from ai_gif_skill.video import VideoGenerationRequest, generate_video


def test_generate_video_dispatches_to_grok_provider_and_writes_mp4(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "generated.mp4"
    reference_image_path = tmp_path / "ref.png"
    reference_image_path.write_bytes(b"fake-image")
    captured: dict[str, object] = {}

    def _fake_generate_video(
        *,
        prompt: str,
        reference_image_path: Path | None,
        model: str | None,
        api_key: str | None,
        duration_seconds: int,
        aspect_ratio: str | None,
        resolution: str | None,
    ) -> ProviderVideoResult:
        captured["prompt"] = prompt
        captured["reference_image_path"] = reference_image_path
        captured["model"] = model
        captured["api_key"] = api_key
        captured["duration_seconds"] = duration_seconds
        captured["aspect_ratio"] = aspect_ratio
        captured["resolution"] = resolution
        return ProviderVideoResult(
            video_bytes=b"fake-video",
            payload={"model": model or "grok-imagine-video"},
        )

    monkeypatch.setattr("ai_gif_skill.providers.grok_video.generate_video", _fake_generate_video)

    payload = generate_video(
        request=VideoGenerationRequest(
            prompt="animate the crab",
            duration_seconds=2,
            output_path=output_path,
            reference_image_path=reference_image_path,
            aspect_ratio="1:1",
            resolution="480p",
        ),
        provider="grok",
        model="grok-imagine-video",
        api_key="test-key",
    )

    assert captured["reference_image_path"] == reference_image_path
    assert captured["duration_seconds"] == 2
    assert output_path.read_bytes() == b"fake-video"
    assert payload["provider"] == "grok"
    assert payload["output_path"] == str(output_path)


def test_generate_video_dispatches_to_gemini_provider_without_reference_image(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "generated.mp4"
    captured: dict[str, object] = {}

    def _fake_generate_video(
        *,
        prompt: str,
        reference_image_path: Path | None,
        model: str | None,
        api_key: str | None,
        duration_seconds: int,
        aspect_ratio: str | None,
        resolution: str | None,
    ) -> ProviderVideoResult:
        captured["reference_image_path"] = reference_image_path
        return ProviderVideoResult(
            video_bytes=b"gemini-video",
            payload={"model": model or "veo-3.1-generate-preview"},
        )

    monkeypatch.setattr("ai_gif_skill.providers.gemini_video.generate_video", _fake_generate_video)

    payload = generate_video(
        request=VideoGenerationRequest(
            prompt="animate the crab",
            duration_seconds=2,
            output_path=output_path,
        ),
        provider="gemini",
        model="veo-3.1-generate-preview",
        api_key="test-key",
    )

    assert captured["reference_image_path"] is None
    assert output_path.read_bytes() == b"gemini-video"
    assert payload["provider"] == "gemini"
