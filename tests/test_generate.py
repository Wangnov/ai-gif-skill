import sys
import types
from pathlib import Path
import os

import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from ai_gif_skill.generate import (
    GenerationRequest,
    generate_image,
    generate_sheet,
    generate_sheet_with_gemini,
)
from ai_gif_skill.providers.base import ProviderImageResult, normalize_provider_name


def _write_template_png(
    path: Path,
    *,
    rows: int,
    cols: int,
    cell_width: int = 32,
    cell_height: int = 32,
    background: str = "#00FF00",
) -> None:
    pnginfo = PngInfo()
    pnginfo.add_text("ai_gif_skill_rows", str(rows))
    pnginfo.add_text("ai_gif_skill_cols", str(cols))
    pnginfo.add_text("ai_gif_skill_cell_width", str(cell_width))
    pnginfo.add_text("ai_gif_skill_cell_height", str(cell_height))
    pnginfo.add_text("ai_gif_skill_background", background)
    Image.new("RGB", (cols * cell_width, rows * cell_height), background).save(path, pnginfo=pnginfo)


def test_generate_sheet_with_gemini_rejects_template_layout_mismatch(tmp_path: Path) -> None:
    input_path = tmp_path / "template.png"
    output_path = tmp_path / "generated.png"
    _write_template_png(input_path, rows=2, cols=4)

    request = GenerationRequest(
        prompt="test",
        background="#00FF00",
        rows=3,
        cols=3,
        cell_width=32,
        cell_height=32,
    )

    with pytest.raises(ValueError, match="Template layout metadata"):
        generate_sheet_with_gemini(
            input_image_path=input_path,
            output_image_path=output_path,
            request=request,
            api_key="test-key",
        )


def test_generate_sheet_with_gemini_carries_layout_metadata_to_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "template.png"
    output_path = tmp_path / "generated.png"
    _write_template_png(input_path, rows=2, cols=4)

    result_image = Image.new("RGB", (80, 40), "#00FF00")

    class _FakePart:
        def as_image(self) -> Image.Image:
            return result_image

    class _FakeModels:
        def generate_content(self, *, model: str, contents: list[object]) -> object:
            assert model == "gemini-2.5-flash-image"
            assert contents
            return types.SimpleNamespace(parts=[_FakePart()])

    class _FakeClient:
        def __init__(self, api_key: str) -> None:
            assert api_key == "test-key"
            self.models = _FakeModels()

    fake_google = types.ModuleType("google")
    fake_google.genai = types.SimpleNamespace(Client=_FakeClient)
    monkeypatch.setitem(sys.modules, "google", fake_google)

    request = GenerationRequest(
        prompt="test",
        background="#00FF00",
        rows=2,
        cols=4,
        cell_width=32,
        cell_height=32,
    )

    generate_sheet_with_gemini(
        input_image_path=input_path,
        output_image_path=output_path,
        request=request,
        api_key="test-key",
    )

    with Image.open(output_path) as image:
        assert image.info["ai_gif_skill_rows"] == "2"
        assert image.info["ai_gif_skill_cols"] == "4"


