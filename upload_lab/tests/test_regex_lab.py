from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from docx import Document

from tools import regex_lab


def make_docx(path: Path, *lines: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    document = Document()
    for line in lines:
        document.add_paragraph(line)
    document.save(str(path))
    return path


TRANSFER = (
    "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
    "Độc lập - Tự do - Hạnh phúc",
    "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
    "Chúng tôi gồm có:",
    "I. BÊN CHUYỂN NHƯỢNG: (Bên A)",
    "Ông: Nguyễn Văn A Sinh ngày: 01/01/1980",
    "II. BÊN NHẬN CHUYỂN NHƯỢNG: (Bên B)",
    "Bà: Nguyễn Thị B Sinh ngày: 02/02/1982",
    "ĐIỀU 1: ĐỐI TƯỢNG CỦA HỢP ĐỒNG",
    "Quyền sử dụng đất của bên A có địa chỉ tại: xã A, tỉnh B.",
    "- Thửa đất số: 10",
)


class RegexLabTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.input = self.root / "input"
        self.cache = self.root / "cache"
        self.golden = self.root / "golden"
        self.packets = self.root / "packets"

    def test_ingest_reuses_hash_record(self):
        make_docx(self.input / "one.docx", *TRANSFER)
        first = regex_lab.ingest_corpus(self.input, self.cache)
        record_path = self.cache / "records" / f"{next(iter(first['records']))}.json"
        first_mtime = record_path.stat().st_mtime_ns

        second = regex_lab.ingest_corpus(self.input, self.cache)

        self.assertEqual(second["summary"]["reused_count"], 1)
        self.assertEqual(second["summary"]["extracted_count"], 0)
        self.assertEqual(record_path.stat().st_mtime_ns, first_mtime)

    def test_layout_clusters_are_deterministic(self):
        make_docx(self.input / "a.docx", *TRANSFER, "Nội dung A")
        make_docx(self.input / "b.docx", *TRANSFER, "Nội dung B")
        make_docx(self.input / "other.docx", "KÍNH GỬI: VĂN PHÒNG", "Ông: Nguyễn Văn C")

        index = regex_lab.ingest_corpus(self.input, self.cache)

        by_path = {path: index["records"][content_hash]["cluster_id"] for path, content_hash in index["paths"].items()}
        self.assertEqual(by_path["a.docx"], by_path["b.docx"])
        self.assertNotEqual(by_path["a.docx"], by_path["other.docx"])

    def test_layout_clusters_separate_document_kinds(self):
        make_docx(self.input / "transfer.docx", *TRANSFER)
        gift = list(TRANSFER)
        gift[2] = "HỢP ĐỒNG TẶNG CHO QUYỀN SỬ DỤNG ĐẤT"
        make_docx(self.input / "gift.docx", *gift)

        index = regex_lab.ingest_corpus(self.input, self.cache)
        by_path = {path: index["records"][content_hash]["cluster_id"] for path, content_hash in index["paths"].items()}

        self.assertNotEqual(by_path["transfer.docx"], by_path["gift.docx"])

    def test_review_packet_has_at_most_three_representatives(self):
        for number in range(4):
            make_docx(self.input / f"sample-{number}.docx", *TRANSFER, f"Mẫu {number}")

        result = regex_lab.review_corpus(self.input, self.cache, self.golden, self.packets)
        packet = Path(result["packet_dir"]) / result["packets"][0]

        self.assertLessEqual(packet.read_text(encoding="utf-8").count("\n## sample-"), 3)

    def test_approve_then_verify_and_detect_changed_extraction(self):
        make_docx(self.input / "one.docx", *TRANSFER)
        regex_lab.approve_corpus(self.input, self.cache, self.golden, approve_all=True)
        unchanged = regex_lab.verify_corpus(self.input, self.cache, self.golden)
        self.assertEqual(unchanged["summary"]["UNCHANGED"], 1)
        self.assertEqual(unchanged["exit_code"], 0)

        index_path = self.cache / "index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        content_hash = next(iter(index["records"]))
        record_path = self.cache / "records" / f"{content_hash}.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["extraction"]["ten_hop_dong"] = "KẾT QUẢ REGEX ĐÃ THAY ĐỔI"
        record_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

        changed = regex_lab.verify_corpus(self.input, self.cache, self.golden)
        self.assertEqual(changed["summary"]["CHANGED"], 1)
        self.assertEqual(changed["exit_code"], 1)

    def test_extract_change_is_seen_when_cache_is_invalidated(self):
        make_docx(self.input / "one.docx", *TRANSFER)
        regex_lab.approve_corpus(self.input, self.cache, self.golden, approve_all=True)
        original = regex_lab.extract_contract.extract

        def changed_extract(*args, **kwargs):
            payload = original(*args, **kwargs)
            payload["web_form"]["ten_hop_dong"] = "CHANGED"
            return payload

        with patch.object(regex_lab, "_extractor_fingerprint", return_value="new-code"), patch.object(
            regex_lab.extract_contract, "extract", side_effect=changed_extract
        ):
            changed = regex_lab.verify_corpus(self.input, self.cache, self.golden)
        self.assertEqual(changed["summary"]["CHANGED"], 1)

    def test_verify_detects_removed_golden_sample(self):
        sample = make_docx(self.input / "one.docx", *TRANSFER)
        regex_lab.approve_corpus(self.input, self.cache, self.golden, approve_all=True)
        sample.unlink()

        result = regex_lab.verify_corpus(self.input, self.cache, self.golden)

        self.assertEqual(result["summary"]["REMOVED"], 1)
        self.assertEqual(result["exit_code"], 1)


EXTRACTION = {
    "document_kind": "transfer_contract",
    "ten_hop_dong": "HỢP ĐỒNG CHUYỂN NHƯỢNG",
    "nguoi_yeu_cau": "",
    "duong_su": "",
    "tai_san": "",
    "nguoi": [{"ho_ten": "Nguyễn Văn A", "gioi_tinh": "Ông", "ngay_sinh": "01/01/1980",
               "cccd": "0123456789", "ngay_cap_cccd": "", "dia_chi": "xã A"}],
    "nguoi_chet": [{"ho_ten": "Trần X", "ngay_sinh": "1920", "ngay_chet": "01/01/2000",
                    "so_giay_to": "TL-1", "ngay_cap": "02/01/2000", "noi_cap": "UBND", "dia_chi": "xã A"}],
    "thua_dat": [{"so_thua_dat": "10", "so_to_ban_do": "5", "dien_tich": "450",
                  "dia_chi": "xã A", "so_gcn": "Đ 123", "ngay_cap_gcn": ""}],
    "tai_san_chua_ho_tro": [],
    "missing_fields": [],
    "error": "",
}


class CompareAnswersTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.cache = self.root / "cache"
        self.answers = self.root / "answers"
        self.answers.mkdir(parents=True)
        self.hash = self._seed_cache()

    def _seed_cache(self) -> str:
        (self.cache / "records").mkdir(parents=True)
        fingerprint = regex_lab._extractor_fingerprint()
        record = {
            "content_hash": "h1", "extractor_fingerprint": fingerprint,
            "relative_path": "one.docx", "layout_signature": "sig",
            "cluster_id": "c1", "extraction": EXTRACTION,
            "flags": [], "kiem_tra": [], "source_lines": [],
        }
        (self.cache / "records" / "h1.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        index = {"extractor_fingerprint": fingerprint, "records": {"h1": record},
                 "paths": {"one.docx": "h1"}, "clusters": {}}
        (self.cache / "index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
        return "h1"

    def _write_expected(self, data) -> Path:
        path = self.answers / "h1.expected.json"
        path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def test_so_tung_truong_nguoi_nguoi_chet_va_dat(self):
        self._write_expected({
            "nguoi": [{"ho_ten": "Nguyễn Văn A", "ngay_sinh": "02/02/1980"}],
            "nguoi_chet": [{"ho_ten": "Trần X", "ngay_chet": "05/05/2001"}],
            "thua_dat": [{"so_thua_dat": "10", "dien_tich": "500"}],
        })

        report = regex_lab.compare_answers(self.answers, self.cache)

        fields = {d["field"] for d in report["diffs"]}
        self.assertIn("nguoi[0].ngay_sinh", fields)
        self.assertIn("nguoi_chet[0].ngay_chet", fields)
        self.assertIn("thua_dat[0].dien_tich", fields)
        self.assertEqual(report["exit_code"], 1)

    def test_rong_xac_nhan_bat_duoc_boc_thua(self):
        self._write_expected({"nguoi": []})

        report = regex_lab.compare_answers(self.answers, self.cache)

        self.assertIn({"file": "one.docx", "field": "nguoi.len", "expected": 0, "actual": 1}, report["diffs"])

    def test_dap_an_trang_la_loi(self):
        self._write_expected({"document_kind": None, "nguoi": None})

        report = regex_lab.compare_answers(self.answers, self.cache)

        self.assertTrue(any(d.get("actual") == "tat ca null" for d in report["diffs"]))
        self.assertEqual(report["exit_code"], 1)

    def test_thieu_thu_muc_dap_an_la_loi(self):
        report = regex_lab.compare_answers(self.root / "khong-ton-tai", self.cache)

        self.assertEqual(report["exit_code"], 1)
        self.assertEqual(report["files_checked"], 0)

    def test_json_hong_la_loi(self):
        self._write_expected("{ khong phai json")

        report = regex_lab.compare_answers(self.answers, self.cache)

        self.assertEqual(report["exit_code"], 1)
        self.assertTrue(any(d["field"] == "*" for d in report["diffs"]))

    def test_cache_cu_bi_tu_choi(self):
        index_path = self.cache / "index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index["extractor_fingerprint"] = "cu-khong-hop-le"
        index_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
        self._write_expected({"document_kind": "transfer_contract"})

        report = regex_lab.compare_answers(self.answers, self.cache)

        self.assertTrue(any(d["field"] == "cache" for d in report["diffs"]))
        self.assertEqual(report["exit_code"], 1)

    def test_dap_an_dung_khong_diff(self):
        self._write_expected({
            "document_kind": "transfer_contract",
            "nguoi": [{"ho_ten": "Nguyễn Văn A", "gioi_tinh": "Ông", "ngay_sinh": "01/01/1980"}],
            "thua_dat": [{"so_thua_dat": "10", "dien_tich": "450"}],
            "tai_san_chua_ho_tro": [],
        })

        report = regex_lab.compare_answers(self.answers, self.cache)

        self.assertEqual(report["diffs"], [])
        self.assertEqual(report["exit_code"], 0)


class ReviewSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.input = self.root / "input"
        self.cache = self.root / "cache"
        self.golden = self.root / "golden"
        self.packets = self.root / "packets"

    def test_blind_packet_khong_lo_dap_an_may(self):
        make_docx(self.input / "one.docx", *TRANSFER)
        result = regex_lab.review_corpus(self.input, self.cache, self.golden, self.packets, blind=True)
        packet_dir = Path(result["packet_dir"])

        packet_text = (packet_dir / result["packets"][0]).read_text(encoding="utf-8")
        self.assertNotIn("KIND_", packet_text)
        self.assertNotIn("Extraction", packet_text)
        expected = json.loads(next(packet_dir.glob("*.expected.json")).read_text(encoding="utf-8"))
        self.assertTrue(all(expected.get(field) is None for field in regex_lab._ANSWER_FIELDS))

    def test_review_chon_cum_co_phat_hien_kiem_tra(self):
        make_docx(self.input / "one.docx", *TRANSFER)
        regex_lab.approve_corpus(self.input, self.cache, self.golden, approve_all=True)
        index_path = self.cache / "index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        content_hash = next(iter(index["records"]))
        record_path = self.cache / "records" / f"{content_hash}.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["kiem_tra"] = [{"id": "R04", "muc": "loi", "noi_dung": "tên bẩn"}]
        record_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

        result = regex_lab.review_corpus(self.input, self.cache, self.golden, self.packets)

        self.assertEqual(result["selected_cluster_count"], 1)
        index_md = (Path(result["packet_dir"]) / "index.md").read_text(encoding="utf-8")
        self.assertIn("HAS_R_FLAGS", index_md)

    def test_cum_da_duyet_khong_loi_khong_chon(self):
        make_docx(self.input / "one.docx", *TRANSFER, "Nội dung A")
        make_docx(self.input / "two.docx", *TRANSFER, "Nội dung B")
        regex_lab.approve_corpus(self.input, self.cache, self.golden, approve_all=True)
        index = json.loads((self.cache / "index.json").read_text(encoding="utf-8"))
        for content_hash in index["records"]:
            record_path = self.cache / "records" / f"{content_hash}.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["kiem_tra"] = []  # gia lap ban kiem sach: luat chay xong, khong phat hien gi
            record["flags"] = []
            record_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

        result = regex_lab.review_corpus(self.input, self.cache, self.golden, self.packets)

        self.assertEqual(result["selected_cluster_count"], 0)

    def test_kiem_tra_loi_ghi_none_va_chon_review(self):
        make_docx(self.input / "one.docx", *TRANSFER)
        with patch.object(regex_lab.kiem_tra_trich_xuat, "kiem_tra_payload", side_effect=RuntimeError("boom")):
            index = regex_lab.ingest_corpus(self.input, self.cache)

        record = next(iter(index["records"].values()))
        self.assertIsNone(record["kiem_tra"])

        result = regex_lab.review_corpus(self.input, self.cache, self.golden, self.packets)
        self.assertEqual(result["selected_cluster_count"], 1)


if __name__ == "__main__":
    unittest.main()
