"""Reviewed occurrence bindings for the original Word, using integrated catalog values."""
from __future__ import annotations
import copy
import hashlib
import json
from .document_intake.docx_source import read_docx, replace_spans
from . import word_engine, word_batch_export as batch
from .case_rows import materialize_case_state

PERSON_LABELS = {"ho_ten": "Họ tên", "so_giay_to": "Số giấy tờ", "ngay_sinh": "Ngày sinh",
                 "ngay_cap": "Ngày cấp", "noi_cap": "Nơi cấp", "dia_chi": "Địa chỉ", "ngay_chet": "Ngày chết"}
ASSET_LABELS = {"so_serial": "Serial", "so_vao_so": "Số vào sổ", "so_thua_dat": "Số thửa",
                "so_to_ban_do": "Số tờ", "dia_chi": "Địa chỉ", "ngay_cap": "Ngày cấp sổ",
                "co_quan_cap": "Cơ quan cấp sổ", "dien_tich": "Diện tích", "loai_dat": "Loại đất"}


def slot_for(snapshot, target, row_id, field_key, ref=None, record=None):
    rows = snapshot.get("stage" if target == "person" else "assets", [])
    index = next((i + 1 for i, row in enumerate(rows) if row.get("row_id") == row_id), None)
    if index is None:
        raise ValueError("Dòng đã bị xóa; hãy kiểm tra lại vị trí")
    if field_key == "land_rows" and ref:
        labels = {"loai_dat": "Loại đất", "dien_tich": "Diện tích", "thoi_han": "Thời hạn"}
        identity = (record or {}).get('land_rows')
        land_index = ref['land_row']
        if identity is not None:
            if land_index not in identity:
                raise ValueError('Dòng đất nguồn đã bị xóa; bỏ vị trí cũ và kiểm tra lại')
            land_index = identity.index(land_index) + 1
        return f"[Loại đất {index}.{land_index} - {labels[ref['land_field']]}]"
    label = (PERSON_LABELS if target == "person" else ASSET_LABELS).get(field_key)
    if label is None:
        raise ValueError("Trường chưa có vị trí Word hỗ trợ")
    prefix = f"Người {index}" if target == "person" else f"Tài sản {index}"
    if target == "person" and snapshot.get("case_type") == "two_party":
        nodes = snapshot.get("diagram", {}).get("state", {}).get("nodes", [])
        node = next((n for n in nodes if n.get("personId") == row_id), None)
        if node is None:
            raise ValueError("Người chưa được đặt vào ô Bên A/B đã lưu")
        number = int(node["id"].removeprefix("p"))
        prefix = f"Bên {'A' if number <= 15 else 'B'} {number if number <= 15 else number - 15}"
    return f"[{prefix} - {label}]"


