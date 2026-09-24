"""Tests for services.document_intake (MIN-108 — multi-source intake).

Contract: notary.case-drafting.v1 — suggestions carry observation metadata,
never `confirmed`; per-source failure isolation; hard limits §5.2.
"""
import unittest
import uuid
from pathlib import Path

import openpyxl

from services.document_intake import (
    IntakeError,
    IntakeOutcome,
    MAX_FILE_BYTES,
    MAX_TEXT_CHARS,
    analyze,
)


def _sid(n):
    # uuid4 hợp lệ theo contract (version=4, variant=8..b), deterministic cho test
    return f"00000000-0000-4000-8000-{n:012d}"


def _file_source(n, kind, path, size=None):
    return {
        "source_id": _sid(n),
        "kind": kind,
        "file_ref": {
            "path": str(path),
            "scope": "machine_local",
            "size_bytes": Path(path).stat().st_size if size is None else size,
        },
    }


def _text_source(n, text):
    return {"source_id": _sid(n), "kind": "text", "text": text}


CCCD_FRONT_LINES = [
    "CĂN CƯỚC CÔNG DÂN",
    "Họ và tên: NGUYỄN VĂN AN",
    "Số: 001234567890",
    "Ngày sinh: 20/03/1980",
    "Giới tính: Nam",
    "Nơi thường trú: Số 1 Đường ABC, Hà Nội",
]

CCCD_BACK_LINES = [
    "CĂN CƯỚC CÔNG DÂN",
    "IDVNA001234567890<<<<<<<<<<<<<",
    "8003201M2503201VNA<<<<<<<<<<<4",
    "NGUYEN<<VAN<AN<<<<<<<<<<<<<<<<",
    "Ngày cấp: 15/01/2021",
]

PROPERTY_LINES = [
    "GIẤY CHỨNG NHẬN",
    "QUYỀN SỬ DỤNG ĐẤT",
    "Số phát hành (serial): DD 123456",
    "Số vào sổ: VP00166",
    "Thửa đất số: 10",
    "Tờ bản đồ số: 5",
    "Diện tích: 447,0 m2",
    "Địa chỉ: Thôn A, Xã B, Huyện C, Tỉnh D",
    "Ngày cấp: 20/05/2010",
]

# Bản ASCII cho PDF text layer — PyMuPDF insert_text chỉ encode được latin-1
# với font built-in; parser fold dấu nên bản không dấu parse tương đương.
PROPERTY_LINES_ASCII = [
    "GIAY CHUNG NHAN",
    "QUYEN SU DUNG DAT",
    "So phat hanh (serial): DD 123456",
    "So vao so: VP00166",
    "Thua dat so: 10",
    "To ban do so: 5",
    "Dien tich: 447,0 m2",
    "Dia chi: Thon A, Xa B, Huyen C, Tinh D",
    "Ngay cap: 20/05/2010",
]

DEATH_LINES = [
    "GIẤY KHAI TỬ",
    "Họ, chữ đệm, tên người chết: TRẦN THỊ BÌNH",
    "Ngày sinh: 01/02/1940",
    "Giấy tờ tùy thân: 009876543210",
    "Nơi cư trú cuối cùng: Số 2 Đường XYZ, Hà Nội",
    "Đã chết vào ngày: 10/11/2020",
]

# GCN nhiều thửa — parser thật trích land_rows=[{ONT,200.0,Lâu dài},{CLN,247.0,12/2043}]
# và fill flat fields: dien_tich=447 (sum), loai_dat=ONT (thửa đầu).
MULTI_PARCEL_LINES = [
    "GIẤY CHỨNG NHẬN",
    "QUYỀN SỬ DỤNG ĐẤT",
    "Số phát hành (serial): DD 123456",
    "Số vào sổ: VP00166",
    "Thửa đất số: 10",
    "Tờ bản đồ số: 5",
    "c. Loại đất: Đất ở tại nông thôn 200,0m²; Đất trồng cây lâu năm 247,0m²",
    "d. Thời hạn sử dụng: Đất ở tại nông thôn: Lâu dài; Đất trồng cây lâu năm: 12/2043",
    "Địa chỉ: Thôn A, Xã B",
    "Ngày cấp: 20/05/2010",
]


