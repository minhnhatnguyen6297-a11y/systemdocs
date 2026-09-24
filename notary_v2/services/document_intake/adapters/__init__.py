"""Per-kind intake source adapters.

Mỗi adapter nhận (SourceSpec, AdapterContext) → list[dict] suggestions
(contract shape) hoặc raise SourceFailed(code, message) cho lỗi per-source —
kể cả limit chỉ phát hiện được khi mở file (PDF > 50 trang, file thật > 20MB)
cũng là per-source error, không hủy các nguồn khác trong batch.
"""

from __future__ import annotations

from ..models import IntakeCancelled


def check_cancel(ctx) -> None:
    """Gọi job.check_cancel() của caller; wrap mọi exception thành
    IntakeCancelled để service re-raise đúng bản gốc, không nuốt vào
    per-source error."""
    fn = getattr(ctx, "check_cancel", None)
    if fn is None:
        return
    try:
        fn()
    except IntakeCancelled:
        raise
    except Exception as exc:  # CancelledByUser hoặc tương đương
        raise IntakeCancelled(exc) from exc
