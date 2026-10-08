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


PAYLOAD = {
    "raw": {
        "document_kind": "transfer_contract",
        "ben_a": {"nguoi": [{"ho_ten": "Nguyễn Văn A", "gioi_tinh": "Ông", "ngay_sinh": "01/01/1980",
                             "cccd": "0123456789", "ngay_cap_cccd": "", "noi_cap": "CA A", "dia_chi": "xã A"}]},
        "ben_b": {"nguoi": []},
        "nguoi_chet": [{"ho_ten": "Trần X", "ngay_sinh": "1920", "ngay_chet": "01/01/2000",
                        "loai_giay_to": "Trích lục", "so_giay_to": "TL-1", "ngay_cap": "02/01/2000",
                        "noi_cap": "UBND", "dia_chi": "xã A"}],
        "danh_sach_thua_dat": [{
            "so_thua_dat": "10", "so_to_ban_do": "5", "dien_tich": "450",
            "chi_tiet_dien_tich": [{"loai_dat": "Đất ở", "dien_tich": "200"},
                                   {"loai_dat": "CLN", "dien_tich": "250"}],
            "land_rows": [{"loai_dat": "Đất ở", "dien_tich": 200.0, "thoi_han": "lâu dài"},
                          {"loai_dat": "CLN", "dien_tich": 250.0, "thoi_han": "50 năm"}],
            "muc_dich_su_dung": "Đất ở", "dia_chi": "xã A",
            "so_gcn": "Đ 123", "ngay_cap_gcn": "", "co_quan_cap": "UBND",
        }],
        "tai_san_chua_ho_tro": [],
        "missing_web_form_fields": [],
    },
    "web_form": {"ten_hop_dong": "HỢP ĐỒNG CHUYỂN NHƯỢNG", "nguoi_yeu_cau": "", "duong_su": "", "tai_san": ""},
}
# Di qua _snapshot that: test phat hien ca viec snapshot lam mat truong.
EXTRACTION = regex_lab._snapshot(PAYLOAD)


