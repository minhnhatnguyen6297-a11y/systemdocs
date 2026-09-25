"""MIN-103 slice C — offline tests for the ported OCR primitives.

Covers ``zalo_module.ocr.{errors,qwen,prep}`` against the legacy behavior of
``notary_v2/services/document_intake/ocr_pipeline.py`` and
``services/zalo_inbox.py``. No network, no real Qwen key: ``call_qwen_ocr``
always receives an injected fake async client, and every image/PDF input is
synthesized in-test with PIL/PyMuPDF.
"""
from __future__ import annotations

import asyncio
import base64
import importlib
import io
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from PIL import Image

import zalo_module.ocr.qwen as qwen_mod
from zalo_module.ocr import (
    OcrApiError,
    OcrError,
    OcrParseError,
    OcrTransportError,
    call_qwen_ocr,
    clean_text,
    extract_native_ocr_lines,
    inspect_media,
    prepare_ai_image_bytes,
    proposed_crop,
    render_pdf_pages,
    write_processed_image,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run(coro):
    return asyncio.run(coro)


class FakeClient:
    """Injected async transport — records the request, returns/raises canned."""

    def __init__(self, response: httpx.Response | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    async def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append(
            {"url": url, "headers": headers or {}, "json": json, "timeout": timeout}
        )
        if self.error is not None:
            raise self.error
        return self.response


def ok_client(payload: dict) -> FakeClient:
    return FakeClient(response=httpx.Response(200, json=payload))


def ocr_payload(lines_text: str) -> dict:
    return {"output": {"choices": [{"message": {"content": lines_text}}]}}


@pytest.fixture(autouse=True)
def clean_ocr_env(monkeypatch):
    """Ambient env must not leak into call-time resolution."""
    for name in (
        "QWEN_API_KEY",
        "DASHSCOPE_API_KEY",
        "OCR_MODEL",
        "QWEN_OCR_BASE_URL",
        "QWEN_OCR_ENABLE_ROTATE",
        "QWEN_OCR_MIN_PIXELS",
        "QWEN_OCR_MAX_PIXELS",
        "QWEN_MAX_IMAGE_PX",
        "OCR_AI_TIMEOUT_SECONDS",
        "OCR_AI_CONCURRENCY",
    ):
        monkeypatch.delenv(name, raising=False)


def make_png_bytes(size=(400, 300), color=(255, 255, 255)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return buf.getvalue()


def make_pdf(tmp_path: Path, pages: int = 2, size=(200, 100)) -> Path:
    import fitz

    doc = fitz.open()
    for _ in range(pages):
        doc.new_page(width=size[0], height=size[1])
    path = tmp_path / "sample.pdf"
    doc.save(path)
    doc.close()
    return path


# ---------------------------------------------------------------------------
# Constants parity (ocr_pipeline.py:36-48)
# ---------------------------------------------------------------------------


def test_constants_match_legacy_defaults():
    assert qwen_mod.DEFAULT_MODEL == "qwen-vl-ocr-2025-11-20"
    assert qwen_mod.QWEN_OCR_BASE_URL == "https://dashscope-intl.aliyuncs.com"
    assert qwen_mod.QWEN_OCR_MIN_PIXELS == 3072
    assert qwen_mod.QWEN_OCR_MAX_PIXELS == 8388608
    assert qwen_mod.QWEN_OCR_ENABLE_ROTATE is False
    assert qwen_mod.OCR_AI_CONCURRENCY == 6
    assert qwen_mod.AI_TIMEOUT_SECONDS == 90.0
    assert qwen_mod.AI_MAX_IMAGE_PX == 1800
    assert qwen_mod.JPEG_QUALITY == 82


def test_import_time_env_overrides(monkeypatch):
    monkeypatch.setenv("QWEN_OCR_MIN_PIXELS", "4096")
    monkeypatch.setenv("QWEN_OCR_MAX_PIXELS", "1000")
    monkeypatch.setenv("QWEN_OCR_ENABLE_ROTATE", "1")
    monkeypatch.setenv("OCR_AI_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("OCR_AI_CONCURRENCY", "2")
    monkeypatch.setenv("QWEN_MAX_IMAGE_PX", "5000")
    monkeypatch.setenv("QWEN_OCR_BASE_URL", "https://example.test/")
    reloaded = importlib.reload(qwen_mod)
    try:
        assert reloaded.QWEN_OCR_MIN_PIXELS == 4096
        assert reloaded.QWEN_OCR_MAX_PIXELS == 1000
        assert reloaded.QWEN_OCR_ENABLE_ROTATE is True
        assert reloaded.AI_TIMEOUT_SECONDS == 45.0
        assert reloaded.OCR_AI_CONCURRENCY == 2
        assert reloaded.AI_MAX_IMAGE_PX == 5000  # above the 640 floor
        assert reloaded.QWEN_OCR_BASE_URL == "https://example.test"  # rstripped
    finally:
        monkeypatch.undo()
        importlib.reload(qwen_mod)


# ---------------------------------------------------------------------------
# Golden request body — literal copy of the legacy payload semantics
# (ocr_pipeline.py:388-406)
# ---------------------------------------------------------------------------


def test_call_qwen_ocr_sends_exact_legacy_body():
    image_bytes = b"\xff\xd8raw-image-bytes"
    b64 = base64.b64encode(image_bytes).decode()
    client = ok_client(ocr_payload("dòng một\ndòng hai"))

    lines = run(call_qwen_ocr(image_bytes, api_key="sk-test", client=client))

    assert lines == ["dòng một", "dòng hai"]
    assert len(client.calls) == 1
    call = client.calls[0]
    assert (
        call["url"]
        == "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    )
    assert call["headers"] == {
        "Authorization": "Bearer sk-test",
        "Content-Type": "application/json",
    }
    golden = {
        "model": "qwen-vl-ocr-2025-11-20",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": f"data:image/jpeg;base64,{b64}",
                            "min_pixels": 3072,
                            "max_pixels": 8388608,
                            "enable_rotate": False,
                        }
                    ],
                }
            ]
        },
        "parameters": {"ocr_options": {"task": "text_recognition"}},
    }
    assert call["json"] == golden
    # Serialized wire parity — identical bytes on the wire either way.
    assert json.dumps(call["json"], sort_keys=True) == json.dumps(golden, sort_keys=True)