def validate_context(context, stage, store, *, read_only=False):
    """Validate opaque references before the Stage transaction; prune removed rows.

    `read_only=True` (bản sao Hồ sơ) chỉ kiểm shape/bytes/candidate/record/
    occurrence: không prune record/binding, không đổi label/template_sha256
    và không `save_template`. Mọi tham chiếu thiếu dòng đích là lỗi, không
    âm thầm bỏ nội dung."""
    if not isinstance(context, dict) or set(context) != {"version", "sources"} or type(context["version"]) is not int or context["version"] != 1:
        raise ValueError("Đối chiếu nguồn Word không hợp lệ")
    if not isinstance(context["sources"], list) or len(context["sources"]) > 8:
        raise ValueError("Tối đa 8 nguồn Word trong hồ sơ")
    result = copy.deepcopy(context)
    rows = {row["row_id"]: target for target, name in (("person", "people"), ("asset", "assets")) for row in stage[name]}
    seen_sources = set()
    for source in result["sources"]:
        if not isinstance(source, dict) or not {"source_id", "sha256", "records", "bindings"} <= set(source) or set(source) - {"source_id", "sha256", "records", "bindings", "template_sha256", 'label'}:
            raise ValueError("Nguồn Word có trường không hợp lệ")
        if source["source_id"] in seen_sources:
            raise ValueError("Nguồn Word bị lặp")
        seen_sources.add(source["source_id"])
        if not isinstance(source["records"], list) or not isinstance(source["bindings"], list):
            raise ValueError("Danh sách đối chiếu Word không hợp lệ")
        if store is None:
            raise ValueError("Kho nguồn Word chưa sẵn sàng")
        content, package = store.load(source["source_id"], source["sha256"])
        if not read_only:
            source['label'] = package.get('label', 'Hợp đồng Word')
        candidates = {s["suggestion_id"]: s for s in package["suggestions"]}
        retained, seen = [], set()
        for record in source["records"]:
            if not isinstance(record, dict) or not {'candidate_id', 'row_id'} <= set(record) or set(record) - {'candidate_id', 'row_id', 'land_rows'}:
                raise ValueError("Dòng đối chiếu Word không hợp lệ")
            candidate = candidates.get(record["candidate_id"])
            if candidate is None or record["candidate_id"] in seen:
                raise ValueError("Ứng viên Word không hợp lệ hoặc bị lặp")
            seen.add(record["candidate_id"])
            if record["row_id"] not in rows:
                if read_only:
                    raise ValueError("Dòng đối chiếu Word không có trong Hồ sơ sao")
                continue
            if rows[record["row_id"]] != candidate["target"]:
                raise ValueError("Không thể gắn người với dòng tài sản")
            if candidate['target'] == 'asset' and 'land_rows' in candidate['fields']:
                original_rows = json.loads(candidate['fields']['land_rows']['normalized_value'])
                current = next(r for r in stage['assets'] if r['row_id'] == record['row_id'])
                identity = record.setdefault('land_rows', list(range(1, len(original_rows) + 1)))
                if (not isinstance(identity, list) or len(identity) != len(current.get('land_rows', [])) or
                    any(n is not None and (type(n) is not int or not 1 <= n <= len(original_rows)) for n in identity) or
                    len([n for n in identity if n is not None]) != len(set(n for n in identity if n is not None))):
                    raise ValueError('Danh tính dòng đất không khớp; hãy kiểm tra lại nguồn')
            retained.append(record)
        source["records"] = retained
        valid = {r["candidate_id"] for r in retained}
        bindings, occurrences = [], set()
        for binding in source["bindings"]:
            if not isinstance(binding, dict) or set(binding) != {"candidate_id", "occurrence_id", "field_key", "slot"}:
                raise ValueError("Vị trí Word không hợp lệ")
            if binding["candidate_id"] not in valid:
                if read_only:
                    raise ValueError("Vị trí Word trỏ ứng viên đã mất")
                continue
            candidate = candidates[binding["candidate_id"]]
            refs = candidate["fields"].get(binding["field_key"], {}).get("source_refs", [])
            record = next(r for r in retained if r['candidate_id'] == binding['candidate_id'])
            if binding['field_key'] == 'land_rows' and not any(r['occurrence_id'] == binding['occurrence_id'] and r['land_row'] in record.get('land_rows', []) for r in refs):
                if read_only:
                    raise ValueError("Vị trí đất không còn thuộc dòng nguồn")
                continue  # Deleted source row cannot transfer its occurrence to a surviving row.
            if not any(ref["occurrence_id"] == binding["occurrence_id"] for ref in refs):
                raise ValueError("Vị trí không thuộc trường của ứng viên")
            if binding["occurrence_id"] in occurrences:
                raise ValueError("Vị trí Word bị gắn hai lần")
            occurrences.add(binding["occurrence_id"])
            bindings.append(binding)
        source["bindings"] = bindings
        if read_only:
            continue
        if bindings:
            replacements = []
            for binding in bindings:
                field = candidates[binding["candidate_id"]]["fields"][binding["field_key"]]
                ref = next(r for r in field["source_refs"] if r["occurrence_id"] == binding["occurrence_id"])
                replacements.append((ref["span"], binding["slot"]))
            derivative = replace_spans(content, read_docx(content), replacements)
            source["template_sha256"] = store.save_template(source["source_id"], derivative)
        else:
            source.pop("template_sha256", None)
    return result


