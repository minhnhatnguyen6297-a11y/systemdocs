"""MIN-95 implements the variant re-run pipeline. Boundary only."""

# Contract §9.2 variant enum — shared with api/ocr_requests validation.
VARIANTS = {"crop_bottom", "rotate", "full_res"}


def run_ocr_variant(logical_id: str, variant: str, preset: str | None):
    """nội bộ bot — MIN-97 chỉ gọi từ job đã duyệt (plan §3.1)."""
    raise NotImplementedError("MIN-95")