def test_call_qwen_ocr_accepts_preencoded_b64():
    b64 = base64.b64encode(b"img").decode()
    client = ok_client(ocr_payload("x"))
    run(call_qwen_ocr(b64, api_key="k", client=client))
    assert client.calls[0]["json"]["input"]["messages"][0]["content"][0][
        "image"
    ] == f"data:image/jpeg;base64,{b64}"


def test_call_qwen_ocr_param_overrides():
    client = ok_client(ocr_payload("x"))
    run(
        call_qwen_ocr(
            b"img",
            api_key="k",
            model="qwen-vl-ocr-latest",
            base_url="https://alt.example.com/",
            min_pixels=100,
            max_pixels=200,
            enable_rotate="1",
            timeout=7,
            client=client,
        )
    )
    call = client.calls[0]
    content = call["json"]["input"]["messages"][0]["content"][0]
    assert call["url"] == "https://alt.example.com/api/v1/services/aigc/multimodal-generation/generation"
    assert call["json"]["model"] == "qwen-vl-ocr-latest"
    assert content["min_pixels"] == 100
    assert content["max_pixels"] == 200
    assert content["enable_rotate"] is True
    assert call["timeout"] == 7.0


def test_settings_take_precedence_over_env(monkeypatch):
    monkeypatch.setenv("OCR_MODEL", "qwen-env-model")
    monkeypatch.setenv("QWEN_API_KEY", "env-key")
    settings = SimpleNamespace(
        qwen_api_base="https://settings.example.com",
        qwen_model="qwen-settings-model",
        qwen_api_key="settings-key",
    )
    client = ok_client(ocr_payload("x"))
    run(call_qwen_ocr(b"img", settings=settings, client=client))
    call = client.calls[0]
    assert call["url"].startswith("https://settings.example.com/")
    assert call["json"]["model"] == "qwen-settings-model"
    assert call["headers"]["Authorization"] == "Bearer settings-key"


