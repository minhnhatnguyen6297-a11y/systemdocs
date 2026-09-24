"""Website providers — registry + adapter engine theo website (MIN-69).

Import `providers.nam_dinh` o day de dang ky website that vao
DEFAULT_REGISTRY mot lan duy nhat khi package duoc import.
"""
from .registry import (
    DEFAULT_REGISTRY,
    ProviderDataDirError,
    UnknownWebsiteError,
    WebsiteProvider,
    WebsiteRegistry,
    get_provider,
    is_known_website,
    list_websites,
    register_default,
    validate_website_id,
)
from . import nam_dinh  # noqa: F401 — side effect: register_default
from .nam_dinh import (
    NAM_DINH_CAPABILITIES,
    NAM_DINH_DISPLAY_URL,
    NAM_DINH_LABEL,
    NAM_DINH_WEBSITE_ID,
    NamDinhProvider,
)

__all__ = [
    "DEFAULT_REGISTRY",
    "NAM_DINH_CAPABILITIES",
    "NAM_DINH_DISPLAY_URL",
    "NAM_DINH_LABEL",
    "NAM_DINH_WEBSITE_ID",
    "NamDinhProvider",
    "ProviderDataDirError",
    "UnknownWebsiteError",
    "WebsiteProvider",
    "WebsiteRegistry",
    "get_provider",
    "is_known_website",
    "list_websites",
    "nam_dinh",
    "register_default",
    "validate_website_id",
]
