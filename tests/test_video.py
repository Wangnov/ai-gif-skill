from pathlib import Path

import pytest
from PIL import Image

from ai_gif_skill.providers.base import ProviderVideoResult
from ai_gif_skill.providers import gemini_video
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


def test_gemini_provider_packs_reference_image_with_bytes_and_mime_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference_image_path = tmp_path / "ref.png"
    Image.new("RGBA", (4, 4), "#00FF00").save(reference_image_path)
    captured: dict[str, object] = {}

    class _FakeOperation:
        done = True
        error = None
        name = "op-123"
        response = type(
            "Response",
            (),
            {"generated_videos": [type("Item", (), {"video": "file-123"})()]},
        )()
        result = response

    class _FakeModels:
        def generate_videos(self, *, model: str, prompt: str, image: object, config: dict[str, object]) -> object:
            captured["model"] = model
            captured["prompt"] = prompt
            captured["image"] = image
            captured["config"] = config
            return _FakeOperation()

    class _FakeOperations:
        def get(self, operation: object) -> object:
            return operation

    class _FakeFiles:
        def download(self, *, file: object) -> bytes:
            captured["download_file"] = file
            return b"fake-video"

    class _FakeClient:
        def __init__(self, api_key: str) -> None:
            captured["api_key"] = api_key
            self.models = _FakeModels()
            self.operations = _FakeOperations()
            self.files = _FakeFiles()

    class _FakeGenaiModule:
        Client = _FakeClient

    monkeypatch.setitem(__import__("sys").modules, "google", type("GoogleModule", (), {"genai": _FakeGenaiModule})())

    result = gemini_video.generate_video(
        prompt="animate the fox",
        reference_image_path=reference_image_path,
        model="veo-3.1-generate-preview",
        api_key="test-key",
        duration_seconds=4,
        aspect_ratio=None,
        resolution=None,
    )

    image_payload = captured["image"]
    assert isinstance(image_payload, dict)
    assert image_payload["mimeType"] == "image/png"
    assert isinstance(image_payload["imageBytes"], str)
    assert captured["config"] == {"duration_seconds": 4}
    assert result.video_bytes == b"fake-video"
