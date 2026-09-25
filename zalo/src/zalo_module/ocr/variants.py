"""Closed variant/preset matrix for OCR re-run requests — contract §9.2.

One request = one variant; the preset space is sealed (no free-form region,
angle, or prompt). ``normalize_preset`` validates the (variant, preset) pair
and returns the canonical preset value stored/compared downstream:

- ``rotate``      → ``"auto"`` | ``None`` (provider ``enable_rotate=true``)
- ``crop_bottom`` → one of ``bottom_quarter`` | ``bottom_third`` | ``bottom_42pct``
- ``full_res``    → ``None`` only

``ValueError`` messages carry the contract error code first
(``unsupported_variant`` / ``missing_preset``) so callers can map them.
"""
from __future__ import annotations

# Contract §9.2 variant enum — shared with api/ocr_requests validation.
VARIANTS = {"crop_bottom", "rotate", "full_res"}

# crop_bottom preset → region fraction (bottom part of the page kept).
# Contract §9.2: bottom_quarter ≈ 0.25, bottom_third ≈ 1/3, bottom_42pct ≈ 0.42.
CROP_FRACTIONS = {
    "bottom_quarter": 0.25,
    "bottom_third": 1.0 / 3.0,
    "bottom_42pct": 0.42,
}

ROTATE_PRESETS = {"auto", None}
_FRACTION_TOLERANCE = 1e-6


def normalize_preset(variant: str, preset) -> str | None:
    """Validate ``(variant, preset)``; return the canonical preset value.

    Raises ``ValueError("unsupported_variant: ...")`` or
    ``ValueError("missing_preset: ...")`` matching contract §9.2 codes.
    """
    if variant not in VARIANTS:
        raise ValueError(f"unsupported_variant: unknown variant {variant!r}")
    if variant == "crop_bottom":
        if preset is None:
            raise ValueError("missing_preset: crop_bottom requires a preset")
        if preset not in CROP_FRACTIONS:
            raise ValueError(
                f"unsupported_variant: unknown crop_bottom preset {preset!r}"
            )
        return preset
    if variant == "rotate":
        if preset not in ROTATE_PRESETS:
            raise ValueError(
                "unsupported_variant: rotate preset must be 'auto' or null"
            )
        return "auto" if preset == "auto" else None
    # full_res
    if preset is not None:
        raise ValueError("unsupported_variant: full_res takes no preset")
    return None


def crop_fraction(preset: str) -> float:
    """Return the bottom fraction for a validated crop preset."""
    return CROP_FRACTIONS[preset]


def preset_for_fraction(fraction) -> str | None:
    """Inverse of ``crop_fraction`` for dedupe matching; None when not equal
    to a closed preset within tolerance."""
    if not isinstance(fraction, (int, float)) or isinstance(fraction, bool):
        return None
    for preset, value in CROP_FRACTIONS.items():
        if abs(float(fraction) - value) <= _FRACTION_TOLERANCE:
            return preset
    return None
