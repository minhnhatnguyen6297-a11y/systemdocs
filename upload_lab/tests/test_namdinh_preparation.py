"""NamDinh adapter boundaries on controlled observed widget shapes, not portal catalogs.

No credentials, owner samples, production DB or network. Set CASE_FIELDS_CHROMIUM
for the actual consumer smoke; NAMDINH_PREPARATION_EVIDENCE_DIR retains safe proof.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from threading import Event

import pytest

from batch_scan import connect_registry, upsert_registry_record
from playwright_uploader import NamDinhUploaderSession, UploaderSettings, build_upload_form_data


SKIPPED = {
    "ghi_chu": "ghichu", "phi_cong_chung": "chiphi.phicongchung",
    "thu_lao_cong_chung": "chiphi.thulaoCongchung",
    # Website names are only fixture DOM IDs, not new app/business keys.
    "chiphi.phiDvNgoaicongchung": "chiphi.phiDvNgoaicongchung",
    "chiphi.phikhac": "chiphi.phikhac",
}
CASE = {
    "tenvanban": "Văn bản kiểm soát ngoài gợi ý", "nhomhopdong": "Nhóm kiểm soát",
    "loaivanbannhandien": None, "socongchung": "001/2026", "ngaycongchung": "2026-06-15",
    "congchungvien": "CCV kiểm soát", "thuky": "Thư ký ngoài gợi ý", "chudat": None,
}


def payload(source):
    return {"case": copy.deepcopy(CASE), "web_form": {
        "loai_tai_san": "Tài sản kiểm soát", "nguoi_yeu_cau": "Người tổng hợp",
        "duong_su": "Đương sự tổng hợp", "tai_san": "Tài sản tổng hợp",
        "tinh_trang": "Đang xử lý", **{key: "DO NOT FILL" for key in SKIPPED},
    }, "raw": {"file_goc": str(source), "source_refs": [{"kind": "controlled"}]}}


def test_builder_omits_skipped_fields_and_status_is_portal_policy(tmp_path):
    data = payload(tmp_path / "controlled.docx")
    before = copy.deepcopy(data)
    form = build_upload_form_data(data)
    assert not set(SKIPPED).intersection(form)
    assert form["tinh_trang"] == "Đã công chứng"
    assert form["file_hop_dong"] == str(tmp_path / "controlled.docx")
    assert data == before
    assert set(data["case"]) == set(CASE)


def controlled_form(*, title_option=False, remote_option=True):
    # SOT §4.2: MUI-like status div+hidden input, freeSolo title/secretary,
    # remote input+role option object, tel date, CKEditor and single file input.
    # Values below deliberately are NOT asserted to be live portal catalogs.
    fields = [
        ("hopdong.tenhopdong", "Tên hợp đồng", True, [CASE["tenvanban"]] if title_option else []),
        ("nhomhopdongId", "Nhóm hợp đồng", False, [CASE["nhomhopdong"]] if remote_option else []),
        ("loaiTaisan", "Loại tài sản", False, ["Tài sản kiểm soát"]),
        ("hopdong.congchungvien.id", "Công chứng viên", False, [CASE["congchungvien"]]),
        ("hopdong.thuky", "Thư ký", True, []),
    ]
    controls = []
    for element_id, label, free_solo, options in fields:
        controls.append(f'<div class="Field-container"><label for="{element_id}">{label}</label>'
                        f'<input id="{element_id}" role="combobox" autocomplete="off" '
                        f'data-free="{str(free_solo).lower()}" data-options=\'{json.dumps(options, ensure_ascii=False)}\'></div>')
    controls.extend([
        '<div class="Field-container"><label>Tình trạng</label><div id="hopdong.tinhtrang" role="combobox" tabindex="0">Đang xử lý</div><input type="hidden" value="DANGXULY" id="status-value"></div>',
        '<label>Ngày công chứng<input type="tel" placeholder="dd/mm/yyyy"></label>',
        '<label>Số công chứng<input id="hopdong.sohopdong"></label>',
    ])
    for label in ("Thông tin người yêu cầu công chứng", "Đương sự", "Tài sản"):
        controls.append(f'<div class="Field-container"><label>{label}</label><div contenteditable="true"></div></div>')
    controls.append('<label>Văn bản hợp đồng<input type="file" id="hopdong.fileHopdong" accept=".doc,.docx,.pdf"></label>')
    for element_id in SKIPPED.values():
        tag = 'textarea' if element_id == 'ghichu' else 'input'
        controls.append(f'<label>{element_id}<{tag} id="{element_id}" data-skip="true"' +
                        ('>portal default</textarea>' if tag == 'textarea' else ' value="portal default">') + '</label>')
    return '''<!doctype html><meta charset="utf-8"><title>Controlled preSave</title>
<style>label,input,[role=combobox],[contenteditable]{display:block;margin:5px} [contenteditable]{border:1px solid;width:500px;min-height:30px} [role=option]{cursor:pointer;border:1px solid;padding:6px}</style>
<form id="controlled">''' + ''.join(controls) + '''<button type="submit" id="save">Lưu hợp đồng</button></form>
<script>
window.proof = {submit:0,saveClicks:0,enters:0,skipEvents:0,values:{},selected:{},attachment:null};
const form=document.getElementById('controlled');
form.addEventListener('submit', e => {e.preventDefault(); proof.submit++});
form.addEventListener('keydown', e => {if(e.key==='Enter') proof.enters++});
document.getElementById('save').addEventListener('click', () => proof.saveClicks++);
let list;
function closeList(){if(list)list.remove();list=null}
function options(el){
 closeList();list=document.createElement('ul');list.setAttribute('role','listbox');
 for(const label of JSON.parse(el.dataset.options).filter(x=>x.includes(el.value))){
  const li=document.createElement('li');li.setAttribute('role','option');li.textContent=label;
  li.addEventListener('mousedown',e=>e.preventDefault());
  li.addEventListener('click',()=>{el.value=label;proof.values[el.id]=label;proof.selected[el.id]={label};closeList()});list.append(li);
 }
 el.parentElement.append(list);
}
for(const el of form.querySelectorAll('input[data-free]')){
 el.addEventListener('input',()=>{if(el.dataset.free==='true') proof.values[el.id]=el.value; options(el)});
 el.addEventListener('focus',()=>options(el));
 el.addEventListener('blur',()=>{if(el.dataset.free==='false'&&!proof.selected[el.id])el.value='';closeList()});
}
const status=document.getElementById('hopdong.tinhtrang');
status.addEventListener('click',()=>{
 closeList();list=document.createElement('ul');list.setAttribute('role','listbox');
 for(const [value,label] of [['DANGXULY','Đang xử lý'],['DACONGCHUNG','Đã công chứng'],['HS_HUY','Hủy bỏ']]){
  const li=document.createElement('li');li.setAttribute('role','option');li.textContent=label;
  li.onclick=()=>{status.textContent=label;document.getElementById('status-value').value=value;proof.values.status=value;closeList()};list.append(li);
 }status.parentElement.append(list);
});
for(const el of form.querySelectorAll('[data-skip]')) for(const event of ['input','change','blur']) el.addEventListener(event,()=>proof.skipEvents++);
for(const el of form.querySelectorAll('[contenteditable]')) el.addEventListener('input',()=>proof.values[el.parentElement.querySelector('label').textContent]=el.innerHTML);
document.getElementById('hopdong.fileHopdong').addEventListener('change',async e=>{
 const file=e.target.files[0];proof.attachment=file?{name:file.name,size:file.size,text:await file.text()}:null;
});
</script>'''


@pytest.mark.parametrize("title_option,remote_option,missing_file", [(False, True, False), (True, True, False), (False, False, False), (False, True, True)])
def test_real_consumer_presave_no_submit_and_attachment(tmp_path, monkeypatch, title_option, remote_option, missing_file):
    executable = os.environ.get("CASE_FIELDS_CHROMIUM")
    if not executable:
        pytest.skip("Set CASE_FIELDS_CHROMIUM for isolated real Chromium consumer proof")
    from playwright.sync_api import sync_playwright
    import playwright_uploader
    source = tmp_path / "controlled.docx"
    source.write_bytes(b"Controlled technical source, not an owner document.")
    data = payload(source)
    original = copy.deepcopy(data)
    work = tmp_path / "work"
    output = work / "output.json"
    work.mkdir()
    output.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    before_output = output.read_bytes()
    conn = connect_registry(work / "registry.sqlite3")
    upsert_registry_record(conn, file_key="controlled", file_path=source, stat_result=source.stat(),
                           customer_folder="controlled", status="extracted", run_id="controlled",
                           contract_no="001/2026", output_json_path=str(output), case_fields=CASE)
    record_id = conn.execute("SELECT id FROM file_registry").fetchone()[0]
    conn.close()
    manifest = work / "manifest.json"
    manifest.write_text('{"run_id":"controlled"}', encoding="utf-8")
    if missing_file:
        source.unlink()
    monkeypatch.setattr(playwright_uploader, "load_requester_contract_lookup", lambda **kwargs: ({}, ""))
    # Simulate a caller carrying legacy nonempty skipped values: consumer must
    # ignore them as well, not rely on today's builder returning empty values.
    real_builder = playwright_uploader.build_upload_form_data
    monkeypatch.setattr(playwright_uploader, "build_upload_form_data", lambda *args, **kwargs: {
        **real_builder(*args, **kwargs), **{key: "DO NOT FILL" for key in SKIPPED}})
    settings = UploaderSettings(base_url="http://controlled.invalid", login_url="http://controlled.invalid/login",
                                create_url="http://controlled.invalid/create", storage_state_path=work / "unused.json",
                                post_prepare_delay_ms=0)
    session = NamDinhUploaderSession(settings, working_dir=work, log_callback=lambda _: None)
    monkeypatch.setattr(session, "ensure_authenticated", lambda **kwargs: None)
    evidence = Path(os.environ.get("NAMDINH_PREPARATION_EVIDENCE_DIR", str(tmp_path / "proof")))
    evidence.mkdir(parents=True, exist_ok=True)
    case_name = f"title-{title_option}-remote-{remote_option}-missing-{missing_file}"
    network = []
    with sync_playwright() as driver:
        browser = driver.chromium.launch(executable_path=executable, headless=True)
        try:
            session.context = browser.new_context()
            def route_local(route):
                network.append({"method": route.request.method, "url": route.request.url})
                if route.request.url == settings.create_url and route.request.method == "GET":
                    body = controlled_form(title_option=title_option, remote_option=remote_option)
                    if missing_file:
                        # Unrelated page text must never stand in for attachment state.
                        body += '<aside id="filename-decoy">controlled.docx</aside>'
                    route.fulfill(status=200, content_type="text/html", body=body)
                else:
                    route.abort()
            session.context.route("**/*", route_local)
            summary = session.prepare_manifest(manifest, Event(), selected_record_ids={record_id}, chunk_size=1)
            page = session.prepared_pages[record_id].page
            state = page.evaluate("proof")
            file_dom = page.locator('[id="hopdong.fileHopdong"]').evaluate("el => [...el.files].map(f=>({name:f.name,size:f.size}))")
            skipped_values = {key: page.locator(f'[id="{element_id}"]').input_value() for key, element_id in SKIPPED.items()}
            debug = json.loads(next(Path(summary["artifact_dir"]).glob("debug_*.json")).read_text(encoding="utf-8"))
            proof = {"scope": "controlled local observed widget shapes, NOT portal persistence/catalog acceptance",
                     "state": state, "file_dom": file_dom, "skipped_values": skipped_values, "network": network,
                     "status_value": page.locator('#status-value').input_value(), "debug": debug, "summary": summary}
            proof["filename_decoy_visible"] = (
                page.locator("#filename-decoy").is_visible() if missing_file else False)
            (evidence / f"{case_name}.json").write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8")
            page.screenshot(path=str(evidence / f"{case_name}.png"), full_page=True)
            assert state["submit"] == 0 and state["saveClicks"] == 0 and state["enters"] == 0
            assert state["skipEvents"] == 0 and set(skipped_values.values()) == {"portal default"}
            assert proof["status_value"] == "DACONGCHUNG"
            assert state["values"]["hopdong.tenhopdong"] == CASE["tenvanban"]
            assert state["values"]["hopdong.thuky"] == CASE["thuky"]
            assert state["values"]["Tài sản"] == "Tài sản tổng hợp"
            if not missing_file:
                assert file_dom == [{"name": source.name, "size": source.stat().st_size}]
                assert state["attachment"]["text"] == source.read_text(encoding="utf-8")
            else:
                assert proof["filename_decoy_visible"]
                assert page.get_by_text(source.name, exact=True).is_visible()
                assert not debug["field_results"]["file_hop_dong"]["success"]
                assert debug["verify"]["fields"]["file_hop_dong"]["actual"] == ""
                assert file_dom == [] and state["attachment"] is None
                assert not debug["verify"]["fields"]["file_hop_dong"]["success"]
            if remote_option:
                assert state["selected"]["nhomhopdongId"] == {"label": CASE["nhomhopdong"]}
            else:
                assert "nhomhopdongId" not in state["selected"]
                assert not debug["verify"]["fields"]["nhom_hop_dong"]["success"]
            assert summary["prepared_count"] == 1
            assert debug["verify"]["fields"]["tinh_trang"]["success"]
            row_conn = connect_registry(work / "registry.sqlite3")
            row = row_conn.execute("SELECT status,case_json FROM file_registry WHERE id=?", (record_id,)).fetchone()
            row_conn.close()
            assert row["status"] == ("prepared_partial" if missing_file or not remote_option else "prepared_dry_run")
            assert json.loads(row["case_json"]) == CASE
            assert output.read_bytes() == before_output and data == original
            assert network == [{"method": "GET", "url": settings.create_url}]
        finally:
            browser.close()
