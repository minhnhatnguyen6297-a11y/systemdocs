"""Access audit — append-only JSONL for every runtime file/dir the module opens.

cli/app calls `configure` once at startup. `record_access` is a no-op until
configured — importing this module never writes anything.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

_access_log: Path | None = None


def configure(path: Path) -> None:
    """Point the access log at `path` (normally runtime_root/access.jsonl)."""
    global _access_log
    _access_log = path


def record_access(path: Path, kind: str) -> None:
    """Append {"path": str(resolved), "kind": kind, "at": iso8601} to the log.

    kind ∈ {"db", "media", "package", "outbox", "journal", "runtime"}.
    No-op when `configure` has not been called.
    """
    if _access_log is None:
        return
    resolved = path.resolve()
    _access_log.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "path": str(resolved),
        "kind": kind,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    with _access_log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
