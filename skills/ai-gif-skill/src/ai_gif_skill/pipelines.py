from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .cutout import run_cutout, run_cutout_frames
from .frames import extract_frames
from .generate import GenerationRequest, generate_image, generate_sheet
from .gif import assemble_gif_from_frames, assemble_gif_from_sheet
from .providers.base import DEFAULT_PROVIDER_NAME, normalize_provider_name
from .video import VideoGenerationRequest, generate_video


@dataclass(frozen=True)
class SheetPipelineRequest:
    template_image_path: Path
    generated_image_path: Path
    cutout_image_path: Path
    output_gif_path: Path
    generation: GenerationRequest
    duration_ms: int = 120
    loop: int = 0


@dataclass(frozen=True)
class VideoPipelineRequest:
    generated_image_path: Path
    generated_video_path: Path
    frames_dir: Path
    cutout_frames_dir: Path
    output_gif_path: Path
    image_prompt: str
    video_prompt: str
    duration_seconds: int
    aspect_ratio: str | None = None
    resolution: str | None = None
    fps: float | int | None = None
    duration_ms: int = 120
    loop: int = 0


def run_sheet_pipeline(
    *,
    request: SheetPipelineRequest,
    provider: str = DEFAULT_PROVIDER_NAME,
    model: str | None = None,
    api_key: str | None = None,
) -> dict[str, object]:
    normalized_provider = normalize_provider_name(provider)
    stages = ["generate-sheet", "cutout", "gif-from-sheet"]
    generate_payload = generate_sheet(
        input_image_path=request.template_image_path,
        output_image_path=request.generated_image_path,
        request=request.generation,
        provider=normalized_provider,
        model=model,
        api_key=api_key,
    )
    cutout_payload = run_cutout(
        input_path=request.generated_image_path,
        output_path=request.cutout_image_path,
    )
    gif_payload = assemble_gif_from_sheet(
        sheet_path=request.cutout_image_path,
        output_path=request.output_gif_path,
        rows=request.generation.rows,
        cols=request.generation.cols,
        duration_ms=request.duration_ms,
        loop=request.loop,
    )
    return {
        "provider": normalized_provider,
        "stages": stages,
        "artifacts": {
            "generated_image_path": str(request.generated_image_path),
            "cutout_image_path": str(request.cutout_image_path),
            "output_gif_path": str(request.output_gif_path),
        },
        "final_output_path": str(request.output_gif_path),
        "generate": generate_payload,
        "cutout": cutout_payload,
        "gif": gif_payload,
    }


def run_video_pipeline(
    *,
    request: VideoPipelineRequest,
    provider: str | None = None,
    image_provider: str | None = None,
    video_provider: str | None = None,
    image_model: str | None = None,
    video_model: str | None = None,
    image_api_key: str | None = None,
    video_api_key: str | None = None,
) -> dict[str, object]:
    shared_provider = normalize_provider_name(provider) if provider is not None else None
    resolved_image_provider = normalize_provider_name(image_provider or shared_provider or DEFAULT_PROVIDER_NAME)
    resolved_video_provider = normalize_provider_name(video_provider or shared_provider or DEFAULT_PROVIDER_NAME)

    stages = [
        "generate-image",
        "generate-video",
        "extract-frames",
        "cutout-frames",
        "gif-from-frames",
    ]
    image_payload = generate_image(
        output_image_path=request.generated_image_path,
        prompt=request.image_prompt,
        provider=resolved_image_provider,
        model=image_model,
        api_key=image_api_key,
    )
    video_payload = generate_video(
        request=VideoGenerationRequest(
            prompt=request.video_prompt,
            duration_seconds=request.duration_seconds,
            output_path=request.generated_video_path,
            reference_image_path=request.generated_image_path,
            aspect_ratio=request.aspect_ratio,
            resolution=request.resolution,
        ),
        provider=resolved_video_provider,
        model=video_model,
        api_key=video_api_key,
    )
    frames_payload = extract_frames(
        video_path=request.generated_video_path,
        output_dir=request.frames_dir,
        fps=request.fps,
    )
    cutout_payload = run_cutout_frames(
        input_dir=request.frames_dir,
        output_dir=request.cutout_frames_dir,
    )
    gif_payload = assemble_gif_from_frames(
        frames_dir=request.cutout_frames_dir,
        output_path=request.output_gif_path,
        duration_ms=request.duration_ms,
        loop=request.loop,
    )
    return {
        "image_provider": resolved_image_provider,
        "video_provider": resolved_video_provider,
        "stages": stages,
        "artifacts": {
            "generated_image_path": str(request.generated_image_path),
            "generated_video_path": str(request.generated_video_path),
            "frames_dir": str(request.frames_dir),
            "cutout_frames_dir": str(request.cutout_frames_dir),
            "output_gif_path": str(request.output_gif_path),
        },
        "final_output_path": str(request.output_gif_path),
        "generate_image": image_payload,
        "generate_video": video_payload,
        "extract_frames": frames_payload,
        "cutout_frames": cutout_payload,
        "gif": gif_payload,
    }
