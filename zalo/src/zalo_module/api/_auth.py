"""Consumer authentication for ``/intake/v1/*`` — contract §9.1/§10.2.

``require_consumer_auth`` is a FastAPI dependency applied to every consumer
endpoint **except** ``GET /intake/v1/status`` (the health contract stays
open so ops can probe liveness before configuring a token).

Policy (decision-sheet §4.1, contract §9.1):

- ``settings.api_token`` set → the request must carry
  ``Authorization: Bearer <token>`` else a 401 ``intake.error.v1`` body with
  ``error.code = "unauthorized"``.
- ``settings.api_token`` unset → allow. Loopback-as-auth: the documented
  deployment binds the API to 127.0.0.1/::1 only, so reachability *is* the
  auth boundary; running without a token off-loopback is a config error —
  ``cli serve`` warns on stderr (docs/delivery.md §auth).

The 401 body is produced by :class:`IntakeRoute`, an ``APIRoute`` subclass
installed as ``route_class`` on the intake routers — it turns the
internal :class:`ConsumerAuthError` into the contract error envelope so no
app-factory wiring is needed.
"""
from __future__ import annotations

import hmac

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from zalo_module.settings import get_settings


class ConsumerAuthError(Exception):
    """Raised inside request handling when consumer auth fails."""


def _settings(request: Request):
    return getattr(request.app.state, "settings", None) or get_settings()


def _unauthorized(detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "schema_version": "intake.error.v1",
            "error": {"code": "unauthorized", "message": detail},
        },
    )


class IntakeRoute(APIRoute):
    """Route class mapping :class:`ConsumerAuthError` → 401 error envelope."""

    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request: Request):
            try:
                return await original(request)
            except ConsumerAuthError as exc:
                return _unauthorized(str(exc) or "unauthorized")

        return handler


def require_consumer_auth(request: Request) -> None:
    """Dependency: enforce ``Authorization: Bearer <api_token>`` when set.

    With no configured token the module is expected to serve on loopback and
    the request is allowed through (loopback-as-auth, documented).
    """
    settings = _settings(request)
    token = getattr(settings, "api_token", None)
    if not token:
        return  # loopback-as-auth: no token configured by design
    header = request.headers.get("authorization") or ""
    scheme, _, credential = header.partition(" ")
    if scheme.lower() != "bearer" or not credential:
        raise ConsumerAuthError("missing bearer token")
    if not hmac.compare_digest(credential.strip(), token):
        raise ConsumerAuthError("bearer token mismatch")


def check_consumer_id(settings, consumer_id) -> JSONResponse | None:
    """Body-level consumer identity: ``consumer_id`` must equal the
    registered ``settings.consumer_id``. Returns the error response or None.

    Used by endpoints whose contract pins a body consumer_id check
    (``receipt_consumer_mismatch`` for receipts, ``unauthorized`` for OCR
    requests) — kept as a shared guard so the comparison stays constant-time.
    """
    registered = getattr(settings, "consumer_id", None)
    if not registered or consumer_id != registered:
        return JSONResponse(
            status_code=401,
            content={
                "schema_version": "intake.error.v1",
                "error": {
                    "code": "unauthorized",
                    "message": "consumer_id does not match the registered consumer",
                },
            },
        )
    return None
