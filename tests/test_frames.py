import json
from pathlib import Path

from PIL import Image

from ai_gif_skill.frames import extract_frames, read_frames_manifest


def test_extract_frames_writes_manifest_and_frame_directory(tmp_path: Path) -> None:
    video_path = tmp_path / "input.mp4"
    output_dir = tmp_path / "frames"
    video_path.write_bytes(b"fake-video")

    def _fake_runner(command: list[str]) -> None:
        assert command[0] == "ffmpeg"
        output_dir.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(output_dir / "frame-001.png")
        Image.new("RGBA", (8, 8), (0, 255, 0, 255)).save(output_dir / "frame-002.png")

    metadata = extract_frames(
        video_path=video_path,
        output_dir=output_dir,
        fps=12,
        runner=_fake_runner,
    )

    manifest = read_frames_manifest(output_dir)

    assert metadata["frame_count"] == 2
    assert metadata["fps"] == 12
    assert (output_dir / "frame-001.png").exists()
    assert (output_dir / "frame-002.png").exists()
    assert manifest is not None
    assert manifest["frame_count"] == 2
    assert manifest["source_path"] == str(video_path)


def test_read_frames_manifest_returns_none_when_missing(tmp_path: Path) -> None:
    assert read_frames_manifest(tmp_path) is None
