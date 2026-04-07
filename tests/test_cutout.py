from io import BytesIO
from pathlib import Path

from PIL import Image

from ai_gif_skill.cutout import run_cutout


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
        model="isnet-anime",
        remove_background=fake_remove,
    )

    written = Image.open(output_path)

    assert metadata["model"] == "isnet-anime"
    assert metadata["output_path"] == str(output_path)
    assert written.mode == "RGBA"
    assert written.getpixel((0, 0))[3] == 0
