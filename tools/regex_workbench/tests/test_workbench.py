"""Test suite cho regex_workbench — fixtures la du lieu gia lap, khong PII that."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import unicodedata
import unittest
from pathlib import Path

from engine import lint_profile, load_profile, run

FIXTURES = Path(__file__).resolve().parent / "fixtures"
PROBE = Path(__file__).resolve().parent / "_timeout_probe.py"
PROBE_LIMIT_S = 45  # giới hạn ngoài tiến trình: engine hỏng => FAIL, không treo suite


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def fields_by_name(result: dict, name: str) -> list[dict]:
    return [f for f in result["fields"] if f["name"] == name]


def all_persons(result: dict) -> list[dict]:
    return [p for b in result["parties"]["blocks"] for p in b["persons"]]


class TransferProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile("transfer")

    def test_profile_lint_clean(self):
        self.assertEqual(lint_profile(self.profile), [])

    def test_custom_land_rule_shapes_rejected_before_lint(self):
        from engine.runner import validate_profile
        for malformed in (None, 7, 'rule', [], {'name': 'dien_tich', 'pattern': 5},
                          {'name': 'dien_tich', 'rule_id': 'x', 'pattern': 'x', 'group': []}):
            profile = copy.deepcopy(self.profile)
            profile['asset_groups']['land_rows']['fields'] = [malformed]
            self.assertTrue(validate_profile(profile))
            self.assertTrue(lint_profile(profile))

    def test_standard_transfer_zones_and_kind(self):
        text = load_fixture("transfer_chuan.txt")
        result = run(text, self.profile)

        self.assertEqual(result["doc_kind"], "transfer")
        self.assertEqual(result["title"]["state"], "matched")
        self.assertIn("CHUYỂN NHƯỢNG", result["title"]["value"])

        zones = {z["name"]: z for z in result["zones"]}
        for zone_id in ("header", "parties", "asset", "clauses", "notary"):
            self.assertIn(zone_id, zones)
            self.assertEqual(zones[zone_id]["state"], "matched", zone_id)
            self.assertIsNotNone(zones[zone_id]["span"], zone_id)

        # Zone ordering: header < parties < asset < clauses < notary
        starts = [zones[zid]["span"][0] for zid in ("header", "parties", "asset", "clauses", "notary")]
        self.assertEqual(starts, sorted(starts))

    def test_provenance_every_field_has_span_snippet_rule(self):
        text = load_fixture("transfer_chuan.txt")
        result = run(text, self.profile)

        for field in result["fields"]:
            self.assertIn(field["state"], ("matched", "ambiguous", "warning_nonstandard", "missing", "error"))
            if field["state"] in ("matched", "warning_nonstandard"):
                start, end = field["span"]
                self.assertEqual(text[start:end], field["raw_snippet"])
                self.assertTrue(field["rule_id"])

        for zone in result["zones"]:
            if zone["state"] == "matched":
                start, end = zone["span"]
                self.assertEqual(text[start:end], zone["raw_snippet"])
                self.assertTrue(zone["rule_id"])

        for person in all_persons(result):
            start, end = person["span"]
            self.assertEqual(text[start:end], person["raw_snippet"])
            self.assertTrue(person["rule_id"])

    def test_standard_fields_extracted(self):
        text = load_fixture("transfer_chuan.txt")
        result = run(text, self.profile)

        serial = fields_by_name(result, "so_serial")[0]
        self.assertEqual(serial["state"], "matched")
        self.assertEqual(serial["value"], "AB 123456")

        self.assertEqual(fields_by_name(result, "thua_dat")[0]["value"], "215")
        self.assertEqual(fields_by_name(result, "to_ban_do")[0]["value"], "34")
        self.assertEqual(fields_by_name(result, "dien_tich_m2")[0]["value"], "68,5")
        self.assertEqual(fields_by_name(result, "ngay_cong_chung")[0]["value"], "15/06/2026")
        self.assertEqual(fields_by_name(result, "cong_chung_vien")[0]["value"], "Phạm Minh Chi")
        self.assertEqual(fields_by_name(result, "so_cong_chung")[0]["value"], "428/2026/CCGD")

    def test_dong_su_dung_person_not_dropped(self):
        """Bug baseline: nguoi sau nhan 'Dong su dung' tung bi bo sot."""
        text = load_fixture("transfer_dong_su_dung.txt")
        result = run(text, self.profile)

        persons = all_persons(result)
        names = [p["fields"]["ho_ten"]["value"] for p in persons]
        self.assertIn("Lê Thị Cẩm", names)
        self.assertEqual(len(persons), 3)

        co_user = next(p for p in persons if p["fields"]["ho_ten"]["value"] == "Lê Thị Cẩm")
        self.assertEqual(co_user["role"], "Đồng sử dụng")
        self.assertEqual(co_user["side"], "A")
        self.assertEqual(co_user["fields"]["cccd"]["value"], "001178000003")

    def test_dong_su_dung_inline_label_keeps_person(self):
        """Review f48a762: 'Dong su dung: Ba: ...' tren CUNG DONG con 2/3 nguoi."""
        text = load_fixture("transfer_dong_su_dung.txt").replace(
            "Đồng sử dụng:\nBà:", "Đồng sử dụng: Bà:"
        )
        result = run(text, self.profile)

        persons = all_persons(result)
        self.assertEqual(len(persons), 3)
        cam = next(
            p for p in persons
            if p["fields"]["ho_ten"]["value"] == "Lê Thị Cẩm"
        )
        self.assertEqual(cam["role"], "Đồng sử dụng")
        self.assertEqual(cam["fields"]["cccd"]["value"], "001178000003")

    def test_person_without_honorific_not_dropped(self):
        """Review f48a762: bo danh xung 'Ba:' sau nhan cung bo sot nguoi.

        Nguoi khong danh xung van duoc tach khi dong ten co bang chung
        (sinh + ngay); gioi_tinh la missing (khong bia).
        """
        text = load_fixture("transfer_dong_su_dung.txt").replace(
            "Đồng sử dụng:\nBà:", "Đồng sử dụng:\n"
        )
        result = run(text, self.profile)

        persons = all_persons(result)
        self.assertEqual(len(persons), 3)
        cam = next(
            p for p in persons
            if p["fields"]["ho_ten"]["value"] == "Lê Thị Cẩm"
        )
        self.assertEqual(cam["role"], "Đồng sử dụng")
        self.assertEqual(cam["fields"]["gioi_tinh"]["state"], "missing")
        self.assertEqual(cam["fields"]["ngay_sinh"]["value"], "03/03/1978")
        self.assertEqual(cam["fields"]["cccd"]["value"], "001178000003")
        # span/raw_snippet cua nguoi van tro dung input goc
        s, e = cam["span"]
        self.assertEqual(text[s:e], cam["raw_snippet"])

    def test_two_cccd_one_person_is_ambiguous(self):
        """Review f48a762: hai CCCD khac nhau trong mot nguoi phai ambiguous."""
        text = load_fixture("transfer_dong_su_dung.txt").replace(
            "Căn cước công dân số: 001075000001",
            "CCCD: 001075000001; CCCD: 001075000009",
        )
        result = run(text, self.profile)

        an = next(
            p for p in all_persons(result)
            if p["fields"]["ho_ten"]["value"] == "Nguyễn Văn An"
        )
        cccd = an["fields"]["cccd"]
        self.assertEqual(cccd["state"], "ambiguous")
        self.assertEqual(len(cccd["candidates"]), 2)
        self.assertEqual(
            {c["value"] for c in cccd["candidates"]},
            {"001075000001", "001075000009"},
        )
        # So CCCD thu hai khong bi tach thanh nguoi ao
        self.assertEqual(len(all_persons(result)), 3)

    def test_bad_kind_rule_reports_error(self):
        """Review f48a762: kind_rule sai regex phai tra error, khong matched ngam."""
        profile = copy.deepcopy(self.profile)
        profile["title"]["kind_rules"][0]["pattern"] = "("  # kind.correction
        result = run(load_fixture("transfer_chuan.txt"), profile)

        self.assertEqual(result["title"]["state"], "error")
        # Rule uu tien cao hon khong danh gia duoc -> kind khong dang tin
        self.assertEqual(result["doc_kind"], "unknown")
        self.assertTrue(
            any("kind.correction" in e for e in result["errors"]),
            result["errors"],
        )

    def test_bad_zone_marker_regex_reports_error(self):
        """Zone marker sai regex -> zone state error + errors kem rule_id."""
        profile = copy.deepcopy(self.profile)
        for zone in profile["zones"]:
            if zone["zone_id"] == "parties":
                zone["start_markers"] = ["("]
        result = run(load_fixture("transfer_chuan.txt"), profile)

        zones = {z["name"]: z for z in result["zones"]}
        self.assertEqual(zones["parties"]["state"], "error")
        self.assertTrue(
            any("zone.parties" in e for e in result["errors"]),
            result["errors"],
        )

    def test_bad_side_marker_regex_parties_error(self):
        """side_markers sai regex -> parties error, khong im lang."""
        profile = copy.deepcopy(self.profile)
        profile["parties"]["side_markers"][0]["pattern"] = "("
        result = run(load_fixture("transfer_chuan.txt"), profile)

        self.assertEqual(result["parties"]["state"], "error")
        self.assertTrue(
            any("party.side" in e for e in result["errors"]),
            result["errors"],
        )

    def test_bad_validator_regex_errors_field(self):
        """Review: validator sai regex -> field error + errors[], khong matched."""
        profile = copy.deepcopy(self.profile)
        for rule in profile["fields"]:
            if rule["name"] == "so_serial":
                rule["validators"] = [
                    {"pattern": "([A-Z]{2}", "on_fail": "warning_nonstandard"}
                ]
        result = run(load_fixture("transfer_chuan.txt"), profile)

        field = fields_by_name(result, "so_serial")[0]
        self.assertEqual(field["state"], "error")
        self.assertTrue(
            any("so_serial" in e and "validator" in e for e in result["errors"]),
            result["errors"],
        )

    def test_sinh_nam_not_mixed_into_name(self):
        """Bug baseline: 'sinh nam 1960' tung bi gom vao ho_ten."""
        text = load_fixture("transfer_sinh_nam.txt")
        result = run(text, self.profile)

        persons = all_persons(result)
        self.assertEqual(len(persons), 3)
        an = next(p for p in persons if p["fields"]["cccd"]["value"] == "001060000001")
        self.assertEqual(an["fields"]["ho_ten"]["value"], "Nguyễn Văn An")
        self.assertNotIn("sinh", an["fields"]["ho_ten"]["value"].lower())
        self.assertEqual(an["fields"]["ngay_sinh"]["value"], "1960")

    def test_dinh_chinh_not_classified_as_transfer(self):
        """Bug baseline: trang Dinh chinh tung bi coi la hop dong chinh."""
        text = load_fixture("dinh_chinh.txt")
        result = run(text, self.profile)

        self.assertEqual(result["doc_kind"], "correction")
        self.assertEqual(result["title"]["rule_id"], "kind.correction")

    def test_serial_one_letter_warns_keeps_raw(self):
        """Bug baseline: serial mot chu cai can giu raw + canh bao chua dung chuan."""
        text = load_fixture("transfer_serial_mot_chu.txt")
        result = run(text, self.profile)

        serial = fields_by_name(result, "so_serial")[0]
        self.assertEqual(serial["state"], "warning_nonstandard")
        self.assertEqual(serial["value"], "M 012345")
        self.assertEqual(serial["raw_snippet"], "M 012345")
        self.assertTrue(serial["warnings"])

    def test_missing_fields_are_honest(self):
        text = load_fixture("transfer_thieu_truong.txt")
        result = run(text, self.profile)

        self.assertEqual(fields_by_name(result, "so_serial")[0]["state"], "missing")
        self.assertIsNone(fields_by_name(result, "so_serial")[0]["value"])

        persons = all_persons(result)
        binh = next(p for p in persons if p["fields"]["ho_ten"]["value"] == "Trần Thị Bình")
        self.assertEqual(binh["fields"]["cccd"]["state"], "missing")

    def test_serial_raw_verbatim_and_labeled_parcel_address(self):
        """Bug #7: serial TEST-001 va nhan 'Dia chi thua dat' phai vao field + span nguon."""
        text = load_fixture("transfer_serial_va_dia_chi_thua.txt")
        result = run(text, self.profile)

        serial = fields_by_name(result, "so_serial")[0]
        self.assertEqual(serial["state"], "warning_nonstandard")
        self.assertEqual(serial["value"], "TEST-001")
        self.assertEqual(serial["raw_snippet"], "TEST-001")
        s, e = serial["span"]
        self.assertEqual(text[s:e], "TEST-001")
        self.assertTrue(serial["warnings"])

        dia_chi = fields_by_name(result, "dia_chi_thua")[0]
        self.assertEqual(dia_chi["state"], "matched")
        self.assertEqual(dia_chi["value"], "xã Mẫu, tỉnh Mẫu")
        s, e = dia_chi["span"]
        self.assertEqual(text[s:e], dia_chi["raw_snippet"])

        zone = next(z for z in result["zones"] if z["name"] == "asset")
        self.assertLessEqual(zone["span"][0], s)
        self.assertLessEqual(e, zone["span"][1])

    def test_serial_raw_formats_keep_source_value(self):
        """Serial nguon bat ky: giu nguyen chuoi ke ca tien to '-', khong cat theo quota hay chuoi con 'do'."""
        text = load_fixture("transfer_serial_va_dia_chi_thua.txt")
        cases = {
            "TEST-001": "warning_nonstandard",
            "123456789": "warning_nonstandard",
            "-TEST-001": "warning_nonstandard",
            "/TEST-001": "warning_nonstandard",
            "TEST/001-A": "warning_nonstandard",
            "SERIES-123456": "warning_nonstandard",
            "ENDDO123": "warning_nonstandard",
            "SERIALONLY": "warning_nonstandard",
            "ABC/RAW": "warning_nonstandard",
            "DO 123456": "matched",  # hai chu + 6 so: dung chuan hien hanh, van giu raw
            "AB 123456": "matched",
        }
        for raw, state in cases.items():
            with self.subTest(raw=raw):
                case_text = text.replace("TEST-001", raw)
                result = run(case_text, self.profile)
                serial = fields_by_name(result, "so_serial")[0]
                self.assertEqual(serial["value"], raw)
                self.assertEqual(serial["raw_snippet"], raw)
                s, e = serial["span"]
                self.assertEqual(case_text[s:e], raw)
                self.assertEqual(serial["state"], state)

    def test_serial_raw_stops_before_do_issuer_and_line_end(self):
        """Bien ' do <co quan> cap' va cuoi dong: khong nuot phan sau serial."""
        text = load_fixture("transfer_chuan.txt").replace("AB 123456", "TEST-001")
        serial = fields_by_name(run(text, self.profile), "so_serial")[0]
        self.assertEqual(serial["value"], "TEST-001")
        self.assertNotIn(" do ", serial["raw_snippet"])

        eol_text = load_fixture("transfer_serial_va_dia_chi_thua.txt").replace(
            "Giấy chứng nhận số: TEST-001; Thửa đất số: 12",
            "Giấy chứng nhận số: TEST-001\nThửa đất số: 12",
        )
        serial_eol = fields_by_name(run(eol_text, self.profile), "so_serial")[0]
        self.assertEqual(serial_eol["value"], "TEST-001")

    def test_serial_parenthetical_annotation_only_on_phat_hanh_label(self):
        """Annotation '(serial)' chi thuoc nhan 'So phat hanh'; sau nhan khac la raw value."""
        text = load_fixture("transfer_serial_va_dia_chi_thua.txt")
        annotated = text.replace("Giấy chứng nhận số:", "Số phát hành (serial):")
        serial = fields_by_name(run(annotated, self.profile), "so_serial")[0]
        self.assertEqual(serial["state"], "warning_nonstandard")
        self.assertEqual(serial["value"], "TEST-001")

        prefixed = text.replace(
            "Giấy chứng nhận số: TEST-001;", "Giấy chứng nhận số: (serial) TEST-001;"
        )
        serial2 = fields_by_name(run(prefixed, self.profile), "so_serial")[0]
        self.assertEqual(serial2["state"], "warning_nonstandard")
        self.assertEqual(serial2["value"], "(serial) TEST-001")
        self.assertEqual(serial2["raw_snippet"], "(serial) TEST-001")
        s, e = serial2["span"]
        self.assertEqual(prefixed[s:e], "(serial) TEST-001")

    def test_serial_blank_stays_missing_without_borrowing_next_field(self):
        """Nhan serial trong (ke ca truoc ';' hay dong moi) -> missing, khong muon field ke."""
        text = load_fixture("transfer_serial_va_dia_chi_thua.txt")
        blanks = (
            "Giấy chứng nhận số:\n",
            "Giấy chứng nhận số: ; ",
            "Giấy chứng nhận số: \n",
            "Giấy chứng nhận số: Thửa đất số 12; ",
        )
        for blank in blanks:
            with self.subTest(blank=blank.replace("\n", "\\n")):
                result = run(
                    text.replace("Giấy chứng nhận số: TEST-001; ", blank), self.profile
                )
                serial = fields_by_name(result, "so_serial")[0]
                self.assertEqual(serial["state"], "missing")
                self.assertIsNone(serial["value"])

    def test_dia_chi_thua_blank_stays_missing_without_borrowing_next_field(self):
        """Nhan dia chi trong (dong moi/';'/nhan ke cung dong) -> missing, khong muon 'Loai dat'."""
        text = load_fixture("transfer_serial_va_dia_chi_thua.txt")
        cases = {
            "newline": text.replace("Địa chỉ thửa đất: xã Mẫu, tỉnh Mẫu;", "Địa chỉ thửa đất:\n"),
            "semicolon": text.replace("Địa chỉ thửa đất: xã Mẫu, tỉnh Mẫu;", "Địa chỉ thửa đất: ; "),
            "same-line label": text.replace(
                "Địa chỉ thửa đất: xã Mẫu, tỉnh Mẫu;\n\n", "Địa chỉ thửa đất: "
            ),
        }
        for name, case_text in cases.items():
            with self.subTest(name=name):
                dia_chi = fields_by_name(run(case_text, self.profile), "dia_chi_thua")[0]
                self.assertEqual(dia_chi["state"], "missing")
                self.assertIsNone(dia_chi["value"])
                self.assertIsNone(dia_chi["span"])

    def test_dia_chi_thua_label_only_reported_variant(self):
        """Chi nhan 'Dia chi thua dat' duoc them; 'Dia chi:' tran khong khop; nhanh cu giu nguyen."""
        text = load_fixture("transfer_serial_va_dia_chi_thua.txt")
        result = run(text.replace("Địa chỉ thửa đất:", "Địa chỉ:"), self.profile)
        self.assertEqual(fields_by_name(result, "dia_chi_thua")[0]["state"], "missing")

        old = fields_by_name(run(load_fixture("transfer_chuan.txt"), self.profile), "dia_chi_thua")[0]
        self.assertEqual(old["state"], "matched")
        self.assertTrue(old["value"].startswith("số 12 đường Láng"))

    def test_ambiguous_when_multiple_matches(self):
        text = load_fixture("transfer_chuan.txt")
        # Hai so cong chung kha di -> phai ambiguous, khong tu chon.
        text = text + chr(10) + "Số công chứng 999/2026/CCGD" + chr(10)
        result = run(text, self.profile)

        field = fields_by_name(result, "so_cong_chung")[0]
        self.assertEqual(field["state"], "ambiguous")
        self.assertEqual(len(field["candidates"]), 2)

    def test_invalid_regex_reports_error_state(self):
        profile = copy.deepcopy(self.profile)
        for rule in profile["fields"]:
            if rule["name"] == "so_serial":
                rule["pattern"] = "([a-z]{1,2}\\d{4,8}"  # thieu dong ngoac
        result = run(load_fixture("transfer_chuan.txt"), profile)

        field = fields_by_name(result, "so_serial")[0]
        self.assertEqual(field["state"], "error")
        self.assertTrue(result["errors"])

    def test_lint_flags_nested_quantifier(self):
        profile = copy.deepcopy(self.profile)
        profile["fields"].append(
            {
                "rule_id": "test.redos",
                "name": "redos_demo",
                "zone": "any",
                "pattern": "(a+)+$",
            }
        )
        problems = lint_profile(profile)
        self.assertTrue(any("nested quantifier" in p for p in problems))

    def test_validate_profile_shape(self):
        """Profile JSON hop le nhung sai kieu -> validate_profile bao ro."""
        from engine import validate_profile

        self.assertEqual(validate_profile(self.profile), [])
        self.assertTrue(validate_profile(None))
        self.assertTrue(validate_profile("transfer"))
        self.assertTrue(validate_profile({"fields": "x"}))
        self.assertTrue(any("fields" in p for p in validate_profile({"fields": "abc"})))
        self.assertTrue(validate_profile({"zones": "abc"}))
        self.assertTrue(validate_profile({"title": []}))
        self.assertTrue(validate_profile({"parties": {"side_markers": "x"}}))
        self.assertTrue(validate_profile({"regex_timeout_ms": "nhanh"}))
        # fields: null (key ton tai, gia tri null) khong con crash engine
        result = run("HỢP ĐỒNG CHUYỂN NHƯỢNG\n", {"fields": None})
        self.assertIn("doc_kind", result)

    def test_edited_rule_takes_effect_on_rerun(self):
        """Dev sua regex trong profile dict -> run() lai dung rule moi."""
        profile = copy.deepcopy(self.profile)
        for rule in profile["fields"]:
            if rule["name"] == "thua_dat":
                rule["pattern"] = "thua\\s*(?:dat|so)\\b[^0-9\\n]{0,24}(9\\d{1,5})"
        result = run(load_fixture("transfer_chuan.txt"), profile)
        # Rule moi chi chap nhan so bat dau bang 9 -> 215 khong khop -> missing
        self.assertEqual(fields_by_name(result, "thua_dat")[0]["state"], "missing")

    def test_profile_roundtrip_via_json(self):
        """Export/import: profile serialize -> load lai -> ket qua giong het."""
        profile_json = json.dumps(self.profile, ensure_ascii=False)
        reloaded = json.loads(profile_json)
        text = load_fixture("transfer_chuan.txt")
        self.assertEqual(run(text, self.profile), run(text, reloaded))


