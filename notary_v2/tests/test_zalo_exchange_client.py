"""Tests for services.zalo_exchange.client (MIN-99 slice A).

Fake module = httpx.MockTransport implementing the contract ``/intake/v1``
surface (contracts/zalo-intake §7/§9/§10) exactly as the producer routes it.
"""
import json

import httpx
import pytest

from services.zalo_exchange.client import (
    IntakeClient,
    IntakeClientError,
    MAX_PAGE_LIMIT,
)

CONSUMER_ID = "c0000000-0000-4000-8000-000000000001"
PACKAGE_ID = "a0000000-0000-4000-8000-000000000001"
REQUEST_ID = "d0000000-0000-4000-8000-000000000001"
MANIFEST_SHA = "9f6d749267fc583b27812443a9021e3b469a968ef9823c156e098630b2583a4a"

STATUS_DOC = {
    "schema_version": "intake.service-status.v1",
    "producer": {"service": "zalo-intake", "build_id": "test"},
    "observed_at": "2026-09-24T08:00:00+07:00",
    "listener": {"state": "connected"},
    "pending": {"packages": 0},
    "storage": {"ack_bytes": 0, "ack_cap_bytes": 1073741824, "ack_warn": False},
    "capabilities": {"source_event_types": {
        "recall": "supported", "reaction": "supported", "edit": "unsupported"}},
}


def _error(status, code, message=""):
    return httpx.Response(
        status,
        json={"schema_version": "intake.error.v1",
              "error": {"code": code, "message": message}},
    )


def _make_transport(*, files=None, feed_pages=None, token=None,
                    receipt_status=200, seen=None):
    """feed_pages: list of package-list docs keyed by `after` value."""
    files = files or {}
    feed_pages = feed_pages or {}
    ocr_requests = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        if token is not None:
            if request.headers.get("authorization") != f"Bearer {token}":
                return _error(401, "unauthorized", "bad bearer")
        path = request.url.path
        if path == "/intake/v1/status":
            return httpx.Response(200, json=STATUS_DOC)
        if path == "/intake/v1/packages" and request.method == "GET":
            after = int(request.url.params.get("after", "0"))
            doc = feed_pages.get(after) or feed_pages.get("*") or {
                "schema_version": "intake.package-list.v1",
                "packages": [], "next_after": after,
                "until_sequence": 0, "has_more": False,
            }
            return httpx.Response(200, json=doc)
        if path.startswith("/intake/v1/packages/") and request.method == "GET":
            name = path.rsplit("/", 1)[1]
            data = files.get(name)
            if data is None:
                return _error(404, "package_unknown", f"no such file {name}")
            return httpx.Response(200, content=data)
        if path == "/intake/v1/receipts" and request.method == "POST":
            if receipt_status != 200:
                return _error(receipt_status, "http_error", "receipt endpoint down")
            return httpx.Response(200, json=json.loads(request.content))
        if path == "/intake/v1/ocr-requests" and request.method == "POST":
            body = json.loads(request.content)
            stored = ocr_requests.get(body["request_id"])
            if stored is None:
                stored = {
                    "schema_version": "intake.ocr-request-status.v1",
                    "request_id": body["request_id"],
                    "job_id": "f0000000-0000-4000-8000-000000000001",
                    "state": "queued", "attempt": 0, "max_attempts": 3,
                }
                ocr_requests[body["request_id"]] = stored
            return httpx.Response(200, json=stored)
        if path.startswith("/intake/v1/ocr-requests/") and request.method == "GET":
            rid = path.rsplit("/", 1)[1]
            doc = ocr_requests.get(rid)
            if doc is None:
                return _error(404, "package_unknown", "unknown request")
            return httpx.Response(200, json=doc)
        return _error(404, "package_unknown", f"no route {path}")

    return httpx.MockTransport(handler)


def _client(transport, **kwargs):
    return IntakeClient("http://module.test", transport=transport, **kwargs)


# ---------------------------------------------------------------------------


def test_service_status_returns_document():
    client = _client(_make_transport())
    doc = client.service_status()
    assert doc["schema_version"] == "intake.service-status.v1"
    assert doc["listener"]["state"] == "connected"