class CompareAnswersTests(unittest.TestCase):
    def test_nested_unanswered_sibling_does_not_diff_and_empty_row_does(self):
        self._write_expected({'nguoi': [{'ho_ten': 'Nguyễn Văn A', 'nested': {'f': None}}]})
        self.assertEqual(regex_lab.compare_answers(self.answers, self.cache)['exit_code'], 0)
        index_path = self.cache / 'index.json'
        index = json.loads(index_path.read_text(encoding='utf-8'))
        index['records'][self.hash]['extraction']['nguoi'].append({'ho_ten':'Người Mẫu Hai'})
        index_path.write_text(json.dumps(index), encoding='utf-8')
        self._write_expected({'nguoi': [{'ho_ten': 'Nguyễn Văn A'}, {}]})
        report = regex_lab.compare_answers(self.answers, self.cache)
        self.assertEqual(report['exit_code'], 1)
        self.assertTrue(any('chi kiem duoc so luong' in str(d['actual']) for d in report['diffs']))

    def test_compare_answers_cannot_reuse_actual_parcel_for_two_expected_rows(self):
        index_path = self.cache / 'index.json'
        index = json.loads(index_path.read_text(encoding='utf-8'))
        index['records'][self.hash]['extraction']['thua_dat'] = [{'so_thua_dat':'11'}, {'so_thua_dat':'12'}]
        index_path.write_text(json.dumps(index), encoding='utf-8')
        self._write_expected({'thua_dat': [{'so_thua_dat':'11'}, {'so_thua_dat':'11'}]})
        report = regex_lab.compare_answers(self.answers, self.cache)
        self.assertEqual(report['exit_code'], 1)
        self.assertTrue(any(d['field'] == 'thua_dat[1].so_thua_dat' and d['actual'] == '12' for d in report['diffs']))

    def test_strict_identity_booleans_and_one_to_one_rows(self):
        probes = [
            ({'ho_ten': 'Nguyễn Văn Mẫu'}, {'ho_ten': 'Nguyên Văn Mẫu'}),
            ({'cccd': '001234567890'}, {'cccd': '1234567890'}),
            ({'cccd': '9007199254740992'}, {'cccd': '9007199254740993'}),
            ({'chi_co_nam_sinh': False}, {'chi_co_nam_sinh': True}),
            ({'chi_co_nam_sinh': False}, {'chi_co_nam_sinh': 0}),
            ({'chi_co_nam_sinh': False}, {'chi_co_nam_sinh': 'False'}),
            ({'ngay_chet': '01/01/2000'}, {'ngay_chet': '02/01/2000'}),
            ([{'so_thua_dat': '11'}, {'so_thua_dat': '11'}], [{'so_thua_dat': '11'}, {'so_thua_dat': '12'}]),
        ]
        for want, got in probes:
            with self.subTest(want=want, got=got):
                self.assertFalse(regex_lab._match(want, got, 'thua_dat' if isinstance(want, list) else ''))
        self.assertTrue(regex_lab._match([{'so_thua_dat':'11'}, {'so_thua_dat':'12'}], [{'so_thua_dat':'12'}, {'so_thua_dat':'11'}], 'thua_dat'))
        ordered = [{'loai_dat':'ONT','dien_tich':10}, {'loai_dat':'CLN','dien_tich':20}]
        self.assertFalse(regex_lab._match({'land_rows':ordered}, {'land_rows':list(reversed(ordered))}))
        self.assertFalse(regex_lab._match({'chi_tiet_dien_tich':ordered}, {'chi_tiet_dien_tich':list(reversed(ordered))}))

    def test_unknown_answer_key_does_not_silently_pass(self):
        self._write_expected({'nguoi': [{'ho_ten': 'Nguyễn Văn A'}], 'thau_dat': []})
        report = regex_lab.compare_answers(self.answers, self.cache)
        self.assertEqual(report['exit_code'], 1)
        self.assertTrue(any(d['field'] == 'thau_dat' and d['actual'] == 'unknown answer key' for d in report['diffs']))

    def test_snapshot_keeps_boolean_false_and_deceased_gender(self):
        payload = {'raw': {'ben_a': {'nguoi': [{'ho_ten':'Người Mẫu','chi_co_nam_sinh':False}]},
                           'nguoi_chet': [{'ho_ten':'Người Chết Mẫu','gioi_tinh':'Ông','chi_co_nam_sinh':True}]}}
        snapshot = regex_lab._snapshot(payload)
        self.assertIs(snapshot['nguoi'][0]['chi_co_nam_sinh'], False)
        self.assertIs(snapshot['nguoi_chet'][0]['chi_co_nam_sinh'], True)
        self.assertEqual(snapshot['nguoi_chet'][0]['gioi_tinh'], 'Ông')

    def test_nested_null_is_unanswered_and_partial_scope_is_explicit(self):
        self._write_expected({'nguoi': [{'nested': {'ho_ten': None}}]})
        report = regex_lab.compare_answers(self.answers, self.cache)
        self.assertEqual(report['exit_code'], 1)
        self.assertEqual(report['checked_fields'], 0)
        self.assertEqual(report['scope'][0]['result_scope'], 'unanswered')
        self._write_expected({'nguoi': [{}]})
        self.assertEqual(regex_lab.compare_answers(self.answers, self.cache)['checked_fields'], 0)
        self._write_expected({'nguoi': [{'ho_ten': 'Nguyễn Văn A'}]})
        report = regex_lab.compare_answers(self.answers, self.cache)
        self.assertEqual(report['exit_code'], 0)
        self.assertEqual(report['checked_fields'], 1)
        self.assertGreater(report['unanswered_fields'], 0)
        self.assertEqual(report['scope'][0]['result_scope'], 'checked_fields_only')

    def test_extraction_error_never_matches_answer(self):
        index_path = self.cache / 'index.json'
        index = json.loads(index_path.read_text(encoding='utf-8'))
        index['records'][self.hash]['extraction']['error'] = 'reader failed'
        index_path.write_text(json.dumps(index), encoding='utf-8')
        self._write_expected({'nguoi': [{'ho_ten': 'Nguyễn Văn A'}]})
        report = regex_lab.compare_answers(self.answers, self.cache)
        self.assertEqual(report['exit_code'], 1)
        self.assertTrue(any(d['field'] == 'error' for d in report['diffs']))

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
            "nguoi": [{"ho_ten": "Nguyễn Văn A", "ngay_sinh": "02/02/1980", "noi_cap": "CA B"}],
            "nguoi_chet": [{"ho_ten": "Trần X", "ngay_chet": "05/05/2001"}],
            "thua_dat": [{"so_thua_dat": "10", "dien_tich": "500", "muc_dich_su_dung": "CLN"}],
        })

        report = regex_lab.compare_answers(self.answers, self.cache)

        fields = {d["field"] for d in report["diffs"]}
        self.assertIn("nguoi[0].ngay_sinh", fields)
        self.assertIn("nguoi[0].noi_cap", fields)
        self.assertIn("nguoi_chet[0].ngay_chet", fields)
        self.assertIn("thua_dat[0].dien_tich", fields)
        self.assertIn("thua_dat[0].muc_dich_su_dung", fields)
        self.assertEqual(report["exit_code"], 1)

    def test_so_ca_dong_chi_tiet_dien_tich_va_land_rows(self):
        self._write_expected({
            "thua_dat": [{
                "so_thua_dat": "10",
                "chi_tiet_dien_tich": [{"loai_dat": "Đất ở", "dien_tich": "50"},
                                       {"loai_dat": "CLN", "dien_tich": "250"}],
                "land_rows": [{"loai_dat": "Đất ở", "dien_tich": 200.0, "thoi_han": "lâu dài"}],
            }],
        })

        report = regex_lab.compare_answers(self.answers, self.cache)

        fields = {d["field"] for d in report["diffs"]}
        self.assertIn("thua_dat[0].chi_tiet_dien_tich", fields)
        self.assertIn("thua_dat[0].land_rows", fields)

    def test_dap_an_con_trong_ban_ghi_long_khong_false_diff(self):
        # null/thieu key ben trong dong long = khong tra loi, khong phai sai.
        self._write_expected({
            "thua_dat": [{"so_thua_dat": "10",
                          "chi_tiet_dien_tich": [{"loai_dat": "Đất ở"}, {"loai_dat": "CLN"}]}],
        })

        report = regex_lab.compare_answers(self.answers, self.cache)

        self.assertEqual(report["diffs"], [])

    def test_so_json_khop_chuoi_engine(self):
        self._write_expected({"thua_dat": [{"so_thua_dat": "10", "dien_tich": 450}]})

        report = regex_lab.compare_answers(self.answers, self.cache)

        self.assertEqual(report["diffs"], [])

    def test_ban_ghi_dap_an_rong_khong_tinh_la_da_tra_loi(self):
        self._write_expected({"nguoi": [{"ho_ten": None}]})

        report = regex_lab.compare_answers(self.answers, self.cache)

        self.assertTrue(any("chi kiem duoc so luong" in str(d.get("actual")) for d in report["diffs"]))
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

    def test_sua_rieng_validator_lam_cache_het_han(self):
        # Doi NOI DUNG file validator -> fingerprint doi -> compare tu choi cache.
        tam = self.root / "validator-moi.py"
        tam.write_text(Path(regex_lab.kiem_tra_trich_xuat.__file__).read_text(encoding="utf-8") + "\n# sua luat\n", encoding="utf-8")
        self._write_expected({"document_kind": "transfer_contract"})

        with patch.object(regex_lab.kiem_tra_trich_xuat, "__file__", str(tam)):
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
        make_docx(self.input / "one.docx", *TRANSFER, "Nội dung A")
        make_docx(self.input / "two.docx", *TRANSFER, "Nội dung B")
        with patch.object(regex_lab.kiem_tra_trich_xuat, "kiem_tra_payload", side_effect=RuntimeError("boom")):
            index = regex_lab.ingest_corpus(self.input, self.cache)

        for record in index["records"].values():
            self.assertIsNone(record["kiem_tra"])
        # Duyet golden + xoa flags: chi con KIEM_TRA_ERROR la ly do chon duy nhat.
        regex_lab.approve_corpus(self.input, self.cache, self.golden, approve_all=True)
        for content_hash in index["records"]:
            record_path = self.cache / "records" / f"{content_hash}.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["flags"] = []
            record_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

        result = regex_lab.review_corpus(self.input, self.cache, self.golden, self.packets)

        self.assertEqual(result["selected_cluster_count"], 1)
        index_md = (Path(result["packet_dir"]) / "index.md").read_text(encoding="utf-8")
        self.assertIn("KIEM_TRA_ERROR", index_md)
        self.assertNotIn("HAS_R_FLAGS", index_md)

    def test_file_gay_finding_phat_nam_trong_goi(self):
        # Cum a, b, c, z — chi z co finding: z phai nam trong 3 mau dai dien.
        for name in ("a", "b", "c", "z"):
            make_docx(self.input / f"{name}.docx", *TRANSFER, f"Nội dung {name}")
        regex_lab.approve_corpus(self.input, self.cache, self.golden, approve_all=True)
        index = json.loads((self.cache / "index.json").read_text(encoding="utf-8"))
        hash_z = index["paths"]["z.docx"]
        for content_hash in index["records"]:
            record_path = self.cache / "records" / f"{content_hash}.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["flags"] = []
            record["kiem_tra"] = [{"id": "R04", "muc": "loi", "noi_dung": "tên bẩn"}] if content_hash == hash_z else []
            record_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

        result = regex_lab.review_corpus(self.input, self.cache, self.golden, self.packets, blind=True)

        self.assertTrue((Path(result["packet_dir"]) / f"{hash_z}.source.txt").exists())


if __name__ == "__main__":
    unittest.main()
