"""Test suite cho regex_workbench — fixtures la du lieu gia lap, khong PII that."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from engine import lint_profile, load_profile, run

FIXTURES = Path(__file__).resolve().parent / "fixtures"


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
        normalized = text.replace("\r\n", "\n")

        for field in result["fields"]:
            self.assertIn(field["state"], ("matched", "ambiguous", "warning_nonstandard", "missing", "error"))
            if field["state"] in ("matched", "warning_nonstandard"):
                start, end = field["span"]
                self.assertEqual(normalized[start:end], field["raw_snippet"])
                self.assertTrue(field["rule_id"])

        for zone in result["zones"]:
            if zone["state"] == "matched":
                start, end = zone["span"]
                self.assertEqual(normalized[start:end], zone["raw_snippet"])
                self.assertTrue(zone["rule_id"])

        for person in all_persons(result):
            start, end = person["span"]
            self.assertEqual(normalized[start:end], person["raw_snippet"])
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


if __name__ == "__main__":
    unittest.main()