def test_list_packages_params_and_parsed_entries():
    seen = []
    feed = {0: {
        "schema_version": "intake.package-list.v1",
        "packages": [{"package_id": PACKAGE_ID, "sequence": 4,
                      "manifest_sha256": MANIFEST_SHA}],
        "next_after": 4, "until_sequence": 7, "has_more": False,
    }}
    client = _client(_make_transport(feed_pages=feed, seen=seen))
    doc = client.list_packages()
    assert doc["packages"][0]["package_id"] == PACKAGE_ID
    req = seen[-1]
    params = req.url.params
    assert params["delivery"] == "pending"
    assert params["after"] == "0"
    assert params["limit"] == str(MAX_PAGE_LIMIT)   # 200 default clamps to 100
    assert "until_sequence" not in params            # first page omits it


def test_list_packages_passes_cursor_and_until_sequence():
    seen = []
    client = _client(_make_transport(seen=seen))
    client.list_packages(after_sequence=5, until_sequence=9)
    params = seen[-1].url.params
    assert params["after"] == "5"
    assert params["until_sequence"] == "9"


def test_fetch_bytes_contract_spelling():
    client = _client(_make_transport(files={"manifest": b'{"a": 1}'}))
    assert client.fetch_bytes(PACKAGE_ID, "manifest") == b'{"a": 1}'


def test_fetch_bytes_falls_back_to_file_spelling():
    seen = []
    client = _client(_make_transport(files={"READY.json": b"{}"}, seen=seen))
    assert client.fetch_bytes(PACKAGE_ID, "ready") == b"{}"
    names = [r.url.path.rsplit("/", 1)[1] for r in seen]
    assert names == ["ready", "READY.json"]          # contract name first


def test_fetch_bytes_404_raises_after_both_spellings():
    client = _client(_make_transport())
    with pytest.raises(IntakeClientError) as exc:
        client.fetch_bytes(PACKAGE_ID, "records")
    assert exc.value.code == "package_unknown"
    assert exc.value.status == 404


def test_fetch_bytes_never_fetches_other_names():
    seen = []
    client = _client(_make_transport(seen=seen))
    for bad in ("images", "photo.jpg", "image", "thumb", "../x", "receipt"):
        with pytest.raises(ValueError):
            client.fetch_bytes(PACKAGE_ID, bad)
    assert seen == []                                 # zero HTTP attempted


def test_send_receipt_round_trip():
    receipt = {
        "schema_version": "intake.receipt.v1",
        "receipt_id": "e0000000-0000-4000-8000-000000000001",
        "package_id": PACKAGE_ID, "consumer_id": CONSUMER_ID,
        "status": "accepted", "received_at": "2026-09-24T08:05:00+07:00",
        "manifest_sha256": MANIFEST_SHA, "record_count": 2,
    }
    client = _client(_make_transport())
    assert client.send_receipt(receipt) == receipt


def test_ocr_request_create_and_get():
    body = {
        "schema_version": "intake.ocr-request.v1",
        "request_id": REQUEST_ID, "consumer_id": CONSUMER_ID,
        "logical_id": "b0000000-0000-4000-8000-000000000001",
        "variant": "rotate", "reason_code": "suspected_rotation",
        "observed_revision": 1, "submitted_at": "2026-09-24T08:05:00+07:00",
    }
    client = _client(_make_transport())
    doc = client.create_ocr_request(body)
    assert doc["state"] == "queued"
    assert doc["request_id"] == REQUEST_ID
    assert client.get_ocr_request(REQUEST_ID) == doc


def test_error_envelope_becomes_intake_client_error():
    client = _client(_make_transport(receipt_status=503))
    with pytest.raises(IntakeClientError) as exc:
        client.send_receipt({})
    assert exc.value.code == "http_error"
    assert exc.value.status == 503


def test_unauthorized_envelope_maps_code():
    def handler(request):
        return _error(401, "unauthorized", "bearer token mismatch")
    client = _client(httpx.MockTransport(handler))
    with pytest.raises(IntakeClientError) as exc:
        client.service_status()
    assert exc.value.code == "unauthorized"


def test_bearer_header_only_when_token_set():
    seen = []
    _client(_make_transport(token="sekret", seen=seen), token="sekret").service_status()
    assert seen[-1].headers["authorization"] == "Bearer sekret"

    seen.clear()
    _client(_make_transport(seen=seen)).service_status()
    assert "authorization" not in seen[-1].headers


def test_non_json_response_is_invalid_response():
    def handler(request):
        return httpx.Response(200, content=b"<html>oops</html>")
    client = _client(httpx.MockTransport(handler))
    with pytest.raises(IntakeClientError) as exc:
        client.service_status()
    assert exc.value.code == "invalid_response"
