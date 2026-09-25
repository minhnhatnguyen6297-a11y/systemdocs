"""Sync httpx client for the Zalo module's ``/intake/v1`` surface.

Contract SOT: ``contracts/zalo-intake/zalo-intake.md`` §7 (pending feed +
receipts), §9 (OCR requests), §10 (status + error envelope). Endpoint shapes
verified against the producer implementation
(``zalo-intake/src/zalo_module/api/intake.py``):

    GET /intake/v1/status                              → intake.service-status.v1 (open)
    GET /intake/v1/packages?delivery=pending&after=&until_sequence=&limit=
                                                       → intake.package-list.v1
    GET /intake/v1/packages/{package_id}/{name}        → raw bytes; name is a
        logical spelling (manifest|records|ready) or the file spelling
        (manifest.json|records.jsonl|READY.json)
    POST /intake/v1/receipts                           → intake.receipt.v1
    POST /intake/v1/ocr-requests                       → intake.ocr-request-status.v1
    GET  /intake/v1/ocr-requests/{request_id}          → intake.ocr-request-status.v1

Consumer identity travels in the Bearer token (``ZALO_INTAKE_API_TOKEN``);
there is NO ``consumer_id`` query param — the module authenticates the
consumer and scopes the pending feed server-side. Every non-2xx body is the
``intake.error.v1`` envelope; it is raised as :class:`IntakeClientError`.

Image bytes are never fetched: :meth:`fetch_bytes` only accepts the three
package logical names and raises ``ValueError`` for anything else.
"""
from __future__ import annotations

import json

import httpx

_ERROR_SCHEMA = "intake.error.v1"

# Logical package-file names (contract §7.2) → file-spelling fallbacks the
# module also routes. No other name may ever be requested.
_FETCH_NAMES = {
    "manifest": ("manifest", "manifest.json"),
    "records": ("records", "records.jsonl"),
    "ready": ("ready", "READY.json"),
}

# Contract §7.2/§3.6: package-list pages are capped at 100 entries.
MAX_PAGE_LIMIT = 100


class IntakeClientError(Exception):
    """An ``intake.error.v1`` envelope (or an unroutable request) from the module.

    ``code`` is the contract §11 error code when the module sent an envelope
    (e.g. ``package_unknown``, ``unauthorized``), ``"http_error"`` for a
    non-envelope HTTP failure, or ``"invalid_response"`` when a 2xx body did
    not parse as expected.
    """

    def __init__(self, code: str, message: str, *, status: int | None = None,
                 retryable: bool | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.status = status
        self.retryable = retryable


def _error_from_response(response: httpx.Response) -> IntakeClientError:
    try:
        body = response.json()
    except (json.JSONDecodeError, ValueError):
        body = None
    if isinstance(body, dict) and body.get("schema_version") == _ERROR_SCHEMA \
            and isinstance(body.get("error"), dict):
        err = body["error"]
        return IntakeClientError(
            str(err.get("code") or "unknown_error"),
            str(err.get("message") or response.reason_phrase or ""),
            status=response.status_code,
            retryable=err.get("retryable") if isinstance(err.get("retryable"), bool) else None,
        )
    return IntakeClientError(
        "http_error",
        f"HTTP {response.status_code} without intake.error.v1 envelope",
        status=response.status_code,
    )


class IntakeClient:
    """Synchronous client for the module API. Holds one ``httpx.Client``."""

    def __init__(self, base_url: str, token: str | None = None,
                 timeout: float = 30, transport: httpx.BaseTransport | None = None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeout,
            transport=transport,
        )

    # -- plumbing -----------------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "IntakeClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.HTTPError as e:
            raise IntakeClientError("http_error", str(e)) from e
        if response.is_error:
            raise _error_from_response(response)
        return response

    def _json(self, method: str, path: str, **kwargs):
        response = self._request(method, path, **kwargs)
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError) as e:
            raise IntakeClientError(
                "invalid_response",
                f"{method} {path}: response is not JSON ({e})",
                status=response.status_code,
            ) from e

    # -- endpoints ------------------------------------------------------------

    def service_status(self) -> dict:
        """GET /intake/v1/status → intake.service-status.v1 document."""
        return self._json("GET", "/intake/v1/status")

    def list_packages(self, after_sequence: int | None = None, *,
                      until_sequence: int | None = None,
                      limit: int = 200) -> dict:
        """GET /intake/v1/packages → parsed intake.package-list.v1 document.

        ``after_sequence`` maps to the contract ``after`` cursor (pagination
        only, never an ACK). ``until_sequence`` is omitted on the first page
        so the producer pins the high-water mark (contract §7.2); subsequent
        pages pass the value the first response returned. ``limit`` is
        clamped to the contract page cap of 100.
        """
        params = {"delivery": "pending", "after": after_sequence or 0,
                  "limit": max(1, min(limit, MAX_PAGE_LIMIT))}
        if until_sequence is not None:
            params["until_sequence"] = until_sequence
        doc = self._json("GET", "/intake/v1/packages", params=params)
        if not isinstance(doc, dict) or not isinstance(doc.get("packages"), list):
            raise IntakeClientError(
                "invalid_response",
                "GET /intake/v1/packages: not an intake.package-list.v1 document",
            )
        return doc

    def fetch_bytes(self, package_id: str, logical_name: str) -> bytes:
        """GET /intake/v1/packages/{id}/{name} → raw file bytes.

        ``logical_name`` must be one of ``manifest`` | ``records`` | ``ready``
        (the three package files — nothing else, ever). The contract spelling
        is tried first, the on-disk file spelling second (the module routes
        both). A 404 on the contract spelling falls back to the file
        spelling; other errors propagate.
        """
        spellings = _FETCH_NAMES.get(logical_name)
        if spellings is None:
            raise ValueError(
                f"fetch_bytes only serves {sorted(_FETCH_NAMES)} (got {logical_name!r}); "
                "image/file names are never fetched"
            )
        first_error = None
        for name in spellings:
            try:
                return self._request(
                    "GET", f"/intake/v1/packages/{package_id}/{name}"
                ).content
            except IntakeClientError as e:
                if e.status == 404 and first_error is None:
                    first_error = e
                    continue
                raise
        raise first_error

    def send_receipt(self, receipt: dict) -> dict:
        """POST /intake/v1/receipts → stored intake.receipt.v1 document."""
        return self._json("POST", "/intake/v1/receipts", json=receipt)

    def create_ocr_request(self, body: dict) -> dict:
        """POST /intake/v1/ocr-requests → intake.ocr-request-status.v1."""
        return self._json("POST", "/intake/v1/ocr-requests", json=body)

    def get_ocr_request(self, request_id: str) -> dict:
        """GET /intake/v1/ocr-requests/{request_id} → intake.ocr-request-status.v1."""
        return self._json("GET", f"/intake/v1/ocr-requests/{request_id}")
