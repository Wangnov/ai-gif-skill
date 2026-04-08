from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable

from PIL import Image

_MANIFEST_NAME = "frames_manifest.json"
_FRAME_GLOB = "frame-*.png"


def list_frame_paths(directory: Path) -> list[Path]:
    return sorted(path for path in directory.glob(_FRAME_GLOB) if path.is_file())


def read_frames_manifest(directory: Path) -> dict[str, object] | None:
    manifest_path = directory / _MANIFEST_NAME
    if not manifest_path.is_file():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def write_frames_manifest(directory: Path, payload: dict[str, object]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / _MANIFEST_NAME
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def _probe_video_fps(video_path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=r_frame_rate",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    output = subprocess.check_output(command, text=True).strip()
    if "/" in output:
        numerator, denominator = output.split("/", maxsplit=1)
        denominator_value = float(denominator)
        if denominator_value == 0:
            return 0.0
        return float(numerator) / denominator_value
    return float(output)


def extract_frames(
    *,
    video_path: Path,
    output_dir: Path,
    fps: float | int | None = None,
    runner: Callable[[list[str]], None] | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-y", "-i", str(video_path)]
    if fps is not None:
        command.extend(["-vf", f"fps={fps}"])
    command.append(str(output_dir / "frame-%03d.png"))

    if runner is None:
        subprocess.run(command, check=True, capture_output=True, text=True)
    else:
        runner(command)

    frame_paths = list_frame_paths(output_dir)
    if not frame_paths:
        raise ValueError(f"No frames were written to {output_dir}.")

    with Image.open(frame_paths[0]) as first_frame:
        width, height = first_frame.size

    resolved_fps = float(fps) if fps is not None else _probe_video_fps(video_path)
    manifest = {
        "frame_count": len(frame_paths),
        "fps": resolved_fps,
        "source_type": "video",
        "source_path": str(video_path),
        "width": width,
        "height": height,
    }
    write_frames_manifest(output_dir, manifest)
    return {
        "video_path": str(video_path),
        "output_dir": str(output_dir),
        **manifest,
    }
