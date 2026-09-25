"""Connector-facing authentication helpers (MIN-103 slice B).

Ported from ``notary_v2/services/zalo_inbox.py`` (verify_webhook_signature)
and ``notary_v2/routers/zalo_inbox.py`` (derived command key). Pure module —
no FastAPI imports; raises :class:`InboxValidationError` so ``api/`` can map
failures onto the module error envelope.

- Event posts: ``x-zalo-signature`` = HMAC-SHA256(webhook_secret,
  ``"{timestamp}.{body}"``) with a ±300 s replay window.
- ``GET .../config``: same signature over an *empty* body.
- ``GET .../commands/next``: the signing key is the derived per-account key
  ``HMAC-SHA256(webhook_secret, account_id).hexdigest()`` — the raw webhook
  secret is never accepted there.
"""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone

from zalo_module.intake.engine import InboxValidationError, _aware, utcnow

UTC = timezone.utc


def sign_body(body: bytes, timestamp: str, secret: str) -> str:
    """Return ``HMAC-SHA256(secret, "{timestamp}.{body}")`` as hex.

    Mirror of the connector's ``signBody`` (``connector/src/core.mjs``).
    """
    return hmac.new(
        secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256
    ).hexdigest()


def command_secret(webhook_secret: str, account_id: str) -> str:
    """Derived per-account key for ``commands/next``: HMAC(secret, account_id)."""
    return hmac.new(
        webhook_secret.encode(), account_id.encode(), hashlib.sha256
    ).hexdigest()


def verify_bootstrap_secret(provided: str | None, secret: str | None) -> bool:
    """Constant-time check of the ``x-zalo-bootstrap`` onboard header.

    False when the secret is unconfigured or the header is absent — onboard
    stays closed in both cases (legacy 403 parity).
    """
    if not secret or provided is None:
        return False
    return hmac.compare_digest(provided, secret)


def verify_webhook_signature(
    body: bytes,
    timestamp: str,
    signature: str,
    secret: str,
    *,
    now: datetime | None = None,
    replay_window_seconds: int = 300,
) -> None:
    """Verify ``{timestamp}.{body}`` HMAC + replay window; raise on failure."""
    if not secret:
        raise InboxValidationError("Webhook secret chưa được cấu hình")
    try:
        sent_at = datetime.fromtimestamp(int(timestamp), tz=UTC)
    except (TypeError, ValueError, OSError) as exc:
        raise InboxValidationError("Webhook timestamp không hợp lệ") from exc
    current = _aware(now) or utcnow()
    if abs((current - sent_at).total_seconds()) > replay_window_seconds:
        raise InboxValidationError("Webhook replay window đã hết")
    expected = sign_body(body, timestamp, secret)
    if not hmac.compare_digest(expected, signature or ""):
        raise InboxValidationError("Webhook signature không hợp lệ")