def test_explicit_kwargs_beat_settings():
    settings = SimpleNamespace(
        qwen_api_base="https://settings.example.com",
        qwen_model="qwen-settings-model",
        qwen_api_key="settings-key",
    )
    client = ok_client(ocr_payload("x"))
    run(
        call_qwen_ocr(
            b"img", api_key="kwarg-key", model="qwen-kwarg", settings=settings, client=client
        )
    )
    call = client.calls[0]
    assert call["headers"]["Authorization"] == "Bearer kwarg-key"
    assert call["json"]["model"] == "qwen-kwarg"


def test_env_fallbacks_for_key_and_model(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dash-key")
    monkeypatch.setenv("OCR_MODEL", "models/QWEN-Custom")
    client = ok_client(ocr_payload("x"))
    run(call_qwen_ocr(b"img", client=client))
    call = client.calls[0]
    # DASHSCOPE_API_KEY is the legacy fallback; models/ prefix stripped + lowered.
    assert call["headers"]["Authorization"] == "Bearer dash-key"
    assert call["json"]["model"] == "qwen-custom"


def test_non_qwen_model_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("OCR_MODEL", "gpt-4o")
    client = ok_client(ocr_payload("x"))
    run(call_qwen_ocr(b"img", api_key="k", client=client))
    assert client.calls[0]["json"]["model"] == "qwen-vl-ocr-2025-11-20"


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------


def test_request_error_maps_to_transport():
    client = FakeClient(error=httpx.RequestError("connection refused"))
    with pytest.raises(OcrTransportError) as ei:
        run(call_qwen_ocr(b"img", api_key="k", client=client))
    assert "Cannot reach Qwen OCR endpoint" in str(ei.value)


def test_timeout_maps_to_transport():
    client = FakeClient(error=httpx.ConnectTimeout("timed out"))
    with pytest.raises(OcrTransportError):
        run(call_qwen_ocr(b"img", api_key="k", client=client))


def test_non_2xx_maps_to_api_error_with_truncated_body():
    client = FakeClient(response=httpx.Response(500, text="x" * 400))
    with pytest.raises(OcrApiError) as ei:
        run(call_qwen_ocr(b"img", api_key="k", client=client))
    assert ei.value.status_code == 500
    assert ei.value.body == "x" * 300  # legacy resp.text[:300] cap


def test_invalid_json_maps_to_parse_error():
    client = FakeClient(response=httpx.Response(200, content=b"<html>nope</html>"))
    with pytest.raises(OcrParseError):
        run(call_qwen_ocr(b"img", api_key="k", client=client))


def test_missing_api_key_raises_ocr_error():
    client = FakeClient()
    with pytest.raises(OcrError, match="Missing API key"):
        run(call_qwen_ocr(b"img", client=client))
    assert client.calls == []


# ---------------------------------------------------------------------------
# extract_native_ocr_lines — golden cases (ocr_pipeline.py:346-374)
# ---------------------------------------------------------------------------


def test_extract_lines_str_content():
    payload = ocr_payload("  line 1  \nline 2\r\n\r\nline 3 ")
    assert extract_native_ocr_lines(payload) == ["line 1", "line 2", "line 3"]


def test_extract_lines_list_content_dicts_and_strings():
    payload = {
        "output": {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"text": "alpha"},
                            {"text": "   "},
                            {"text": "beta"},
                            "gamma",
                            {"nope": 1},
                            42,
                        ]
                    }
                }
            ]
        }
    }
    assert extract_native_ocr_lines(payload) == ["alpha", "beta", "gamma"]


def test_extract_lines_unescapes_literal_backslash_n():
    payload = ocr_payload("first\\nsecond")
    assert extract_native_ocr_lines(payload) == ["first", "second"]


def test_extract_lines_falls_back_to_message_text():
    payload = {"output": {"choices": [{"message": {"text": "t1\nt2"}}]}}
    assert extract_native_ocr_lines(payload) == ["t1", "t2"]


def test_extract_lines_empty_choices_and_missing_output():
    assert extract_native_ocr_lines({"output": {"choices": []}}) == []
    assert extract_native_ocr_lines({}) == []
    assert extract_native_ocr_lines({"output": {}}) == []


def test_extract_lines_cleans_whitespace_per_line():
    payload = ocr_payload("a   b\t\tc\n   \n d ")
    assert extract_native_ocr_lines(payload) == ["a b c", "d"]


def test_clean_text_collapses_whitespace():
    assert clean_text("  a \n b\tc  ") == "a b c"
    assert clean_text(None) == ""
    assert clean_text(123) == "123"


