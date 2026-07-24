import asyncio
from io import BytesIO

import PIL.Image
import pytest
from fastapi import BackgroundTasks
from fastapi.exceptions import HTTPException

from pdfserve.pdf import PdfFileInfo, PdfTransform


def _png_bytes(width: int, height: int) -> BytesIO:
    buf = BytesIO()
    PIL.Image.new("RGB", (width, height), color=(255, 0, 0)).save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_load_image_rotate_90_swaps_dimensions():
    info = PdfFileInfo(filename="a.png", content=_png_bytes(100, 50), rotate=90)
    pt = PdfTransform(files=[])

    result = asyncio.run(pt.load_image(info))

    assert result.image is not None
    assert result.image.size == (50, 100)
    assert result.pdf is not None


def test_load_image_rotate_zero_is_noop():
    info = PdfFileInfo(filename="a.png", content=_png_bytes(100, 50), rotate=0)
    pt = PdfTransform(files=[])

    result = asyncio.run(pt.load_image(info))

    assert result.image is not None
    assert result.image.size == (100, 50)


def test_load_image_rotate_180_keeps_dimensions():
    info = PdfFileInfo(filename="a.png", content=_png_bytes(100, 50), rotate=180)
    pt = PdfTransform(files=[])

    result = asyncio.run(pt.load_image(info))

    assert result.image is not None
    assert result.image.size == (100, 50)


def test_pdftransform_applies_rotations_by_index():
    info = PdfFileInfo(filename="a.png", content=_png_bytes(100, 50))
    pt = PdfTransform(files=[info], rotations=[90])

    loaded = asyncio.run(pt.files)

    assert loaded[0].image.size == (50, 100)


def test_pdftransform_without_rotations_leaves_image_untouched():
    info = PdfFileInfo(filename="a.png", content=_png_bytes(100, 50))
    pt = PdfTransform(files=[info])

    loaded = asyncio.run(pt.files)

    assert loaded[0].image.size == (100, 50)


def test_merge_rejects_rotations_length_mismatch():
    try:
        from pdfserve.server.api.pdf import merge_pdf
    except TypeError as exc:  # pragma: no cover
        pytest.skip(f"router import blocked by pre-existing fastapi/pydantic incompatibility: {exc}")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            merge_pdf(
                BackgroundTasks(),
                files=["https://example.com/a.png", "https://example.com/b.png"],
                rotations=[90],
            )
        )

    assert exc.value.status_code == 422
    assert "rotations length" in exc.value.detail
