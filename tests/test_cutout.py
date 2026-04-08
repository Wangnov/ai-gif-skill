from io import BytesIO
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from ai_gif_skill.frames import write_frames_manifest
from ai_gif_skill.cutout import remove_solid_background, run_cutout
from ai_gif_skill.cutout import run_cutout_frames


def test_remove_solid_background_makes_key_color_transparent_and_keeps_subject() -> None:
    source = Image.new("RGB", (4, 4), "#00FF00")
    source.putpixel((1, 1), (40, 120, 240))
    source.putpixel((2, 2), (50, 130, 250))

    result = remove_solid_background(
        source,
        background_color="#00FF00",
        tolerance=8,
    )

    assert result.mode == "RGBA"
    assert result.getpixel((0, 0))[3] == 0
    assert result.getpixel((1, 1))[3] == 255


def test_run_cutout_defaults_to_color_mode(tmp_path: Path) -> None:
    input_path = tmp_path / "input.png"
    output_path = tmp_path / "output.png"

    source = Image.new("RGB", (4, 4), "#00FF00")
    source.putpixel((1, 1), (40, 120, 240))
    source.save(input_path)

    metadata = run_cutout(
        input_path=input_path,
        output_path=output_path,
    )

    written = Image.open(output_path)

    assert metadata["mode"] == "color"
    assert metadata["background_color"] == "#00FF00"
    assert metadata["tolerance"] > 0
    assert written.mode == "RGBA"
    assert written.getpixel((0, 0))[3] == 0
    assert written.getpixel((1, 1))[3] == 255


def test_run_cutout_writes_png_via_injected_remover(tmp_path: Path) -> None:
    input_path = tmp_path / "input.png"
    output_path = tmp_path / "output.png"

    Image.new("RGB", (4, 4), "#00FF00").save(input_path)

    def fake_remove(_data: bytes, **_kwargs: object) -> bytes:
        image = Image.new("RGBA", (4, 4), (0, 0, 255, 255))
        image.putpixel((0, 0), (0, 0, 255, 0))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    metadata = run_cutout(
        input_path=input_path,
        output_path=output_path,
        mode="rembg",
        model="isnet-anime",
        remove_background=fake_remove,
    )

    written = Image.open(output_path)

    assert metadata["mode"] == "rembg"
    assert metadata["model"] == "isnet-anime"
    assert metadata["output_path"] == str(output_path)
    assert written.mode == "RGBA"
    assert written.getpixel((0, 0))[3] == 0


def test_run_cutout_preserves_layout_metadata_from_input(tmp_path: Path) -> None:
    input_path = tmp_path / "input.png"
    output_path = tmp_path / "output.png"

    pnginfo = PngInfo()
    pnginfo.add_text("ai_gif_skill_rows", "2")
    pnginfo.add_text("ai_gif_skill_cols", "4")

    source = Image.new("RGB", (4, 4), "#00FF00")
    source.putpixel((1, 1), (40, 120, 240))
    source.save(input_path, pnginfo=pnginfo)

    run_cutout(
        input_path=input_path,
        output_path=output_path,
    )

    with Image.open(output_path) as written:
        assert written.info["ai_gif_skill_rows"] == "2"
        assert written.info["ai_gif_skill_cols"] == "4"


def test_run_cutout_frames_writes_matching_frame_count_and_manifest(tmp_path: Path) -> None:
    input_dir = tmp_path / "frames"
    output_dir = tmp_path / "cutout-frames"
    input_dir.mkdir()

    frame_1 = Image.new("RGB", (4, 4), "#00FF00")
    frame_1.putpixel((1, 1), (40, 120, 240))
    frame_1.save(input_dir / "frame-001.png")

    frame_2 = Image.new("RGB", (4, 4), "#00FF00")
    frame_2.putpixel((2, 2), (50, 130, 250))
    frame_2.save(input_dir / "frame-002.png")

    write_frames_manifest(
        input_dir,
        {
            "frame_count": 2,
            "fps": 24,
            "source_type": "video",
            "source_path": str(tmp_path / "input.mp4"),
            "width": 4,
            "height": 4,
        },
    )

    metadata = run_cutout_frames(
        input_dir=input_dir,
        output_dir=output_dir,
        tolerance=8,
    )

    written_1 = Image.open(output_dir / "frame-001.png")
    written_2 = Image.open(output_dir / "frame-002.png")

    assert metadata["frame_count"] == 2
    assert metadata["fps"] == 24
    assert written_1.mode == "RGBA"
    assert written_2.mode == "RGBA"
    assert written_1.getpixel((0, 0))[3] == 0
    assert written_2.getpixel((0, 0))[3] == 0