async def _fake_ocr_image(client, *, api_key, model, image_b64, filename, enable_rotate=False):
    """Trả lines theo tên file — fixture CCCD 2 mặt / GCN / giấy báo tử."""
    name = (filename or "").lower()
    if "back" in name:
        return list(CCCD_BACK_LINES)
    if "front" in name or "cccd" in name:
        return list(CCCD_FRONT_LINES)
    if "death" in name:
        return list(DEATH_LINES)
    if "gcn" in name or "property" in name or "so_do" in name:
        return list(PROPERTY_LINES)
    return ["không đọc được gì"]


async def _fake_ocr_by_page(client, *, api_key, model, image_b64, filename, enable_rotate=False):
    name = (filename or "").lower()
    if "#p1" in name:
        return list(CCCD_FRONT_LINES)
    if "#p2" in name:
        return list(CCCD_BACK_LINES)
    return list(PROPERTY_LINES)


def _walk_strings(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)
    elif isinstance(obj, str):
        yield obj


def _make_pdf(tmp_path, name: str, page_texts: list) -> Path:
    import fitz

    pdf = fitz.open()
    for text in page_texts:
        page = pdf.new_page()
        if text:
            page.insert_text((72, 72), text)
    out = Path(tmp_path) / name
    pdf.save(str(out))
    pdf.close()
    return out


def _make_docx(tmp_path, name: str, lines: list) -> Path:
    import docx

    document = docx.Document()
    for line in lines:
        document.add_paragraph(line)
    out = Path(tmp_path) / name
    document.save(str(out))
    return out


def _make_xlsx(tmp_path, name: str, headers: list, rows: list) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DanhSach"
    ws.append(headers)
    for row in rows:
        ws.append(row)
    out = Path(tmp_path) / name
    wb.save(str(out))
    return out


