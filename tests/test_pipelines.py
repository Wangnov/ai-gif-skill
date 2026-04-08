from pathlib import Path

import pytest

from ai_gif_skill.generate import GenerationRequest
from ai_gif_skill.pipelines import (
    SheetPipelineRequest,
    VideoPipelineRequest,
    run_sheet_pipeline,
    run_video_pipeline,
)


def test_run_sheet_pipeline_returns_stage_list_and_final_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stage_calls: list[str] = []

    def _fake_generate_sheet(**kwargs: object) -> dict[str, object]:
        stage_calls.append("generate-sheet")
        Path(kwargs["output_image_path"]).write_bytes(b"generated")
        return {"output_image_path": str(kwargs["output_image_path"])}

    def _fake_run_cutout(**kwargs: object) -> dict[str, object]:
        stage_calls.append("cutout")
        Path(kwargs["output_path"]).write_bytes(b"cutout")
        return {"output_path": str(kwargs["output_path"])}

    def _fake_gif(**kwargs: object) -> dict[str, object]:
        stage_calls.append("gif-from-sheet")
        Path(kwargs["output_path"]).write_bytes(b"gif")
        return {"output_path": str(kwargs["output_path"])}

    monkeypatch.setattr("ai_gif_skill.pipelines.generate_sheet", _fake_generate_sheet)
    monkeypatch.setattr("ai_gif_skill.pipelines.run_cutout", _fake_run_cutout)
    monkeypatch.setattr("ai_gif_skill.pipelines.assemble_gif_from_sheet", _fake_gif)

    payload = run_sheet_pipeline(
        request=SheetPipelineRequest(
            template_image_path=tmp_path / "template.png",
            generated_image_path=tmp_path / "generated.png",
            cutout_image_path=tmp_path / "cutout.png",
            output_gif_path=tmp_path / "final.gif",
            generation=GenerationRequest(
                prompt="test",
                background="#00FF00",
                rows=2,
                cols=4,
                cell_width=32,
                cell_height=32,
            ),
        ),
        provider="grok",
    )

    assert stage_calls == ["generate-sheet", "cutout", "gif-from-sheet"]
    assert payload["provider"] == "grok"
    assert payload["final_output_path"] == str(tmp_path / "final.gif")
    assert payload["stages"] == ["generate-sheet", "cutout", "gif-from-sheet"]


def test_run_video_pipeline_supports_mixed_providers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stage_calls: list[str] = []

    def _fake_generate_image(**kwargs: object) -> dict[str, object]:
        stage_calls.append(f"generate-image:{kwargs['provider']}")
        Path(kwargs["output_image_path"]).write_bytes(b"image")
        return {"output_image_path": str(kwargs["output_image_path"])}

    def _fake_generate_video(**kwargs: object) -> dict[str, object]:
        stage_calls.append(f"generate-video:{kwargs['provider']}")
        kwargs["request"].output_path.write_bytes(b"video")
        return {"output_path": str(kwargs["request"].output_path)}

    def _fake_extract_frames(**kwargs: object) -> dict[str, object]:
        stage_calls.append("extract-frames")
        Path(kwargs["output_dir"]).mkdir(parents=True, exist_ok=True)
        (Path(kwargs["output_dir"]) / "frame-001.png").write_bytes(b"frame")
        return {"output_dir": str(kwargs["output_dir"])}

    def _fake_cutout_frames(**kwargs: object) -> dict[str, object]:
        stage_calls.append("cutout-frames")
        Path(kwargs["output_dir"]).mkdir(parents=True, exist_ok=True)
        (Path(kwargs["output_dir"]) / "frame-001.png").write_bytes(b"frame")
        return {"output_dir": str(kwargs["output_dir"])}

    def _fake_gif(**kwargs: object) -> dict[str, object]:
        stage_calls.append("gif-from-frames")
        Path(kwargs["output_path"]).write_bytes(b"gif")
        return {"output_path": str(kwargs["output_path"])}

    monkeypatch.setattr("ai_gif_skill.pipelines.generate_image", _fake_generate_image)
    monkeypatch.setattr("ai_gif_skill.pipelines.generate_video", _fake_generate_video)
    monkeypatch.setattr("ai_gif_skill.pipelines.extract_frames", _fake_extract_frames)
    monkeypatch.setattr("ai_gif_skill.pipelines.run_cutout_frames", _fake_cutout_frames)
    monkeypatch.setattr("ai_gif_skill.pipelines.assemble_gif_from_frames", _fake_gif)

    payload = run_video_pipeline(
        request=VideoPipelineRequest(
            generated_image_path=tmp_path / "generated.png",
            generated_video_path=tmp_path / "generated.mp4",
            frames_dir=tmp_path / "frames",
            cutout_frames_dir=tmp_path / "cutout-frames",
            output_gif_path=tmp_path / "final.gif",
            image_prompt="image",
            video_prompt="video",
            duration_seconds=2,
            fps=12,
        ),
        image_provider="gemini",
        video_provider="grok",
    )

    assert stage_calls == [
        "generate-image:gemini",
        "generate-video:grok",
        "extract-frames",
        "cutout-frames",
        "gif-from-frames",
    ]
    assert payload["image_provider"] == "gemini"
    assert payload["video_provider"] == "grok"
    assert payload["final_output_path"] == str(tmp_path / "final.gif")