def validate_new_bindings(case, context, previous, store):
    """Check new confirmations against the composed committed rows/seats before DB commit."""
    snapshot = values = None
    old = {(s['source_id'], json.dumps(b, sort_keys=True), json.dumps(next((r for r in s['records'] if r['candidate_id'] == b['candidate_id']), {}), sort_keys=True))
           for s in (previous or {}).get('sources', []) for b in s['bindings']}
    for source in context.get('sources', []):
        _, package = store.load(source['source_id'], source['sha256'])
        candidates = {s['suggestion_id']: s for s in package['suggestions']}
        for binding in source['bindings']:
            record = next(r for r in source['records'] if r['candidate_id'] == binding['candidate_id'])
            if (source['source_id'], json.dumps(binding, sort_keys=True), json.dumps(record, sort_keys=True)) in old:
                continue
            if values is None:
                snapshot = materialize_case_state(case)
                values = word_engine.build_binding_mapping(case)
            candidate = candidates[binding['candidate_id']]
            ref = next(r for r in candidate['fields'][binding['field_key']]['source_refs'] if r['occurrence_id'] == binding['occurrence_id'])
            slot = slot_for(snapshot, candidate['target'], record['row_id'], binding['field_key'], ref, record)
            if slot != binding['slot'] or values.get(slot) in (None, ''):
                raise ValueError('Vị trí Word không khớp dòng/ô đã lưu hoặc chưa có giá trị: ' + slot)


def reviewed_template(case, source_id, store, *, missing=None):
    """Dựng bản gốc đã thay tại đúng span đã xác nhận.

    Vị trí đã xác nhận nhưng trường chưa có giá trị đã lưu KHÔNG chặn
    xuất (owner 23/10/2026 phần W): chỗ đó để trống và ghi vào `missing`.
    Lệch slot/hash vẫn là lỗi mapping thật (hồ sơ đổi cấu trúc)."""
    snapshot = materialize_case_state(case)
    source = next((s for s in snapshot.get("docx_import", {}).get("sources", []) if s["source_id"] == source_id), None)
    if source is None or not source["bindings"]:
        raise ValueError("Chưa xác nhận các vị trí của nguồn Word trong hồ sơ này")
    content, package = store.load(source_id, source["sha256"])
    reader = read_docx(content)
    candidates = {s["suggestion_id"]: s for s in package["suggestions"]}
    records = {r["candidate_id"]: r for r in source["records"]}
    values = word_engine.build_template_mapping(case, static=True)
    tokens, replacements = [], []
    for binding in source["bindings"]:
        candidate = candidates[binding["candidate_id"]]
        ref = next(r for r in candidate["fields"][binding["field_key"]]["source_refs"] if r["occurrence_id"] == binding["occurrence_id"])
        record = records[binding['candidate_id']]
        slot = slot_for(snapshot, candidate["target"], record['row_id'], binding["field_key"], ref, record)
        if slot != binding["slot"]:
            raise ValueError("Thứ tự người/tài sản hoặc ô Bên A/B đã đổi; xác nhận lại vị trí")
        tokens.append((ref["span"], slot))
        if slot not in values or values[slot] in (None, ""):
            if missing is not None and slot not in missing:
                missing.append(slot)
            replacements.append((ref["span"], ""))
            continue
        replacements.append((ref["span"], str(values[slot])))
    derivative = replace_spans(content, reader, tokens)
    derivative_hash = hashlib.sha256(derivative).hexdigest()
    if source.get("template_sha256") != derivative_hash:
        raise ValueError("Mẫu đã đổi; cần xác nhận lại vị trí")
    store.load_template(source_id, derivative_hash)
    # Re-create the derivative from verified original bytes on every export.
    # Exact spans resolve through the integrated mapping, avoiding global string replacement.
    rendered = replace_spans(content, reader, replacements)
    return rendered, derivative_hash


