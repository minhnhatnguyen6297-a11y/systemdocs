"""Website provider registry — contract upload.workflow.v1 §4/§6.1.

Danh muc production chi co `nam_dinh`. Website gia chi duoc inject qua mot
`WebsiteRegistry` rieng trong test — `DEFAULT_REGISTRY` khong bao gio nhan
provider gia. Frontend/sidecar doc catalog qua `list_websites()` va resolve
bo xu ly qua `get_provider(website_id)`; website chua dang ky bi tu choi
(`unknown_website`), khong quay ve nam_dinh ngam.
"""
from __future__ import annotations

import re
from pathlib import Path

WEBSITE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
WEBSITES_DIR_NAME = "websites"

# Layout du lieu mot website trong data root (plan §3.2). Thu muc con nay la
# working_dir cua engine: registry.sqlite3/output/runs/downloads/upload_runs/
# nd_storage_state.json/uploader_staff_options.json/logs.
WEBSITE_SUBDIRS = ("output", "runs", "downloads", "upload_runs", "logs")
WEBSITE_STATE_FILES = (
    "nd_storage_state.json",
    "uploader_staff_options.json",
    "registry.sqlite3",
)


class UnknownWebsiteError(Exception):
    """website_id khong co trong registry → error code `unknown_website`."""

    code = "unknown_website"

    def __init__(self, website_id):
        self.website_id = website_id
        super().__init__(f"website chua dang ky: {website_id!r}")


class ProviderDataDirError(Exception):
    """data_dir khong phai vung du lieu cua website nay."""

    code = "website_mismatch"

    def __init__(self, website_id, data_dir):
        self.website_id = website_id
        self.data_dir = data_dir
        super().__init__(
            f"data_dir {data_dir} khong thuoc website {website_id!r}")


class WebsiteProvider:
    """Adapter mong toi engine upload_lab cho mot website cu the.

    Lop con dinh nghia `website_id`/`label`/`display_url`/`capabilities` va
    override `create_browser()`/`audit_excel()`. Cac helper data_dir/layout
    dung chung theo contract §3.2 — moi website mot thu muc rieng duoi
    `<data_root>/websites/<website_id>/`.
    """

    def __init__(self, *, website_id, label, display_url,
                 capabilities, status="available"):
        if not WEBSITE_ID_RE.match(str(website_id or "")):
            raise ValueError(f"website_id khong hop le: {website_id!r}")
        self.website_id = website_id
        self.label = label
        self.display_url = display_url
        self.capabilities = tuple(capabilities)
        self.status = status

    # ---------- catalog ----------

    def catalog_entry(self):
        """Entry JSON-safe cho `upload.websites` (contract §6.1)."""
        return {
            "website_id": self.website_id,
            "label": self.label,
            "display_url": self.display_url,
            "capabilities": list(self.capabilities),
            "status": self.status,
        }

    # ---------- vung du lieu ----------

    def website_data_dir(self, data_root) -> Path:
        """`<data_root>/websites/<website_id>` — chua tao tren dia."""
        return Path(data_root) / WEBSITES_DIR_NAME / self.website_id

    def assert_data_dir(self, data_dir) -> Path:
        """Kiem tra data_dir da resolve dung vung cua website nay.

        Bat buoc dang `.../websites/<website_id>` — tranh ghi nham du lieu
        website khac khi caller truyen nham path.
        """
        resolved = Path(data_dir).resolve()
        if resolved.name != self.website_id \
                or resolved.parent.name != WEBSITES_DIR_NAME:
            raise ProviderDataDirError(self.website_id, resolved)
        return resolved

    def ensure_data_layout(self, data_dir) -> Path:
        """assert + tao cac thu muc con chuan; tra Path da resolve."""
        resolved = self.assert_data_dir(data_dir)
        for sub in WEBSITE_SUBDIRS:
            (resolved / sub).mkdir(parents=True, exist_ok=True)
        return resolved

    # ---------- engine hooks (lop con override) ----------

    def create_browser(self, data_dir):
        """Tao browser/engine session ghi du lieu trong data_dir."""
        raise NotImplementedError

    def audit_excel(self, path, *, from_date, to_date):
        """Audit so cong chung Excel → cau truc chung cua engine."""
        raise NotImplementedError

    def public_config(self, data_dir) -> dict:
        """Gia tri cong khai trong schema cho UI — khong dump .env."""
        raise NotImplementedError

    def load_staff_options_cache(self, data_dir) -> dict:
        raise NotImplementedError


class WebsiteRegistry:
    """Tap website theo thu tu dang ky. Production dung DEFAULT_REGISTRY;
    test tu tao instance rieng de inject provider gia."""

    def __init__(self):
        self._providers = {}

    def register(self, provider: WebsiteProvider):
        if not isinstance(provider, WebsiteProvider):
            raise TypeError("provider phai la WebsiteProvider")
        if provider.website_id in self._providers:
            raise ValueError(f"website da dang ky: {provider.website_id}")
        self._providers[provider.website_id] = provider
        return provider

    def is_known(self, website_id) -> bool:
        return website_id in self._providers

    def get_provider(self, website_id) -> WebsiteProvider:
        if not isinstance(website_id, str) \
                or not WEBSITE_ID_RE.match(website_id):
            raise UnknownWebsiteError(website_id)
        provider = self._providers.get(website_id)
        if provider is None:
            raise UnknownWebsiteError(website_id)
        return provider

    def list_websites(self) -> list[dict]:
        return [p.catalog_entry() for p in self._providers.values()]

    def website_ids(self) -> list[str]:
        return list(self._providers)


DEFAULT_REGISTRY = WebsiteRegistry()


def register_default(provider: WebsiteProvider):
    return DEFAULT_REGISTRY.register(provider)


def list_websites() -> list[dict]:
    """Catalog cong khai (contract §6.1) — chi website that."""
    return DEFAULT_REGISTRY.list_websites()


def get_provider(website_id) -> WebsiteProvider:
    return DEFAULT_REGISTRY.get_provider(website_id)


def is_known_website(website_id) -> bool:
    return DEFAULT_REGISTRY.is_known(website_id)


def validate_website_id(website_id) -> str:
    """Chuan hoa + kiem tra da dang ky; raise UnknownWebsiteError."""
    return DEFAULT_REGISTRY.get_provider(website_id).website_id