def test_generate_sheet_with_gemini_handles_image_like_parts_without_pnginfo_support(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "template.png"
    output_path = tmp_path / "generated.png"
    _write_template_png(input_path, rows=2, cols=4)

    pil_image = Image.new("RGB", (80, 40), "#00FF00")

    class _ImageLike:
        def save(self, fp: object, format: str | None = None) -> None:
            pil_image.save(fp, format=format or "PNG")

    class _FakePart:
        def as_image(self) -> _ImageLike:
            return _ImageLike()

    class _FakeModels:
        def generate_content(self, *, model: str, contents: list[object]) -> object:
            assert model == "gemini-2.5-flash-image"
            assert contents
            return types.SimpleNamespace(parts=[_FakePart()])

    class _FakeClient:
        def __init__(self, api_key: str) -> None:
            assert api_key == "test-key"
            self.models = _FakeModels()

    fake_google = types.ModuleType("google")
    fake_google.genai = types.SimpleNamespace(Client=_FakeClient)
    monkeypatch.setitem(sys.modules, "google", fake_google)

    request = GenerationRequest(
        prompt="test",
        background="#00FF00",
        rows=2,
        cols=4,
        cell_width=32,
        cell_height=32,
    )

    generate_sheet_with_gemini(
        input_image_path=input_path,
        output_image_path=output_path,
        request=request,
        api_key="test-key",
    )

    with Image.open(output_path) as image:
        assert image.info["ai_gif_skill_rows"] == "2"
        assert image.info["ai_gif_skill_cols"] == "4"


def test_generate_sheet_with_gemini_handles_image_like_parts_that_only_save_to_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "template.png"
    output_path = tmp_path / "generated.png"
    _write_template_png(input_path, rows=2, cols=4)

    pil_image = Image.new("RGB", (80, 40), "#00FF00")

    class _PathOnlyImageLike:
        def save(self, fp: object, format: str | None = None) -> None:
            if not isinstance(fp, (str, os.PathLike)):
                raise TypeError(
                    "argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'BytesIO'"
                )
            pil_image.save(fp, format=format or "PNG")

    class _FakePart:
        def as_image(self) -> _PathOnlyImageLike:
            return _PathOnlyImageLike()

    class _FakeModels:
        def generate_content(self, *, model: str, contents: list[object]) -> object:
            assert model == "gemini-2.5-flash-image"
            assert contents
            return types.SimpleNamespace(parts=[_FakePart()])

    class _FakeClient:
        def __init__(self, api_key: str) -> None:
            assert api_key == "test-key"
            self.models = _FakeModels()

    fake_google = types.ModuleType("google")
    fake_google.genai = types.SimpleNamespace(Client=_FakeClient)
    monkeypatch.setitem(sys.modules, "google", fake_google)

    request = GenerationRequest(
        prompt="test",
        background="#00FF00",
        rows=2,
        cols=4,
        cell_width=32,
        cell_height=32,
    )

    generate_sheet_with_gemini(
        input_image_path=input_path,
        output_image_path=output_path,
        request=request,
        api_key="test-key",
    )

    with Image.open(output_path) as image:
        assert image.info["ai_gif_skill_rows"] == "2"
        assert image.info["ai_gif_skill_cols"] == "4"


def test_normalize_provider_name_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unknown provider"):
        normalize_provider_name("unknown")


def test_normalize_provider_name_normalizes_case() -> None:
    assert normalize_provider_name("GeMiNi") == "gemini"


def test_generate_sheet_dispatches_to_grok_provider_and_preserves_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "template.png"
    output_path = tmp_path / "generated.png"
    _write_template_png(input_path, rows=2, cols=4)

    captured: dict[str, object] = {}

    def _fake_generate_sheet(*, input_image_path: Path, prompt: str, model: str | None, api_key: str | None) -> ProviderImageResult:
        captured["input_image_path"] = input_image_path
        captured["prompt"] = prompt
        captured["model"] = model
        captured["api_key"] = api_key
        return ProviderImageResult(
            image=Image.new("RGB", (80, 40), "#00FF00"),
            payload={"model": model or "grok-imagine-image"},
        )

    monkeypatch.setattr("ai_gif_skill.providers.grok_image.generate_sheet", _fake_generate_sheet)

    request = GenerationRequest(
        prompt="test",
        background="#00FF00",
        rows=2,
        cols=4,
        cell_width=32,
        cell_height=32,
    )

    payload = generate_sheet(
        input_image_path=input_path,
        output_image_path=output_path,
        request=request,
        provider="grok",
        model="grok-imagine-image",
        api_key="test-key",
    )

    assert captured["input_image_path"] == input_path
    assert "EXACTLY 8 frames" in str(captured["prompt"])
    assert payload["provider"] == "grok"

    with Image.open(output_path) as image:
        assert image.info["ai_gif_skill_rows"] == "2"
        assert image.info["ai_gif_skill_cols"] == "4"


def test_generate_image_dispatches_to_grok_provider_without_sheet_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "generated.png"
    captured: dict[str, object] = {}

    def _fake_generate_image(*, prompt: str, input_image_path: Path | None, model: str | None, api_key: str | None) -> ProviderImageResult:
        captured["prompt"] = prompt
        captured["input_image_path"] = input_image_path
        captured["model"] = model
        captured["api_key"] = api_key
        return ProviderImageResult(
            image=Image.new("RGB", (64, 64), "#123456"),
            payload={"model": model or "grok-imagine-image"},
        )

    monkeypatch.setattr("ai_gif_skill.providers.grok_image.generate_image", _fake_generate_image)

    payload = generate_image(
        output_image_path=output_path,
        prompt="make a crab",
        provider="grok",
        model="grok-imagine-image",
        api_key="test-key",
    )

    assert captured["prompt"] == "make a crab"
    assert payload["provider"] == "grok"

    with Image.open(output_path) as image:
        assert "ai_gif_skill_rows" not in image.info
        assert "ai_gif_skill_cols" not in image.info