def binding_proposals(case, source_id, store):
    snapshot = materialize_case_state(case)
    source = next((s for s in snapshot.get("docx_import", {}).get("sources", []) if s["source_id"] == source_id), None)
    if source is None:
        raise ValueError("Nguồn Word không thuộc hồ sơ")
    content, package = store.load(source_id, source["sha256"])
    reader = read_docx(content)
    candidates = {s["suggestion_id"]: s for s in package["suggestions"]}
    values = word_engine.build_binding_mapping(case)
    proposals = []
    for record in source["records"]:
        candidate = candidates[record["candidate_id"]]
        row = next((r for r in snapshot.get("stage" if candidate["target"] == "person" else "assets", [])
                    if r.get("row_id") == record["row_id"]), {})
        for field_key, field in candidate["fields"].items():
            for ref in field["source_refs"]:
                try:
                    slot = slot_for(snapshot, candidate["target"], record["row_id"], field_key, ref, record)
                    reason = reader.replacement_reason(ref['span'])
                    if slot not in values or values[slot] in (None, ''):
                        reason = reason or 'Vị trí chưa có giá trị đã lưu'
                except ValueError as exc:
                    slot, reason = '', str(exc)
                proposals.append({"candidate_id": record["candidate_id"], "occurrence_id": ref["occurrence_id"],
                    "field_key": field_key, "slot": slot, "raw_snippet": ref["raw_snippet"],
                    "row_id": record["row_id"], "row_label": row.get("ho_ten") or row.get("so_serial") or record["row_id"],
                    "value": str(values.get(slot, "")),
                    "supported": reason is None, 'reason': reason,
                    'selected': reason is None and any(b['occurrence_id'] == ref['occurrence_id'] and b['slot'] == slot for b in source['bindings'])})
    return proposals


def export_original(case, source_id, store, destination, *, check_cancel=None):
    from pathlib import Path
    dest = Path(destination)
    spec = batch.WordDocumentSpec("original.docx", "Hợp đồng Word gốc", "hop_dong_goc", True)
    reason = word_engine.word_block_reason(
        word_engine.build_word_context(case), static=True)
    if reason is not None:
        entry = batch._failed_entry(spec, reason, batch._block_message(reason))
        data = batch._batch_data(
            dest, [entry], succeeded=[], failed=[spec.document_key], skipped=[])
        raise batch.WordBatchError(
            "word_batch_failed", "Toàn bộ văn bản trong lượt xuất đều lỗi",
            details={"documents": [{"document_key": spec.document_key,
                                   **entry["error"]}]},
            result_data=data)
    missing = []
    try:
        rendered, _ = reviewed_template(case, source_id, store,
                                        missing=missing)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        raise batch.WordBatchError("word.original_mapping_invalid", str(exc)) from exc
    temp = None
    try:
        temp = batch._temp_file_in(dest, prefix=".word_export_", suffix=".docx")
        temp.write_bytes(rendered)
        if check_cancel:
            check_cancel()
        name = batch._publish(temp, dest, spec, case.id, set())
    except PermissionError as exc:
        raise batch.WordBatchError("file_locked", "Không ghi được file Word trong thư mục đích") from exc
    except OSError as exc:
        raise batch.WordBatchError("word.render_failed", "Không lưu được file Word") from exc
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
    return batch._batch_data(dest, [{"document_key": "original.docx", "display_name": spec.display_name,
        "status": "saved", "actual_filename": name, "output_file": {"path": str(dest / name), "scope": "machine_local"},
        "error": None, "missing": missing}], succeeded=["original.docx"], failed=[], skipped=[])
