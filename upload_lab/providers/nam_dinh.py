"""Provider Nam Dinh — adapter mong toi engine upload_lab hien co.

Khong viet lai business logic: moi ham goi thang vao playwright_uploader /
batch_scan / ui.services.* voi `working_dir`/`base_dir` la data_dir cua
website. Chi co mot provider that trong catalog production.
"""
from __future__ import annotations

from pathlib import Path

try:
    from providers.registry import (
        WebsiteProvider,
        register_default,
    )
except ImportError:  # pragma: no cover — import kieu package upload_lab.providers
    from .registry import (
        WebsiteProvider,
        register_default,
    )

NAM_DINH_WEBSITE_ID = "nam_dinh"
NAM_DINH_LABEL = "Nam Định"
NAM_DINH_DISPLAY_URL = "https://congchungnamdinh.ninhbinh.gov.vn"
NAM_DINH_CAPABILITIES = (
    "login",
    "download_export",
    "audit_excel",
    "scan",
    "prepare",
    "staff_options",
    "reconcile",
)

# Khoa .env cong khai theo schema — khong bao gio tra toan bo .env cho UI.
_PUBLIC_CONFIG_KEYS = (
    "base_url",
    "browser_channel",
    "max_prepared_tabs",
    "storage_state_exists",
    "env_exists",
)


class NamDinhProvider(WebsiteProvider):
    """Bo xu ly website congchungnamdinh.ninhbinh.gov.vn."""

    def __init__(self):
        super().__init__(
            website_id=NAM_DINH_WEBSITE_ID,
            label=NAM_DINH_LABEL,
            display_url=NAM_DINH_DISPLAY_URL,
            capabilities=NAM_DINH_CAPABILITIES,
            status="available",
        )

    # ---------- engine glue ----------

    def load_settings(self, data_dir):
        """UploaderSettings doc .env trong data_dir cua website."""
        from playwright_uploader import load_uploader_settings
        return load_uploader_settings(self.assert_data_dir(data_dir))

    def create_browser(self, data_dir):
        """NamDinhUploaderSession voi working_dir = data_dir cua website.

        Tao object session thoi — Playwright/browser mo lazy ben trong
        engine khi co thao tac dau tien (khong launch o day).
        """
        from playwright_uploader import NamDinhUploaderSession
        resolved = self.ensure_data_layout(data_dir)
        settings = self.load_settings(resolved)
        return NamDinhUploaderSession(settings, working_dir=resolved)

    def audit_excel(self, path, *, from_date, to_date):
        """analyze_contract_book that → ContractBookAnalysis (cau truc
        chung ma scan_classification_service/folder_workflow_service dung)."""
        from ui.services.contract_book_audit import analyze_contract_book
        return analyze_contract_book(
            Path(path), from_date=from_date, to_date=to_date)

    def env_check(self, data_dir):
        """Checklist moi truong that cua engine, scoped data_dir website."""
        from ui.services.environment_check_service import (
            run_environment_checks)
        resolved = self.assert_data_dir(data_dir)
        settings = self.load_settings(resolved)
        return run_environment_checks(resolved, settings.base_url)

    def run_scan(self, folder_path, data_dir, *, modified_since=None,
                 full_rescan=False, progress_callback=None):
        """run_folder_scan that — manifest ghi vao data_dir/runs."""
        from ui.services.folder_workflow_service import run_folder_scan
        resolved = self.ensure_data_layout(data_dir)
        return run_folder_scan(
            Path(folder_path),
            modified_since=modified_since,
            full_rescan=full_rescan,
            progress_callback=progress_callback,
            working_dir=resolved)

    def connect_registry(self, data_dir):
        """sqlite3.Connection toi registry.sqlite3 CUA website nay."""
        from batch_scan import connect_registry
        resolved = self.assert_data_dir(data_dir)
        return connect_registry(resolved / "registry.sqlite3")

    # ---------- cau hinh cong khai / nhan su ----------

    def public_config(self, data_dir) -> dict:
        """Chi cac gia tri cong khai trong schema cho UI.

        Khong tra .env nguyen ban: storage_state_path/cookie/session khong
        bao gio di ra; chi base_url/channel/max_prepared_tabs + co hieu.
        """
        from playwright_uploader import (
            _resolve_tool_relative_path,
            read_uploader_env,
        )
        resolved = self.assert_data_dir(data_dir)
        values = read_uploader_env(resolved)
        settings = self.load_settings(resolved)
        storage_state = _resolve_tool_relative_path(
            resolved,
            values.get("ND_STORAGE_STATE_PATH", ""),
            default_name="nd_storage_state.json",
        )
        return {
            "website_id": self.website_id,
            "base_url": settings.base_url,
            "browser_channel": settings.browser_channel,
            "max_prepared_tabs": settings.max_prepared_tabs,
            "storage_state_exists": storage_state.exists(),
            "env_exists": (resolved / ".env").is_file(),
        }

    def save_chunk_size(self, data_dir, chunk_size: int) -> Path:
        """Dong bo so tab/dot vao .env cua website (engine-native store).

        `upload.preferences` luu o workspace store; ham nay giu engine
        doc duoc cung gia tri khi prepare chay.
        """
        from playwright_uploader import update_uploader_env
        resolved = self.assert_data_dir(data_dir)
        value = max(1, min(int(chunk_size), 30))
        return update_uploader_env(
            {"ND_MAX_PREPARED_TABS": str(value)}, base_dir=resolved)

    def load_staff_options_cache(self, data_dir) -> dict:
        from playwright_uploader import NamDinhUploaderSession
        resolved = self.assert_data_dir(data_dir)
        return NamDinhUploaderSession.load_staff_options_cache(resolved)


register_default(NamDinhProvider())
