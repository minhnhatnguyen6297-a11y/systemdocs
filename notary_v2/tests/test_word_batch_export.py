"""Tests cho services.word_batch_export — batch Word export theo
contract notary.case-drafting.v1 §8 (MIN-110).

Case duck-typed như test_word_engine (SimpleNamespace + case_state_json
theo persisted workspace shape). Chạy từ repo root notary_v2.
"""
from __future__ import annotations

import dataclasses
import json
import re
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from docx import Document

from services import word_batch_export as wbe


BUILTIN_TEMPLATE = Path("word_templates/1. PCDS .docx")


# ---------------------------------------------------------------- fixtures


def _person(cid, name, *, gender="Nam", born=None, dead=None, doc_no="",
            issued=None, address=""):
    return SimpleNamespace(
        id=cid, ho_ten=name, gioi_tinh=gender, ngay_sinh=born,
        ngay_chet=dead, so_giay_to=doc_no, ngay_cap=issued,
        dia_chi=address, loai_giay_to="CCCD", noi_cap="CA",
        loai_dia_chi="",
    )


def _participant(person, role, *, receive=True):
    return SimpleNamespace(
        customer=person, customer_id=person.id, vai_tro=role,
        co_nhan_tai_san=receive, ty_le=0.0, hang_thua_ke=1,
        parent_customer_id=None,
    )


