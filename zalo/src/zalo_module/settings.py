"""Runtime settings for the Zalo intake module.

`get_settings(env)` reads `os.environ` when `env is None`; tests pass a dict.
Creating the runtime directory tree (runtime_root + media/, packages/,
outbox/, connector/) is the ONLY side effect of loading settings.

MIN-103 slice B added the connector/engine fields (decision sheet §7). The
``ZALO_INBOX_*`` / ``ZALO_CONNECTOR_*`` / ``ZALO_DATA_SYNC_TIMEOUT_SECONDS``
env names are the wire contract with the connector subprocess and stay
verbatim — renaming is deferred to MIN-94.
"""

import math
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONNECTOR_QUOTA_BYTES = 5 << 30      # 5 GiB
DEFAULT_CONNECTOR_RETENTION_HOURS = 168.0    # 7 days
DEFAULT_DATA_SYNC_TIMEOUT_SECONDS = 900      # 15 minutes


@dataclass(frozen=True)
class Settings:
    runtime_root: Path          # ZALO_INTAKE_RUNTIME_DIR, default ./runtime
    db_url: str                 # ZALO_INTAKE_DB_URL, default sqlite:///{runtime_root}/zalo_intake.db
    consumer_id: str | None     # ZALO_INTAKE_CONSUMER_ID (uuid) — serve requires it
    bind: str                   # ZALO_INTAKE_BIND, default 127.0.0.1
    port: int                   # ZALO_INTAKE_PORT, default 8790
    qwen_api_base: str          # QWEN_API_BASE, default https://dashscope-intl.aliyuncs.com
    qwen_model: str             # QWEN_MODEL, default qwen-vl-ocr-2025-11-20
    qwen_api_key: str | None    # QWEN_API_KEY — None when unset; NO default
    account_id: str | None      # ZALO_ACCOUNT_ID (uuid) — None before login
    ocr_config_version: str     # OCR_CONFIG_VERSION, default "ocr-config-v1"
    access_log_path: Path       # runtime_root/access.jsonl — audit
    # -- MIN-103 connector/engine fields (sheet §7) --------------------------
    # Defaults keep direct ``Settings(**kwargs)`` construction working for
    # tests that don't exercise the connector surface.
    api_token: str | None = None          # ZALO_INTAKE_API_TOKEN — Bearer /intake/v1
    webhook_secret: str | None = None     # ZALO_INBOX_WEBHOOK_SECRET
    bootstrap_secret: str | None = None   # ZALO_INBOX_BOOTSTRAP_SECRET
    connector_state_root: Path | None = None  # ZALO_CONNECTOR_STATE_ROOT
    connector_quota_bytes: int = DEFAULT_CONNECTOR_QUOTA_BYTES
    connector_retention_hours: float = DEFAULT_CONNECTOR_RETENTION_HOURS
    data_sync_timeout_seconds: int = DEFAULT_DATA_SYNC_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        # Frozen dataclass: derive the default connector root from
        # runtime_root when the field was not supplied.
        if self.connector_state_root is None:
            object.__setattr__(
                self,
                "connector_state_root",
                Path(self.runtime_root) / "connector",
            )


def _positive_int(env: dict[str, str], name: str, default: int) -> int:
    raw = env.get(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        value = int(str(raw).strip())
    except ValueError as exc:
        raise ValueError(f"{name} phải là số nguyên dương") from exc
    if value <= 0:
        raise ValueError(f"{name} phải là số nguyên dương")
    return value


def _connector_quota(env: dict[str, str]) -> int:
    value = _positive_int(
        env, "ZALO_CONNECTOR_QUOTA_BYTES", DEFAULT_CONNECTOR_QUOTA_BYTES
    )
    if value > 2**53 - 1:
        raise ValueError("ZALO_CONNECTOR_QUOTA_BYTES không hợp lệ")
    return value


def _connector_retention(env: dict[str, str]) -> float:
    raw = env.get("ZALO_CONNECTOR_RETENTION_HOURS")
    if raw is None or not str(raw).strip():
        return DEFAULT_CONNECTOR_RETENTION_HOURS
    try:
        value = float(str(raw).strip())
    except ValueError as exc:
        raise ValueError(
            "ZALO_CONNECTOR_RETENTION_HOURS không hợp lệ"
        ) from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError("ZALO_CONNECTOR_RETENTION_HOURS không hợp lệ")
    return value


def get_settings(env: dict[str, str] | None = None) -> Settings:
    """Load settings. `env` replaces os.environ entirely when given."""
    e = os.environ if env is None else env
    runtime_root = Path(e.get("ZALO_INTAKE_RUNTIME_DIR", "./runtime"))
    db_url = e.get("ZALO_INTAKE_DB_URL") or (
        f"sqlite:///{runtime_root.as_posix()}/zalo_intake.db"
    )
    settings = Settings(
        runtime_root=runtime_root,
        db_url=db_url,
        consumer_id=e.get("ZALO_INTAKE_CONSUMER_ID") or None,
        bind=e.get("ZALO_INTAKE_BIND", "127.0.0.1"),
        port=int(e.get("ZALO_INTAKE_PORT", "8790")),
        qwen_api_base=e.get(
            "QWEN_API_BASE", "https://dashscope-intl.aliyuncs.com"
        ),
        qwen_model=e.get("QWEN_MODEL", "qwen-vl-ocr-2025-11-20"),
        qwen_api_key=e.get("QWEN_API_KEY") or None,
        account_id=e.get("ZALO_ACCOUNT_ID") or None,
        ocr_config_version=e.get("OCR_CONFIG_VERSION", "ocr-config-v1"),
        api_token=e.get("ZALO_INTAKE_API_TOKEN") or None,
        access_log_path=runtime_root / "access.jsonl",
        webhook_secret=e.get("ZALO_INBOX_WEBHOOK_SECRET") or None,
        bootstrap_secret=e.get("ZALO_INBOX_BOOTSTRAP_SECRET") or None,
        connector_state_root=Path(
            e.get("ZALO_CONNECTOR_STATE_ROOT")
            or runtime_root / "connector"
        ),
        connector_quota_bytes=_connector_quota(e),
        connector_retention_hours=_connector_retention(e),
        data_sync_timeout_seconds=_positive_int(
            e, "ZALO_DATA_SYNC_TIMEOUT_SECONDS",
            DEFAULT_DATA_SYNC_TIMEOUT_SECONDS,
        ),
    )
    # mkdir is the only side effect of settings.
    for sub in (
        settings.runtime_root,
        settings.runtime_root / "media",
        settings.runtime_root / "packages",
        settings.runtime_root / "outbox",
        settings.connector_state_root,
    ):
        sub.mkdir(parents=True, exist_ok=True)
    return settings