class TimeoutInterruptTests(unittest.TestCase):
    """Chứng minh regex quá hạn bị NGẮT THẬT trong engine `regex`.

    Mọi case chạy qua _timeout_probe.py trong process con có subprocess
    timeout cứng: nếu cơ chế interrupt hỏng, test FAIL sau PROBE_LIMIT_S
    thay vì treo suite vĩnh viễn.
    """

    @staticmethod
    def _probe(mode: str, *args) -> dict:
        try:
            proc = subprocess.run(
                [sys.executable, "-X", "utf8", str(PROBE), mode, *map(str, args)],
                capture_output=True,
                text=True,
                timeout=PROBE_LIMIT_S,
            )
        except subprocess.TimeoutExpired:
            raise AssertionError(
                f"probe '{mode}' quá {PROBE_LIMIT_S}s — engine không ngắt được regex"
            )
        if proc.returncode != 0:
            raise AssertionError(f"probe '{mode}' crash:\n{proc.stderr[-2000:]}")
        return json.loads(proc.stdout)

    def test_redos_field_interrupted_and_recovers(self):
        """`(a|a)*b` lọt lint tĩnh nhưng timeout engine vẫn ngắt được."""
        out = self._probe("field_redos", FIXTURES / "transfer_chuan.txt")
        first = out["first"]

        field = next(f for f in first["fields"] if f["rule_id"] == "test.redos_field")
        self.assertEqual(field["state"], "error")
        self.assertIn("timeout", field["note"])
        self.assertTrue(
            any("test.redos_field" in e and "timeout" in e for e in first["errors"]),
            first["errors"],
        )
        # Các field khác vẫn trích bình thường trong cùng lượt
        serial = next(f for f in first["fields"] if f["name"] == "so_serial")
        self.assertEqual(serial["state"], "matched")

        # Lần chạy hợp lệ tiếp theo trong cùng process vẫn thành công
        self.assertEqual(out["second"]["doc_kind"], "transfer")
        self.assertEqual(out["second"]["errors"], [])

    def test_redos_party_marker_propagates_error(self):
        """extractor.py:257 cũ nuốt lỗi timeout của trích người — giờ phải error."""
        out = self._probe("party_redos")
        first = out["first"]

        self.assertEqual(first["parties"]["state"], "error")
        self.assertIn("test.redos_party", first["parties"]["note"])
        self.assertTrue(
            any("test.redos_party" in e and "timeout" in e for e in first["errors"]),
            first["errors"],
        )
        # Recovery
        self.assertEqual(out["second"]["parties"]["state"], "matched")

    def test_redos_zone_marker_reports_error(self):
        """Zone có marker quá hạn báo error + errors[] kèm rule_id, không im lặng."""
        out = self._probe("zone_redos")
        first = out["first"]

        zones = {z["name"]: z for z in first["zones"]}
        self.assertEqual(zones["parties"]["state"], "error")
        self.assertTrue(
            any("zone.parties" in e and "timeout" in e for e in first["errors"]),
            first["errors"],
        )
        # Recovery
        second_zones = {z["name"]: z for z in out["second"]["zones"]}
        self.assertEqual(second_zones["parties"]["state"], "matched")