# ---------------------------------------------------------------------------
# prepare_ai_image_bytes — (ocr_pipeline.py:322-343)
# ---------------------------------------------------------------------------


def test_prepare_ai_image_downscales_to_1800_and_reencodes_jpeg():
    src = make_png_bytes(size=(2400, 1200))
    out = prepare_ai_image_bytes(src)
    img = Image.open(io.BytesIO(out))
    assert img.format == "JPEG"
    assert img.size == (1800, 900)
    assert img.mode == "RGB"


def test_prepare_ai_image_applies_exif_orientation():
    img = Image.new("RGB", (100, 200), (10, 20, 30))
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate-90 orientation tag
    buf = io.BytesIO()
    img.save(buf, "JPEG", exif=exif.tobytes())

    out = prepare_ai_image_bytes(buf.getvalue())
    result = Image.open(io.BytesIO(out))
    assert result.size == (200, 100)  # transposed, not (100, 200)


def test_prepare_ai_image_small_image_unchanged_size():
    src = make_png_bytes(size=(800, 600))
    out = prepare_ai_image_bytes(src)
    img = Image.open(io.BytesIO(out))
    assert img.size == (800, 600)
    assert img.format == "JPEG"


def test_prepare_ai_image_respects_max_px_floor_and_param():
    src = make_png_bytes(size=(2000, 1000))
    out = prepare_ai_image_bytes(src, max_px=1000)
    img = Image.open(io.BytesIO(out))
    assert img.size == (1000, 500)


def test_prepare_ai_image_malformed_returns_original():
    garbage = b"this is not an image at all"
    assert prepare_ai_image_bytes(garbage) == garbage


def test_prepare_ai_image_converts_non_rgb():
    buf = io.BytesIO()
    Image.new("RGBA", (100, 100), (255, 0, 0, 128)).save(buf, "PNG")
    out = prepare_ai_image_bytes(buf.getvalue())
    img = Image.open(io.BytesIO(out))
    assert img.mode == "RGB"
    assert img.format == "JPEG"


# ---------------------------------------------------------------------------
# prep.py — proposed_crop / write_processed_image / inspect_media /
# render_pdf_pages (zalo_inbox.py:859-1077)
# ---------------------------------------------------------------------------


def page_with_dark_block(size=(400, 400), block=(60, 60, 340, 340)) -> Image.Image:
    """White page with a dark content block ≈49% area — inside the 0.40-0.97 gate."""
    img = Image.new("RGB", size, (255, 255, 255))
    for y in range(block[1], block[3]):
        for x in range(block[0], block[2]):
            img.putpixel((x, y), (20, 20, 20))
    return img


def test_proposed_crop_returns_bbox_inside_gate():
    bbox = proposed_crop(page_with_dark_block())
    assert bbox is not None
    # bbox roughly bounds the dark block (median/contrast not applied here).
    assert bbox[0] <= 70 and bbox[1] <= 70
    assert bbox[2] >= 330 and bbox[3] >= 330
    # and stays inside the image bounds
    assert 0 <= bbox[0] < bbox[2] <= 400
    assert 0 <= bbox[1] < bbox[3] <= 400


def test_proposed_crop_blank_image_returns_none():
    assert proposed_crop(Image.new("RGB", (300, 300), (255, 255, 255))) is None


def test_proposed_crop_tiny_content_below_ratio_returns_none():
    # ~6% area dark block → below the 0.40 gate.
    img = Image.new("RGB", (400, 400), (255, 255, 255))
    for y in range(0, 50):
        for x in range(0, 50):
            img.putpixel((x, y), (0, 0, 0))
    assert proposed_crop(img) is None


def test_write_processed_image_full_and_crop(tmp_path):
    src = page_with_dark_block(size=(3000, 2000), block=(400, 300, 2600, 1700))
    full, crop = write_processed_image(
        src, tmp_path / "item-full.jpg", tmp_path / "item-crop.jpg"
    )
    assert full.exists() and full.name == "item-full.jpg"
    out = Image.open(full)
    assert out.format == "JPEG"
    assert max(out.size) <= 2400  # thumbnail cap
    assert out.size == (2400, 1600)
    assert crop is not None and crop.exists()
    crop_img = Image.open(crop)
    assert crop_img.format == "JPEG"
    assert 0 < crop_img.width <= 2400 and 0 < crop_img.height <= 1600