class SourceValidationTests(unittest.TestCase):
    """Job-level limits → IntakeError với contract codes."""

    def test_too_many_sources(self):
        sources = [_text_source(i, "x") for i in range(1, 10)]
        with self.assertRaises(IntakeError) as cm:
            analyze(sources)
        self.assertEqual(cm.exception.code, "intake_too_many_sources")

    def test_empty_sources(self):
        with self.assertRaises(IntakeError) as cm:
            analyze([])
        self.assertEqual(cm.exception.code, "validation_error")

    def test_unsupported_kind(self):
        with self.assertRaises(IntakeError) as cm:
            analyze([{"source_id": _sid(1), "kind": "zip", "text": "x"}])
        self.assertEqual(cm.exception.code, "intake_unsupported_source")

    def test_duplicate_source_id(self):
        src = _text_source(1, "abc")
        with self.assertRaises(IntakeError) as cm:
            analyze([src, dict(src)])
        self.assertEqual(cm.exception.code, "validation_error")

    def test_text_over_limit(self):
        with self.assertRaises(IntakeError) as cm:
            analyze([_text_source(1, "x" * (MAX_TEXT_CHARS + 1))])
        self.assertEqual(cm.exception.code, "intake_text_too_long")

    def test_text_with_file_ref_rejected(self):
        src = _text_source(1, "abc")
        src["file_ref"] = {"path": "D:/x.txt", "scope": "machine_local", "size_bytes": 3}
        with self.assertRaises(IntakeError) as cm:
            analyze([src])
        self.assertEqual(cm.exception.code, "validation_error")

    def test_declared_size_over_limit(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.png"
            p.write_bytes(b"img")
            src = _file_source(1, "image", str(p), size=MAX_FILE_BYTES + 1)
            with self.assertRaises(IntakeError) as cm:
                analyze([src])
            self.assertEqual(cm.exception.code, "intake_source_too_large")

    def test_actual_size_over_limit(self):
        # Declared size đã > limit → job-level validation trước khi đọc file.
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "big.png"
            p.write_bytes(b"x" * (MAX_FILE_BYTES + 1))
            src = _file_source(1, "image", str(p))  # declared = actual > limit
            with self.assertRaises(IntakeError) as cm:
                analyze([src])
            self.assertEqual(cm.exception.code, "intake_source_too_large")

    def test_misdeclared_size_per_source_error(self):
        # Declared nhỏ nhưng file thật > limit → per-source error (stat trước
        # read nên file > limit không bao giờ được đọc vào RAM).
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "big.png"
            p.write_bytes(b"x" * (MAX_FILE_BYTES + 1))
            src = _file_source(1, "image", str(p), size=100)
            outcome = analyze([src, _text_source(2, "abc")], api_key="k")
        self.assertEqual(outcome.status, "partial")
        self.assertEqual(outcome.errors[0]["code"], "intake_source_too_large")
        self.assertEqual(outcome.errors[0]["source_id"], _sid(1))

    def test_is_dir_true_rejected(self):
        src = {
            "source_id": _sid(1),
            "kind": "pdf",
            "file_ref": {
                "path": "D:/folder",
                "scope": "machine_local",
                "size_bytes": 1,
                "is_dir": True,
            },
        }
        with self.assertRaises(IntakeError) as cm:
            analyze([src])
        self.assertEqual(cm.exception.code, "validation_error")

    def test_missing_size_bytes_rejected(self):
        src = {
            "source_id": _sid(1),
            "kind": "pdf",
            "file_ref": {"path": "D:/x.pdf", "scope": "machine_local"},
        }
        with self.assertRaises(IntakeError) as cm:
            analyze([src])
        self.assertEqual(cm.exception.code, "validation_error")

    def test_bad_scope_rejected(self):
        src = {
            "source_id": _sid(1),
            "kind": "pdf",
            "file_ref": {"path": "D:/x.pdf", "scope": "onedrive", "size_bytes": 1},
        }
        with self.assertRaises(IntakeError) as cm:
            analyze([src])
        self.assertEqual(cm.exception.code, "file_scope_not_supported")

    def test_relative_path_rejected(self):
        src = {
            "source_id": _sid(1),
            "kind": "pdf",
            "file_ref": {"path": "docs/x.pdf", "scope": "machine_local", "size_bytes": 1},
        }
        with self.assertRaises(IntakeError) as cm:
            analyze([src])
        self.assertEqual(cm.exception.code, "file_scope_not_supported")

    def test_missing_file_ref_for_file_kind(self):
        with self.assertRaises(IntakeError) as cm:
            analyze([{"source_id": _sid(1), "kind": "pdf"}])
        self.assertEqual(cm.exception.code, "validation_error")

    def test_text_on_file_kind_rejected(self):
        src = _text_source(1, "abc")
        src["kind"] = "pdf"
        with self.assertRaises(IntakeError) as cm:
            analyze([src])
        self.assertEqual(cm.exception.code, "validation_error")


class ShapeInvariantTests(unittest.TestCase):
    """Contract §4 invariants trên mọi suggestion."""

    def test_no_confirmed_no_empty_raw(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "cccd_front.png"
            img.write_bytes(b"fake-image-bytes")
            outcome = analyze(
                [_file_source(1, "image", str(img))],
                api_key="k", ocr_call=_fake_ocr_image)
        self.assertEqual(outcome.status, "succeeded")
        data = outcome.result_data
        blob = list(_walk_strings(data))
        self.assertNotIn("confirmed", blob)
        for s in data["suggestions"]:
            uuid.UUID(s["suggestion_id"])  # uuid4
            self.assertIn(s["target"], ("person", "asset"))
            for name, f in s["fields"].items():
                self.assertIn(f["observation_state"], ("observed", "normalized", "inferred"))
                if f["observation_state"] != "inferred":
                    self.assertIsNone(f["confidence"])
                self.assertTrue(f["source_refs"], f"{name} thiếu source_refs")
                self.assertNotEqual(f["raw_value"], "")

    def test_raw_differs_from_normalized(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "cccd_front.png"
            img.write_bytes(b"fake-image-bytes")
            outcome = analyze(
                [_file_source(1, "image", str(img))],
                api_key="k", ocr_call=_fake_ocr_image)
        sug = outcome.result_data["suggestions"][0]
        self.assertEqual(sug["target"], "person")
        fields = sug["fields"]
        # name uppercase → title case normalized
        self.assertEqual(fields["ho_ten"]["raw_value"], "NGUYỄN VĂN AN")
        self.assertEqual(fields["ho_ten"]["normalized_value"], "Nguyễn Văn An")
        self.assertEqual(fields["ho_ten"]["observation_state"], "normalized")
        self.assertIsNone(fields["ho_ten"]["confidence"])
        # date dd/mm/YYYY → YYYY-MM-DD
        self.assertEqual(fields["ngay_sinh"]["normalized_value"], "1980-03-20")


class ImageAdapterTests(unittest.TestCase):
    def test_cccd_front_person(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "cccd_front.png"
            img.write_bytes(b"fake-image")
            outcome = analyze(
                [_file_source(1, "image", str(img))],
                api_key="k", ocr_call=_fake_ocr_image)
        self.assertEqual(outcome.status, "succeeded")
        sug = outcome.result_data["suggestions"][0]
        self.assertEqual(sug["target"], "person")
        self.assertEqual(sug["fields"]["so_giay_to"]["normalized_value"], "001234567890")
        self.assertEqual(sug["fields"]["gioi_tinh"]["normalized_value"], "Nam")

    def test_death_certificate_person(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "death.png"
            img.write_bytes(b"fake-image")
            outcome = analyze(
                [_file_source(1, "image", str(img))],
                api_key="k", ocr_call=_fake_ocr_image)
        sug = outcome.result_data["suggestions"][0]
        self.assertEqual(sug["target"], "person")
        self.assertEqual(sug["fields"]["ngay_chet"]["normalized_value"], "2020-11-10")

    def test_property_asset(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "gcn.png"
            img.write_bytes(b"fake-image")
            outcome = analyze(
                [_file_source(1, "image", str(img))],
                api_key="k", ocr_call=_fake_ocr_image)
        sug = outcome.result_data["suggestions"][0]
        self.assertEqual(sug["target"], "asset")
        self.assertEqual(
            sug["fields"]["so_serial"]["normalized_value"], "DD123456")
        self.assertEqual(sug["fields"]["so_serial"]["observation_state"], "inferred")
        self.assertIsNotNone(sug["fields"]["so_serial"]["confidence"])
        self.assertEqual(sug["fields"]["dien_tich"]["normalized_value"], 447.0)

    def test_missing_api_key_is_per_source_error(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "cccd_front.png"
            img.write_bytes(b"fake-image")
            outcome = analyze(
                [_file_source(1, "image", str(img)), _text_source(2, "ngẫu nhiên")],
                api_key="", ocr_call=_fake_ocr_image)
        self.assertEqual(outcome.status, "partial")
        err = outcome.errors[0]
        self.assertEqual(err["code"], "ocr.engine_unavailable")
        self.assertEqual(err["source_id"], _sid(1))
        # text source vẫn được xử lý (parse_failed ở đây vì text vô nghĩa)
        self.assertEqual(set(outcome.failed + outcome.succeeded), {_sid(1), _sid(2)})

    def test_ocr_failure_does_not_stop_other_sources(self):
        import tempfile
        async def _boom(client, **kw):
            raise RuntimeError("engine down")
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "cccd_front.png"
            img.write_bytes(b"fake-image")
            xlsx = _make_xlsx(td, "people.xlsx",
                              ["Họ tên", "Giới tính", "Ngày sinh", "Số giấy tờ"],
                              [["Nguyen Van A", "Nam", "1988", "111222333444"]])
            outcome = analyze(
                [_file_source(1, "image", str(img)), _file_source(2, "xlsx", str(xlsx))],
                api_key="k", ocr_call=_boom)
        self.assertEqual(outcome.status, "partial")
        self.assertEqual(outcome.failed, [_sid(1)])
        self.assertEqual(outcome.succeeded, [_sid(2)])
        self.assertEqual(outcome.errors[0]["code"], "ocr.engine_unavailable")
        self.assertEqual(len(outcome.suggestions), 1)

    def test_wrong_extension_parse_failed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "evil.exe"
            f.write_bytes(b"MZ")
            outcome = analyze([_file_source(1, "image", str(f))], api_key="k")
        self.assertEqual(outcome.status, "partial")
        self.assertEqual(outcome.errors[0]["code"], "intake.parse_failed")

    def test_missing_file_per_source_error(self):
        outcome = analyze(
            [{"source_id": _sid(1), "kind": "image",
              "file_ref": {"path": "D:/nonexistent_dir_xyz/no.png",
                           "scope": "machine_local", "size_bytes": 5}},
             _text_source(2, "tối thiểu text")],
            api_key="k")
        self.assertIn(_sid(1), outcome.failed)
        self.assertEqual(outcome.errors[0]["code"], "file_not_found")


class PdfAdapterTests(unittest.TestCase):
    def test_pdf_text_layer_property(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            pdf = _make_pdf(td, "gcn.pdf", ["\n".join(PROPERTY_LINES_ASCII)])
            outcome = analyze([_file_source(1, "pdf", str(pdf))], api_key="k")
        self.assertEqual(outcome.status, "succeeded")
        sug = outcome.result_data["suggestions"][0]
        self.assertEqual(sug["target"], "asset")
        self.assertEqual(sug["fields"]["so_serial"]["normalized_value"], "DD123456")
        refs = sug["fields"]["so_serial"]["source_refs"]
        self.assertTrue(any(r.get("page") == 1 for r in refs))

    def test_pdf_scanned_pages_use_ocr_and_pair(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            # 2 trang không text layer → OCR path
            pdf = _make_pdf(td, "cccd.pdf", ["", ""])
            outcome = analyze(
                [_file_source(1, "pdf", str(pdf))],
                api_key="k", ocr_call=_fake_ocr_by_page)
        self.assertEqual(outcome.status, "succeeded")
        sugs = outcome.result_data["suggestions"]
        self.assertEqual(len(sugs), 1)
        sug = sugs[0]
        self.assertEqual(sug["target"], "person")
        self.assertEqual(sug["fields"]["so_giay_to"]["normalized_value"], "001234567890")
        # ghép mặt sau: ngay_cap lấy từ trang back
        self.assertEqual(sug["fields"]["ngay_cap"]["normalized_value"], "2021-01-15")
        pages = {r.get("page") for f in sug["fields"].values() for r in f["source_refs"]}
        self.assertEqual(pages, {1, 2})

    def test_pdf_scanned_no_api_key(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            pdf = _make_pdf(td, "scan.pdf", [""])
            outcome = analyze([_file_source(1, "pdf", str(pdf))], api_key="")
        self.assertEqual(outcome.status, "partial")
        self.assertEqual(outcome.errors[0]["code"], "ocr.engine_unavailable")

    def test_pdf_too_many_pages(self):
        # Limit §5.2 phát hiện lúc mở file → per-source error, không hủy batch.
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            pdf = _make_pdf(td, "big.pdf", [f"page {i}" for i in range(51)])
            ok = _make_xlsx(td, "people.xlsx", ["Họ tên"], [["Nguyen A"]])
            outcome = analyze(
                [_file_source(1, "pdf", str(pdf)), _file_source(2, "xlsx", str(ok))],
                api_key="k")
        self.assertEqual(outcome.status, "partial")
        self.assertEqual(outcome.failed, [_sid(1)])
        self.assertEqual(outcome.succeeded, [_sid(2)])
        self.assertEqual(outcome.errors[0]["code"], "intake_source_too_large")


class DocxAdapterTests(unittest.TestCase):
    def test_docx_property(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f = _make_docx(td, "gcn.docx", PROPERTY_LINES)
            outcome = analyze([_file_source(1, "docx", str(f))], api_key="k")
        self.assertEqual(outcome.status, "succeeded")
        sug = outcome.result_data["suggestions"][0]
        self.assertEqual(sug["target"], "asset")
        self.assertEqual(sug["fields"]["so_serial"]["normalized_value"], "DD123456")

    def test_docx_corrupt_parse_failed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "bad.docx"
            f.write_bytes(b"not a docx")
            outcome = analyze([_file_source(1, "docx", str(f))], api_key="k")
        self.assertEqual(outcome.status, "partial")
        self.assertEqual(outcome.errors[0]["code"], "intake.parse_failed")


class ExcelAdapterTests(unittest.TestCase):
    def test_person_rows_with_cell_refs(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f = _make_xlsx(
                td, "people.xlsx",
                ["Họ tên", "Giới tính", "Ngày sinh", "Số giấy tờ", "Địa chỉ"],
                [
                    ["NGUYỄN VĂN A", "Nam", "1988", "111 222 333 444", "Hà Nội"],
                    ["Trần Thị B", "Nữ", "1990-05-10", "", "Nam Định"],
                ])
            outcome = analyze([_file_source(1, "xlsx", str(f))], api_key="k")
        self.assertEqual(outcome.status, "succeeded")
        sugs = outcome.result_data["suggestions"]
        self.assertEqual(len(sugs), 2)
        first = sugs[0]
        self.assertEqual(first["target"], "person")
        self.assertEqual(first["fields"]["ho_ten"]["normalized_value"], "Nguyễn Văn A")
        self.assertEqual(
            first["fields"]["so_giay_to"]["normalized_value"], "111222333444")
        ref = first["fields"]["ho_ten"]["source_refs"][0]
        self.assertEqual(ref["sheet"], "DanhSach")
        self.assertEqual(ref["cell"], "A2")
        # row 2 (sheet row 3)
        second = sugs[1]
        self.assertEqual(second["fields"]["gioi_tinh"]["normalized_value"], "Nữ")
        self.assertEqual(second["fields"]["ngay_sinh"]["normalized_value"], "1990-05-10")

    def test_missing_required_column_parse_failed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f = _make_xlsx(td, "bad.xlsx", ["A", "B"], [["1", "2"]])
            outcome = analyze([_file_source(1, "xlsx", str(f))], api_key="k")
        self.assertEqual(outcome.status, "partial")
        self.assertEqual(outcome.errors[0]["code"], "intake.parse_failed")


class TextAdapterTests(unittest.TestCase):
    def test_pasted_property_text(self):
        outcome = analyze([_text_source(1, "\n".join(PROPERTY_LINES))], api_key="k")
        self.assertEqual(outcome.status, "succeeded")
        sug = outcome.result_data["suggestions"][0]
        self.assertEqual(sug["target"], "asset")
        self.assertTrue(any("span" in r for f in sug["fields"].values() for r in f["source_refs"]))

    def test_cccd_qr_text(self):
        qr = "001234567890|012345678|Nguyen Van An|20031980|Nam|So 1 Duong ABC, Ha Noi|15012021"
        outcome = analyze([_text_source(1, qr)], api_key="k")
        self.assertEqual(outcome.status, "succeeded")
        sug = outcome.result_data["suggestions"][0]
        self.assertEqual(sug["target"], "person")
        self.assertEqual(sug["fields"]["so_giay_to"]["normalized_value"], "001234567890")
        self.assertEqual(sug["fields"]["ngay_sinh"]["normalized_value"], "1980-03-20")

    def test_garbage_text_parse_failed(self):
        outcome = analyze([_text_source(1, "12345")], api_key="k")
        self.assertEqual(outcome.status, "partial")
        self.assertEqual(outcome.errors[0]["code"], "intake.parse_failed")

    def test_land_rows_multi_parcel(self):
        # I-1: GCN nhiều thửa → field land_rows (JSON normalized_value) +
        # warning intake.multi_parcel; flat fields vẫn đúng (sum / thửa đầu).
        import json
        outcome = analyze(
            [_text_source(1, "\n".join(MULTI_PARCEL_LINES))], api_key="k")
        self.assertEqual(outcome.status, "succeeded")
        sug = outcome.result_data["suggestions"][0]
        self.assertEqual(sug["target"], "asset")

        land = sug["fields"].get("land_rows")
        self.assertIsNotNone(land, "thiếu field land_rows cho GCN nhiều thửa")
        rows = json.loads(land["normalized_value"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            rows[0],
            {"loai_dat": "ONT", "dien_tich": 200, "thoi_han": "Lâu dài"})
        self.assertEqual(
            rows[1],
            {"loai_dat": "CLN", "dien_tich": 247, "thoi_han": "12/2043"})
        self.assertEqual(land["observation_state"], "normalized")
        self.assertIsNone(land["confidence"])
        self.assertTrue(land["raw_value"])
        self.assertTrue(any("span" in r for r in land["source_refs"]))

        codes = [w["code"] for w in sug["warnings"]]
        self.assertIn("intake.multi_parcel", codes)
        # Flat fields không đổi: dien_tich = tổng, loai_dat = thửa đầu.
        self.assertEqual(sug["fields"]["dien_tich"]["normalized_value"], 447)
        self.assertEqual(sug["fields"]["loai_dat"]["normalized_value"], "ONT")

    def test_single_parcel_no_land_rows_field(self):
        # 1 thửa → flat fields đủ, không emit land_rows (field chỉ cho ≥2).
        lines = [ln for ln in MULTI_PARCEL_LINES
                 if not ln.startswith(("c.", "d."))]
        lines.insert(6, "Loại đất: Đất ở tại nông thôn 200,0m²")
        outcome = analyze([_text_source(1, "\n".join(lines))], api_key="k")
        sug = outcome.result_data["suggestions"][0]
        self.assertNotIn("land_rows", sug["fields"])
        codes = [w["code"] for w in sug["warnings"]]
        self.assertNotIn("intake.multi_parcel", codes)

    def test_unsupported_target_vs_parse_failed(self):
        # M-1: doc_type nhận diện được nhưng chưa map person/asset
        # → intake.unsupported_target (unknown/missing → parse_failed).
        from services.document_intake import ocr_pipeline
        orig = ocr_pipeline._normalize_native_ocr_doc

        def _fake_marriage(lines, filename):
            return {"doc_type": "marriage",
                    "data": {"vo": "A", "chong": "B"},
                    "filename": filename}

        ocr_pipeline._normalize_native_ocr_doc = _fake_marriage
        try:
            outcome = analyze([_text_source(1, "giay chung nhan ket hon")],
                              api_key="k")
        finally:
            ocr_pipeline._normalize_native_ocr_doc = orig
        self.assertEqual(outcome.status, "partial")
        self.assertEqual(
            outcome.errors[0]["code"], "intake.unsupported_target")


class AggregationTests(unittest.TestCase):
    def test_partial_breakdown(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "bad.docx"
            bad.write_bytes(b"junk")
            ok = _make_xlsx(td, "people.xlsx", ["Họ tên"], [["Nguyen A"]])
            outcome = analyze(
                [_file_source(1, "docx", str(bad)), _file_source(2, "xlsx", str(ok))],
                api_key="k")
        self.assertEqual(outcome.status, "partial")
        data = outcome.result_data
        self.assertEqual(data["breakdown"]["succeeded"], [_sid(2)])
        self.assertEqual(data["breakdown"]["failed"], [_sid(1)])
        self.assertEqual(len(data["suggestions"]), 1)
        self.assertEqual(len(data["errors"]), 1)

    def test_all_failed_status(self):
        outcome = analyze([_text_source(1, "12345")], api_key="k")
        self.assertEqual(outcome.status, "partial")
        self.assertEqual(outcome.succeeded, [])

    def test_all_succeeded_status(self):
        outcome = analyze([_text_source(1, "\n".join(PROPERTY_LINES))], api_key="k")
        self.assertEqual(outcome.status, "succeeded")
        self.assertNotIn("breakdown", outcome.result_data)

    def test_cancel_between_sources(self):
        calls = {"n": 0}
        def _cancel():
            calls["n"] += 1
            if calls["n"] > 1:
                raise RuntimeError("user_canceled")
        with self.assertRaises(RuntimeError):
            analyze(
                [_text_source(1, "\n".join(PROPERTY_LINES)),
                 _text_source(2, "\n".join(PROPERTY_LINES))],
                check_cancel=_cancel, api_key="k")

    def test_result_schema_version(self):
        outcome = analyze([_text_source(1, "\n".join(PROPERTY_LINES))], api_key="k")
        self.assertEqual(outcome.result_data["schema_version"], "notary.case-drafting.v1")


if __name__ == "__main__":
    unittest.main()