def _prop(**kwargs):
    defaults = dict(
        so_serial="BM 1451111", so_vao_so="CS123", so_thua_dat="45",
        so_to_ban_do="12", dia_chi="Thửa đất tại xã Minh Tân",
        loai_dat="Đất ở", dien_tich=120.5,
        loai_so="Giấy chứng nhận quyền sử dụng đất",
        land_rows_json='[{"loai_dat":"ONT","dien_tich":"80","thoi_han":"Lâu dài"}]',
        hinh_thuc_su_dung="Sử dụng riêng", thoi_han="Lâu dài",
        nguon_goc="Nhà nước công nhận", ngay_cap=date(2020, 7, 8),
        co_quan_cap="UBND huyện Ý Yên",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _node(person_id, *, role="Khac", will_receive=False, is_land_owner=False,
          hidden=False, deleted=False):
    return {
        "id": f"node_{person_id}", "personId": str(person_id),
        "role": role, "isLandOwner": is_land_owner,
        "willReceive": will_receive,
        "hidden": hidden, "deleted": deleted,
    }


def _case_state(*people, nodes=None):
    """Persisted workspace shape: stage list + engineInput projection (V2)."""
    stage = []
    for p in people:
        stage.append({
            "id": str(p.id), "ho_ten": p.ho_ten, "gioi_tinh": p.gioi_tinh,
            "ngay_sinh": p.ngay_sinh.isoformat() if p.ngay_sinh else None,
            "ngay_chet": p.ngay_chet.isoformat() if p.ngay_chet else None,
            "so_giay_to": p.so_giay_to,
            "ngay_cap": p.ngay_cap.isoformat() if p.ngay_cap else None,
            "noi_cap": p.noi_cap, "dia_chi": p.dia_chi,
            "loai_dia_chi": p.loai_dia_chi,
        })
    payload = {"schemaVersion": 2, "stage": stage, "assets": [],
               "diagram": {}}
    if nodes is not None:
        payload["diagram"] = {
            "engineInput": {"version": 2, "nodes": nodes},
            "engineResult": {"allocations": {}},
        }
    return json.dumps(payload, ensure_ascii=False)


def _make_case(owner, *, participants=None, properties=None,
               case_state=None, cid=99):
    """properties=None → không tài sản (empty); [] cũng vậy."""
    props = properties or []
    return SimpleNamespace(
        id=cid,
        nguoi_chet=owner,
        tai_san=props[0] if props else None,
        property_links=[
            SimpleNamespace(property=p, is_primary=(i == 0), id=i + 1)
            for i, p in enumerate(props)
        ],
        ngay_lap_ho_so=date(2026, 7, 3),
        loai_van_ban="khai_nhan",
        noi_niem_yet="UBND xã Minh Tân",
        ghi_chu="",
        participants=participants or [],
        case_state_json=case_state,
    )


def _ready_case(cid=99):
    owner = _person(1, "Nguyễn Văn Chủ", dead=date(2024, 2, 3),
                    doc_no="001")
    heir = _person(2, "Nguyễn Văn Con", doc_no="002")
    return _make_case(
        owner, properties=[_prop()], cid=cid,
        case_state=_case_state(
            owner, heir,
            nodes=[
                _node(1, role="Owner", is_land_owner=True),
                _node(2, role="Con", will_receive=True),
            ]))


def _resolve_builtin(_key):
    return BUILTIN_TEMPLATE


def _resolve_none(_key):
    return None


def _batch(case, keys, dest_dir, **kw):
    kw.setdefault("resolve_template", _resolve_builtin)
    return wbe.export_batch(
        case, case_id=case.id, document_keys=keys, dest_dir=dest_dir, **kw)


def _docs_by_key(data):
    return {d["document_key"]: d for d in data["documents"]}


# ------------------------------------------------------------- options


class TestExportOptions:
    def test_ready_case_all_documents_listed(self):
        data = wbe.export_options(
            _ready_case(), resolve_template=_resolve_builtin)
        assert data["schema_version"] == "notary.case-drafting.v1"
        docs = _docs_by_key(data)
        assert set(docs) == {"khai_nhan_di_san", "thoa_thuan_phan_chia",
                             "niem_yet"}
        assert docs["khai_nhan_di_san"]["ready"] is True
        assert docs["khai_nhan_di_san"]["block_reason"] is None
        assert docs["thoa_thuan_phan_chia"]["ready"] is True
        assert docs["niem_yet"]["ready"] is False
        assert docs["niem_yet"]["block_reason"] == "word.template_missing"

    def test_empty_case_blocks_with_word_reason(self):
        owner = _person(1, "Nguyễn Văn Chủ", dead=date(2024, 2, 3))
        case = _make_case(owner, properties=[], case_state=None)
        data = wbe.export_options(case, resolve_template=_resolve_builtin)
        docs = _docs_by_key(data)
        assert docs["khai_nhan_di_san"]["ready"] is False
        assert docs["khai_nhan_di_san"]["block_reason"] == "word.no_assets"
        # niem_yet: template check trước data validation (mock parity)
        assert docs["niem_yet"]["block_reason"] == "word.template_missing"

    def test_missing_template_blocks_templated_docs(self):
        data = wbe.export_options(_ready_case(),
                                  resolve_template=_resolve_none)
        docs = _docs_by_key(data)
        assert docs["khai_nhan_di_san"]["block_reason"] == (
            "word.template_missing")
        assert docs["thoa_thuan_phan_chia"]["block_reason"] == (
            "word.template_missing")

    def test_no_receiver(self):
        owner = _person(1, "Nguyễn Văn Chủ", dead=date(2024, 2, 3))
        child = _person(2, "Nguyễn Văn Con")
        case = _make_case(
            owner, properties=[_prop()],
            case_state=_case_state(
                owner, child,
                nodes=[
                    _node(1, role="Owner", is_land_owner=True),
                    _node(2, role="Con", will_receive=False),
                ]))
        docs = _docs_by_key(wbe.export_options(
            case, resolve_template=_resolve_builtin))
        assert docs["khai_nhan_di_san"]["block_reason"] == "word.no_receiver"

    def test_no_deceased_landowner(self):
        owner = _person(1, "Nguyễn Văn Chủ")          # còn sống
        child = _person(2, "Nguyễn Văn Con")
        case = _make_case(
            owner, properties=[_prop()],
            case_state=_case_state(
                owner, child,
                nodes=[
                    _node(1, role="Owner", is_land_owner=True),
                    _node(2, role="Con", will_receive=True),
                ]))
        docs = _docs_by_key(wbe.export_options(
            case, resolve_template=_resolve_builtin))
        assert docs["khai_nhan_di_san"]["block_reason"] == (
            "word.no_deceased_landowner")

    def test_no_landowner_when_owner_hidden_in_diagram(self):
        owner = _person(1, "Nguyễn Văn Chủ", dead=date(2024, 2, 3))
        child = _person(2, "Nguyễn Văn Con")
        case = _make_case(
            owner, properties=[_prop()],
            case_state=_case_state(
                owner, child,
                nodes=[
                    _node(1, role="Owner", is_land_owner=True,
                          hidden=True),          # owner ẩn → không active
                    _node(2, role="Con", will_receive=True),
                ]))
        docs = _docs_by_key(wbe.export_options(
            case, resolve_template=_resolve_builtin))
        assert docs["khai_nhan_di_san"]["block_reason"] == "word.no_landowner"

    def test_too_many_assets(self):
        owner = _person(1, "Nguyễn Văn Chủ", dead=date(2024, 2, 3))
        heir = _person(2, "Nguyễn Văn Con")
        props = [_prop(dia_chi=f"Đất {i}", so_serial=f"S{i}")
                 for i in range(1, 7)]
        case = _make_case(
            owner, properties=props,
            case_state=_case_state(
                owner, heir,
                nodes=[
                    _node(1, role="Owner", is_land_owner=True),
                    _node(2, role="Con", will_receive=True),
                ]))
        docs = _docs_by_key(wbe.export_options(
            case, resolve_template=_resolve_builtin))
        assert docs["khai_nhan_di_san"]["block_reason"] == (
            "word.too_many_assets")

    def test_too_many_people(self):
        owner = _person(1, "Nguyễn Văn Chủ", dead=date(2024, 2, 3))
        people = [owner]
        nodes = [_node(1, role="Owner", is_land_owner=True)]
        for i in range(2, 23):                       # 22 người active
            p = _person(i, f"Người {i}")
            people.append(p)
            nodes.append(_node(i, role="Con", will_receive=True))
        case = _make_case(owner, properties=[_prop()],
                          case_state=_case_state(*people, nodes=nodes))
        docs = _docs_by_key(wbe.export_options(
            case, resolve_template=_resolve_builtin))
        assert docs["khai_nhan_di_san"]["block_reason"] == (
            "word.too_many_people")


# ------------------------------------------------------------- batch


class TestExportBatch:
    def test_writes_independent_docx_per_document(self, tmp_path):
        data = _batch(_ready_case(),
                      ["khai_nhan_di_san", "thoa_thuan_phan_chia"],
                      tmp_path)
        assert data["schema_version"] == "notary.case-drafting.v1"
        assert data["destination"]["is_dir"] is True
        assert data["destination"]["scope"] == "machine_local"
        assert data["breakdown"] == {
            "succeeded": ["khai_nhan_di_san", "thoa_thuan_phan_chia"],
            "failed": [], "skipped": []}
        names = {d["actual_filename"] for d in data["documents"]}
        assert names == {
            "Van_ban_khai_nhan_di_san_HS-99.docx",
            "Thoa_thuan_phan_chia_di_san_HS-99.docx"}
        for d in data["documents"]:
            assert d["status"] == "saved"
            assert d["error"] is None
            assert re.match(r"^[A-Za-z0-9_-]+_HS-99(_\d+)?\.docx$",
                            d["actual_filename"])
            assert ".." not in d["actual_filename"]
            out = Path(d["output_file"]["path"])
            assert out.parent == tmp_path
            assert out.is_file()
            doc = Document(str(out))                 # DOCX mở được
            assert doc.paragraphs

    def test_collision_with_existing_files_keeps_old_bytes(self, tmp_path):
        old1 = tmp_path / "Van_ban_khai_nhan_di_san_HS-99.docx"
        old2 = tmp_path / "Van_ban_khai_nhan_di_san_HS-99_2.docx"
        old1.write_bytes(b"cu-1")
        old2.write_bytes(b"cu-2")
        data = _batch(_ready_case(), ["khai_nhan_di_san"], tmp_path)
        doc = data["documents"][0]
        assert doc["actual_filename"] == (
            "Van_ban_khai_nhan_di_san_HS-99_3.docx")
        # file cũ nguyên byte — KHÔNG BAO GIỜ ghi đè
        assert old1.read_bytes() == b"cu-1"
        assert old2.read_bytes() == b"cu-2"

    def test_intra_batch_same_filename_stem_no_clash(
            self, tmp_path, monkeypatch):
        """Hai document_key trỏ cùng filename_stem → reservation nội
        batch → file thứ hai hậu tố _2."""
        spec = dataclasses.replace(
            wbe.DOC_CATALOG_BY_KEY["thoa_thuan_phan_chia"],
            filename_stem="Van_ban_khai_nhan_di_san")
        monkeypatch.setitem(
            wbe.DOC_CATALOG_BY_KEY, "thoa_thuan_phan_chia", spec)
        data = _batch(_ready_case(),
                      ["khai_nhan_di_san", "thoa_thuan_phan_chia"],
                      tmp_path)
        names = sorted(d["actual_filename"] for d in data["documents"])
        assert names == [
            "Van_ban_khai_nhan_di_san_HS-99.docx",
            "Van_ban_khai_nhan_di_san_HS-99_2.docx"]

    def test_partial_saved_and_failed(self, tmp_path):
        data = _batch(_ready_case(),
                      ["khai_nhan_di_san", "niem_yet"], tmp_path)
        docs = _docs_by_key(data)
        assert docs["khai_nhan_di_san"]["status"] == "saved"
        assert docs["niem_yet"]["status"] == "failed"
        assert docs["niem_yet"]["error"]["code"] == "word.template_missing"
        assert data["breakdown"]["succeeded"] == ["khai_nhan_di_san"]
        assert data["breakdown"]["failed"] == ["niem_yet"]
        assert data["breakdown"]["skipped"] == []
        # file của doc thành công tồn tại dù doc kia lỗi
        assert (tmp_path
                / "Van_ban_khai_nhan_di_san_HS-99.docx").is_file()

    def test_all_failed_raises_batch_failed_with_result(self, tmp_path):
        owner = _person(1, "Nguyễn Văn Chủ", dead=date(2024, 2, 3))
        empty = _make_case(owner, properties=[], case_state=None)
        with pytest.raises(wbe.WordBatchError) as exc:
            _batch(empty, ["khai_nhan_di_san", "niem_yet"], tmp_path)
        err = exc.value
        assert err.code == "word_batch_failed"
        rd = err.result_data
        assert rd["breakdown"] == {
            "succeeded": [],
            "failed": ["khai_nhan_di_san", "niem_yet"],
            "skipped": []}
        codes = {d["error"]["code"] for d in rd["documents"]}
        assert codes == {"word.no_assets", "word.template_missing"}
        # không file nào được tạo
        assert list(tmp_path.iterdir()) == []

    def test_template_missing_when_no_template(self, tmp_path):
        # Doc duy nhat fail -> all-failed -> word_batch_failed kem result.
        with pytest.raises(wbe.WordBatchError) as exc:
            _batch(_ready_case(), ["khai_nhan_di_san"], tmp_path,
                   resolve_template=_resolve_none)
        assert exc.value.code == "word_batch_failed"
        doc = exc.value.result_data["documents"][0]
        assert doc["status"] == "failed"
        assert doc["error"]["code"] == "word.template_missing"
        assert list(tmp_path.iterdir()) == []

    def test_unresolved_placeholders_fail_document(self, tmp_path):
        bad_template = tmp_path / "bad_template.docx"
        doc = Document()
        doc.add_paragraph("Văn bản thử — [Trường Chưa Hỗ Trợ]")
        doc.save(str(bad_template))
        with pytest.raises(wbe.WordBatchError) as exc:
            _batch(_ready_case(), ["khai_nhan_di_san"], tmp_path,
                   resolve_template=lambda _k: bad_template)
        assert exc.value.code == "word_batch_failed"
        result = exc.value.result_data["documents"][0]
        assert result["status"] == "failed"
        assert result["error"]["code"] == "word.unresolved_placeholders"
        # không output nào được tạo
        assert not list(tmp_path.glob("*_HS-*.docx"))

    def test_cancel_mid_batch_keeps_saved_and_marks_skipped(self, tmp_path):
        class _Cancel(Exception):
            def __init__(self, data):
                super().__init__("cancel")
                self.data = data

        def _check(data):
            # Raise khi đã có doc saved mà còn doc pending → tương đương
            # cancel flag của jobstore bật giữa văn bản 1 và 2.
            if data["breakdown"]["succeeded"] \
                    and data["breakdown"]["skipped"]:
                raise _Cancel(data)

        keys = ["khai_nhan_di_san", "thoa_thuan_phan_chia", "niem_yet"]
        with pytest.raises(_Cancel) as exc:
            _batch(_ready_case(), keys, tmp_path, check_cancel=_check)
        data = exc.value.data
        docs = _docs_by_key(data)
        assert docs["khai_nhan_di_san"]["status"] == "saved"
        assert docs["thoa_thuan_phan_chia"]["status"] == "skipped"
        assert docs["niem_yet"]["status"] == "skipped"
        assert data["breakdown"]["succeeded"] == ["khai_nhan_di_san"]
        assert data["breakdown"]["skipped"] == [
            "thoa_thuan_phan_chia", "niem_yet"]
        # file đã lưu giữ nguyên; file chưa bắt đầu không được tạo
        files = sorted(p.name for p in tmp_path.glob("*.docx"))
        assert files == ["Van_ban_khai_nhan_di_san_HS-99.docx"]

    def test_unsafe_generated_filename_fails_document(
            self, tmp_path, monkeypatch):
        """Defense-in-depth: filename_stem từ catalog phải là tên Windows
        hợp lệ — stem xấu → doc failed, không file nào được tạo."""
        spec = dataclasses.replace(
            wbe.DOC_CATALOG_BY_KEY["khai_nhan_di_san"],
            filename_stem="..\\evil")
        monkeypatch.setitem(
            wbe.DOC_CATALOG_BY_KEY, "khai_nhan_di_san", spec)
        with pytest.raises(wbe.WordBatchError) as exc:
            _batch(_ready_case(), ["khai_nhan_di_san"], tmp_path)
        assert exc.value.code == "word_batch_failed"
        result = exc.value.result_data["documents"][0]
        assert result["status"] == "failed"
        assert result["error"]["code"] == "word.invalid_filename"
        assert list(tmp_path.iterdir()) == []

    def test_progress_reported_per_document(self, tmp_path):
        calls = []
        _batch(_ready_case(),
               ["khai_nhan_di_san", "thoa_thuan_phan_chia"], tmp_path,
               report_progress=lambda d, t, label: calls.append((d, t)))
        assert calls == [(1, 2), (2, 2)]


# ---------------------------------------------------- payload validation


class TestDocumentKeysValidation:
    @pytest.mark.parametrize("bad", [None, "khai_nhan_di_san", 3,
                                     {"a": 1}, (("khai_nhan_di_san"),)])
    def test_non_list_keys_validation_error(self, tmp_path, bad):
        with pytest.raises(wbe.WordBatchError) as exc:
            _batch(_ready_case(), bad, tmp_path)
        assert exc.value.code == "validation_error"

    def test_empty_keys(self, tmp_path):
        with pytest.raises(wbe.WordBatchError) as exc:
            _batch(_ready_case(), [], tmp_path)
        assert exc.value.code == "word_no_documents_selected"

    def test_duplicate_keys(self, tmp_path):
        with pytest.raises(wbe.WordBatchError) as exc:
            _batch(_ready_case(),
                   ["khai_nhan_di_san", "khai_nhan_di_san"], tmp_path)
        assert exc.value.code == "word_duplicate_document_key"
        assert exc.value.details["document_key"] == "khai_nhan_di_san"

    @pytest.mark.parametrize("key", ["khong_co", "BAD-KEY", 42])
    def test_unknown_or_malformed_keys(self, tmp_path, key):
        with pytest.raises(wbe.WordBatchError) as exc:
            _batch(_ready_case(), [key], tmp_path)
        assert exc.value.code == "word_unknown_document_key"

    def test_validation_happens_before_any_file(self, tmp_path):
        for keys in ([], ["khai_nhan_di_san", "khai_nhan_di_san"],
                     ["khong_co"]):
            with pytest.raises(wbe.WordBatchError):
                _batch(_ready_case(), keys, tmp_path)
        assert list(tmp_path.iterdir()) == []

    def test_missing_destination_dir(self, tmp_path):
        with pytest.raises(wbe.WordBatchError) as exc:
            _batch(_ready_case(), ["khai_nhan_di_san"],
                   tmp_path / "khong-ton-tai")
        assert exc.value.code == "file_not_found"


# ------------------------------------------------- filename safety unit


class TestFilenameSafety:
    @pytest.mark.parametrize("name", [
        "CON.docx", "NUL.txt", "LPT1.docx",
        "a\\b_HS-99.docx", "a/b_HS-99.docx", "a:b_HS-99.docx",
        "..\\evil_HS-99.docx", "a..b_HS-99.docx",
        "a?_HS-99.docx", "a*_HS-99.docx",
        "trail _HS-99.docx ", ".dot_HS-99.docx", "name_HS-99.docx.",
    ])
    def test_unsafe_windows_names_rejected(self, name):
        assert wbe.is_safe_windows_filename(name) is False

    @pytest.mark.parametrize("name", [
        "Van_ban_khai_nhan_di_san_HS-99.docx",
        "Thoa_thuan_phan_chia_di_san_HS-99_12.docx",
        # "CON_HS-99" khong phai reserved name (chi stem dung "CON" moi bi cam)
        "CON_HS-99.docx",
    ])
    def test_safe_names_accepted(self, name):
        assert wbe.is_safe_windows_filename(name) is True