def test_write_processed_image_no_crop_when_blank(tmp_path):
    full, crop = write_processed_image(
        Image.new("RGB", (800, 600), (255, 255, 255)), tmp_path / "b-full.jpg"
    )
    assert full.exists()
    assert crop is None


def test_write_processed_image_accepts_path_and_bytes(tmp_path):
    src_path = tmp_path / "src.png"
    src_path.write_bytes(make_png_bytes((500, 500)))
    full, _ = write_processed_image(src_path, tmp_path / "p-full.jpg")
    assert Image.open(full).size == (500, 500)

    full2, _ = write_processed_image(make_png_bytes((320, 240)), tmp_path / "b2-full.jpg")
    assert Image.open(full2).size == (320, 240)


def test_inspect_media_image_path_and_bytes(tmp_path):
    path = tmp_path / "img.png"
    path.write_bytes(make_png_bytes((640, 480)))
    assert inspect_media(path) == (1, 640 * 480)
    assert inspect_media(make_png_bytes((100, 50))) == (1, 100 * 50)
    assert inspect_media(path, mime_type="image/png") == (1, 640 * 480)


def test_inspect_media_pdf_counts_pages_and_zoom_pixels(tmp_path):
    pdf = make_pdf(tmp_path, pages=2, size=(200, 100))
    pages, pixels = inspect_media(pdf)
    assert pages == 2
    # per page: int(200*2) * int(100*2) = 80000
    assert pixels == 2 * (400 * 200)
    # bytes input via %PDF magic sniffing
    assert inspect_media(pdf.read_bytes()) == (2, 2 * 80000)


def test_inspect_media_corrupt_image_raises():
    with pytest.raises(OcrError, match="Ảnh hỏng"):
        inspect_media(b"definitely not an image")


def test_inspect_media_corrupt_pdf_raises(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"%PDF-1.4 broken")
    with pytest.raises(OcrError, match="PDF"):
        inspect_media(bad)


def test_render_pdf_pages_returns_png_per_page(tmp_path):
    pdf = make_pdf(tmp_path, pages=3, size=(200, 100))
    pages = render_pdf_pages(pdf)
    assert len(pages) == 3
    for blob in pages:
        img = Image.open(io.BytesIO(blob))
        assert img.format == "PNG"
        assert img.size == (400, 200)  # Matrix(2,2) zoom


def test_render_pdf_pages_accepts_bytes(tmp_path):
    pdf = make_pdf(tmp_path, pages=1, size=(100, 100))
    pages = render_pdf_pages(pdf.read_bytes())
    assert len(pages) == 1
    assert Image.open(io.BytesIO(pages[0])).size == (200, 200)


def test_render_pdf_pages_corrupt_raises():
    with pytest.raises(OcrError):
        render_pdf_pages(b"not a pdf")


# ---------------------------------------------------------------------------
# No FastAPI coupling in the ocr layer (decision sheet §1.4)
# ---------------------------------------------------------------------------


def test_ocr_layer_has_no_fastapi_imports():
    import ast

    ocr_dir = Path(qwen_mod.__file__).resolve().parent
    for py in ocr_dir.glob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                assert not name.split(".")[0] == "fastapi", f"{py.name}: {name}"


def test_public_package_surface():
    import zalo_module.ocr as pkg

    for name in (
        "call_qwen_ocr",
        "extract_native_ocr_lines",
        "prepare_ai_image_bytes",
        "clean_text",
        "inspect_media",
        "proposed_crop",
        "write_processed_image",
        "render_pdf_pages",
        "OcrError",
        "OcrTransportError",
        "OcrApiError",
        "OcrParseError",
    ):
        assert name in pkg.__all__
        assert callable(getattr(pkg, name)) or name.startswith("Ocr")


def test_error_hierarchy():
    assert issubclass(OcrTransportError, OcrError)
    assert issubclass(OcrApiError, OcrError)
    assert issubclass(OcrParseError, OcrError)
    err = OcrApiError(502, "boom")
    assert err.status_code == 502 and err.body == "boom"
    assert "502" in str(err) and "boom" in str(err)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