class SpanUnicodeFidelityTests(unittest.TestCase):
    """Span phải trỏ đúng đoạn nguồn trên input gốc: NFD, CRLF, ngoài BMP."""

    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile("transfer")

    def test_nfd_input_spans_slice_source_exactly(self):
        nfc_text = load_fixture("transfer_chuan.txt")
        nfd_text = unicodedata.normalize("NFD", nfc_text)
        self.assertNotEqual(nfd_text, nfc_text)  # fixture thật sự có dấu
        result = run(nfd_text, self.profile)

        for field in result["fields"]:
            if field["state"] in ("matched", "warning_nonstandard"):
                s, e = field["span"]
                self.assertEqual(nfd_text[s:e], field["raw_snippet"], field["rule_id"])

        serial = next(f for f in result["fields"] if f["name"] == "so_serial")
        self.assertEqual(serial["value"], "AB 123456")

        persons = all_persons(result)
        names_nfc = {
            unicodedata.normalize("NFC", p["fields"]["ho_ten"]["value"]) for p in persons
        }
        self.assertIn("Nguyễn Văn An", names_nfc)

    def test_crlf_input_spans_slice_source_exactly(self):
        text = load_fixture("transfer_chuan.txt").replace("\n", "\r\n")
        result = run(text, self.profile)

        serial = next(f for f in result["fields"] if f["name"] == "so_serial")
        s, e = serial["span"]
        self.assertEqual(text[s:e], "AB 123456")
        self.assertEqual(serial["raw_snippet"], "AB 123456")

        for zone in result["zones"]:
            if zone["state"] == "matched":
                s, e = zone["span"]
                self.assertEqual(text[s:e], zone["raw_snippet"], zone["rule_id"])

    def test_non_bmp_chars_do_not_shift_spans(self):
        """Ký tự ngoài BMP (1 code point Python / 2 UTF-16 unit JS) trước field."""
        text = "📜📜\n" + load_fixture("transfer_chuan.txt") + "\n📌"
        result = run(text, self.profile)

        serial = next(f for f in result["fields"] if f["name"] == "so_serial")
        s, e = serial["span"]
        self.assertEqual(text[s:e], "AB 123456")
        self.assertEqual(serial["raw_snippet"], "AB 123456")
        # span vẫn là code-point index của input gốc (emoji = 1)
        self.assertTrue(s > 3)

        # JSON roundtrip giữ nguyên span cho consumer (UI dùng code point)
        rt = json.loads(json.dumps(result, ensure_ascii=False))
        rt_serial = next(f for f in rt["fields"] if f["name"] == "so_serial")
        self.assertEqual(rt_serial["span"], [s, e])
        self.assertEqual(rt_serial["raw_snippet"], "AB 123456")


if __name__ == "__main__":
    unittest.main()
