"""pii_redact: che PII/duong dan/token trong log + exception (bug-evidence).

Du lieu trong file nay la GIA LAP.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path

import pytest

import pii_redact as p

ROOT = Path(__file__).resolve().parents[2]


def test_copies_identical():
    a = (ROOT / "notary_v2" / "pii_redact.py").read_bytes()
    b = (ROOT / "shell" / "sidecar" / "pii_redact.py").read_bytes()
    assert a == b, "notary_v2/pii_redact.py va shell/sidecar/pii_redact.py phai giong het"


@pytest.mark.parametrize("raw, leaked, marker", [
    ("RuntimeError: parser exploded at C:\\secret\\path with token xyz",
     ["C:\\secret", "xyz"], "<path>"),
    ("loi doc \\\\fileserver\\share\\ho_so\\a.pdf", ["fileserver", "ho_so"], "<path>"),
    ("loi doc \\\\?\\D:\\very\\long\\x.docx", ["very\\long"], "<path>"),
    ("open /home/tester/hs/a.docx failed", ["/home/tester", "a.docx"], "<path>"),
    ("auth Bearer abc.def.ghi", ["abc.def"], "<token>"),
    ("token=s3cr3tValue&x=1", ["s3cr3tValue"], "<token>"),
    ('{"password": "hunter2"}', ["hunter2"], "<token>"),
    ("push ghp_ABCDEFabcdef0123456789xyzXYZ", ["ghp_ABC"], "<token>"),
    ("CCCD 001080012345 khong hop le", ["001080012345"], "<cccd>"),
    ("CMND so: 123456789", ["123456789"], "<cccd>"),
    ("ngay sinh 01/02/1980", ["01/02/1980"], "<date>"),
    ("dob=1980-02-01 sai", ["1980-02-01"], "<date>"),
    ("Nguyễn Văn An khong khop", ["Văn An"], "<name>"),
    ("ho ten: Thị Bé Mười", ["Bé Mười"], "<name>"),
    ("địa chỉ: Số 12 Thôn Đông, Yên Phú", ["Thôn Đông", "Yên Phú"], "<address>"),
    ("tai xã Yên Phú, huyện Ý Yên", ["Yên Phú", "Ý Yên"], "<address>"),
])
def test_redact_text(raw, leaked, marker):
    out = p.redact_text(raw)
    for s in leaked:
        assert s not in out, out
    assert marker in out


@pytest.mark.parametrize("keep", [
    "job 2026-10-28T10:00:00 ok",
    "GET http://127.0.0.1:8000/api/v1/jobs status=500",
    "page 3/12 record_count=40",
    "ValueError: thieu truong so_to",
])
def test_no_false_positive_on_operational_text(keep):
    assert p.redact_text(keep) == keep


def test_redact_exception_zalo_example():
    exc = RuntimeError("parser exploded at C:\\secret\\path with token xyz")
    assert p.redact_exception(exc) == \
        "RuntimeError: parser exploded at <path> with token <token>"


def test_add_secret_literal():
    p.add_secret("sidecar-tok-0f9e8d")
    assert "sidecar-tok" not in p.redact_text("hdr sidecar-tok-0f9e8d")


def _logger_with_buffer():
    buf = io.StringIO()
    lg = logging.getLogger("test.pii_redact")
    lg.handlers.clear()
    lg.propagate = False
    h = logging.StreamHandler(buf)
    h.setFormatter(logging.Formatter("%(message)s"))
    lg.addHandler(h)
    p.attach_filter(lg)
    return lg, buf


def test_filter_redacts_args_and_traceback():
    lg, buf = _logger_with_buffer()
    lg.warning("job %s failed for %s", "j1", "Trần Thị Lan 001080012345")
    try:
        raise RuntimeError("bad file C:\\Users\\tester\\hs.docx")
    except RuntimeError:
        lg.exception("crash")
    out = buf.getvalue()
    assert "j1" in out
    for s in ("Thị Lan", "001080012345", "C:\\Users", "hs.docx"):
        assert s not in out, out
    assert "<cccd>" in out and "<path>" in out and "Traceback" in out


def test_redacting_stream():
    inner = io.StringIO()
    st = p.RedactingStream(inner)
    st.write("WARN: loi o /var/lib/x/y.db ")
    st.write("token abc123\nkhong ")
    st.flush()
    out = inner.getvalue()
    assert "/var/lib" not in out and "abc123" not in out
    assert out.startswith("WARN: loi o <path> token <token>\n")


def test_parse_runner_sanitize_uses_redaction():
    from services.zalo_exchange.parse_runner import _sanitize_error
    msg = _sanitize_error(
        RuntimeError("parser exploded at C:\\secret\\path with token xyz"))
    assert msg == "RuntimeError: parser exploded at <path> with token <token>"


def test_observability_attaches_filter(tmp_path, monkeypatch):
    import observability
    root = logging.getLogger()
    before = list(root.handlers)
    try:
        monkeypatch.setattr(observability.os.path, "abspath",
                            lambda _f: str(tmp_path / "observability.py"))
        observability.configure_process_logging("pii_test")
        added = [h for h in root.handlers if h not in before]
        assert added and all(p._FILTER in h.filters for h in added)
    finally:
        for h in list(root.handlers):
            if h not in before:
                root.removeHandler(h)
                h.close()
