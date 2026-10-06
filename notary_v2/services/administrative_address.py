"""Read-only v2 administrative lookup over the administrative timeline ledger.

v2 (TASK-3): payload {query, presentation}; every clause is searched
independently against all communes and all provinces nationwide; each
matching source row is returned separately for the user to choose.
No dates, no auto-apply, no "(nay la ...)" suffix here.
Local-only: never sends customer addresses anywhere, never writes ledger.
"""
from __future__ import annotations

import json
import re
import threading
import unicodedata
from pathlib import Path

try:  # Engine services are imported as top-level modules in the packaged sidecar.
    import administrative_timeline as timeline
except ImportError:
    from notary_v2 import administrative_timeline as timeline


SCHEMA_VERSION = "notary.address-lookup.v2"
MAX_QUERY_LEN = 4000
DRAFTING_LIMIT = 10

# Longest first so "TP." / "TT." / "TX." win over "P." / "X.".
_ABBREV = (
    ("TT.", "Thị trấn"),
    ("TX.", "Thị xã"),
    ("TP.", "Thành phố"),
    ("TP", "Thành phố"),
    ("X.", "Xã"),
    ("P.", "Phường"),
    ("H.", "Huyện"),
    ("Q.", "Quận"),
)
_ABBREV_RX = re.compile(
    r"^\s*(TT\.|TX\.|TP\.?|X\.|P\.|H\.|Q\.)\s*(.*)$", re.I | re.S,
)
_ABBREV_FULL = {k.upper(): v for k, v in _ABBREV}

_PREFIXES_LOWER = (
    "thành phố", "thị trấn", "thị xã", "đặc khu", "phường",
    "tỉnh", "huyện", "quận", "xã", "tp.", "tp",
)


def _has_diacritics(cluster_nfc: str) -> bool:
    """True when the user's typed cluster carries any Vietnamese mark.

    Checked AFTER NFC but BEFORE abbreviation expansion, so the machine-added
    "Phường" from "P." never flips the comparison mode. "đ"/"Đ" counts as a
    mark: "da nang" (plain d) is undiacritic, "đà nẵng" is diacritic.
    """
    if "đ" in cluster_nfc.casefold():
        return True
    return any(
        unicodedata.combining(c)
        for c in unicodedata.normalize("NFD", cluster_nfc)
    )


def _strip_diacritics(value: str) -> str:
    base = "".join(
        c for c in unicodedata.normalize("NFD", value)
        if not unicodedata.combining(c)
    )
    return base.replace("đ", "d").replace("Đ", "D")


def _norm(value: str, undiacritic: bool) -> str:
    text = unicodedata.normalize("NFC", value or "").casefold()
    if undiacritic:
        text = _strip_diacritics(text)
    return text


def expand_abbreviation(cluster: str) -> str:
    """Expand a leading shorthand (P. / X. / TT. / TP / H. / Q. / TX.) only."""
    match = _ABBREV_RX.match(cluster)
    if not match:
        return cluster
    full = _ABBREV_FULL.get(match.group(1).upper())
    if not full:
        return cluster
    rest = match.group(2)
    return full + (" " + rest if rest else "")


def split_query(query: str) -> list[str]:
    """Split on comma and hyphen; drop empties; strip only outer spaces."""
    return [
        part.strip()
        for part in re.split(r"[,-]", query)
        if part.strip()
    ]


def _draft_name(official: str) -> str:
    """Lowercase the generic prefix for drafting display (xa Y Yen...)."""
    lowered = official.casefold()
    for prefix in _PREFIXES_LOWER:
        if lowered == prefix:
            return prefix
        if lowered.startswith(prefix + " "):
            return prefix + official[len(prefix):]
    return official[:1].lower() + official[1:] if official else official


class AddressIndex:
    def __init__(self, ledger):
        self.ledger = ledger
        self.units = {u["id"]: u for u in ledger["units"]}
        self.unit_order = [u["id"] for u in ledger["units"]]
        self.names: dict[str, list] = {}
        for row in ledger["names"]:
            self.names.setdefault(row["unit_id"], []).append(row)
        self.parents: dict[str, list] = {}
        for row in ledger["parents"]:
            self.parents.setdefault(row["unit_id"], []).append(row)
        version = ledger.get("dataset_version")
        self.active_observations: list = [
            o for o in ledger.get("observations", [])
            if o.get("dataset_version") == version
        ]
        self.obs_by_unit: dict[str, list] = {}
        for obs in self.active_observations:
            self.obs_by_unit.setdefault(obs["unit_id"], []).append(obs)

    def _active_record(self, rows, uid: str, prefix: str):
        """Name/parent row thuộc đúng bản kho đang hoạt động.

        Importer giữ lịch sử và thêm bản ghi mới mang id theo version
        (`name:<16 ký tự đầu version>:<uid>`); phần tử đầu là cũ nhất nên
        không bao giờ được dùng làm "hiện tại". Observation đã có trường
        `dataset_version`; names/parents khớp bằng id mang version.
        """
        cands = [r for r in (rows or []) if r.get("unit_id") == uid]
        if not cands:
            return None
        version = self.ledger.get("dataset_version") or ""
        wanted = f"{prefix}:{version[:16]}:{uid}"
        for row in cands:
            if row.get("id") == wanted:
                return row
        # Version-tagged importer rows are history, not a name-only catalog.
        # If no row belongs to this version the unit is no longer current.
        if any(re.fullmatch(rf"{prefix}:[0-9a-f]{{16}}:{re.escape(uid)}",
                            r.get("id", "")) for r in cands):
            return None
        return cands[-1]

    def official_name(self, uid: str) -> str:
        row = self._active_record(self.names.get(uid), uid, "name")
        if row:
            return row.get("value") or ""
        return ""

    def province_id(self, uid: str):
        row = self._active_record(self.parents.get(uid), uid, "parent")
        if row:
            return row.get("parent_id")
        return None

    def _invalid(self, dataset_version=None, revision=None):
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "invalid_input",
            "presentation": None,
            "total": 0,
            "results": [],
            "dataset_version": dataset_version,
            "revision": revision,
        }

    def _empty(self, status: str, presentation: str, total: int = 0):
        return {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "presentation": presentation,
            "total": total,
            "results": [],
            "dataset_version": self.ledger.get("dataset_version"),
            "revision": self.ledger.get("revision"),
        }

    def _row(self, uid: str, obs, presentation: str) -> dict:
        level = self.units[uid].get("level")
        name = self.official_name(uid)
        province_ref = None
        province_name = ""
        if level == "commune":
            pid = self.province_id(uid)
            if pid and pid in self.units and self.units[pid].get("level") == "province":
                province_name = self.official_name(pid)
                if province_name:
                    province_ref = {"unit_id": pid, "name": province_name}
            if province_ref is None:
                raise timeline.LedgerError("current commune has no current province")
        if presentation == "drafting":
            if level == "province":
                display = _draft_name(name)
            else:
                display = _draft_name(name) + (
                    ", " + _draft_name(province_name) if province_name else ""
                )
        else:
            source = (obs or {}).get("raw_phrase") if obs else None
            if level == "province":
                display = (name + " = " + source) if source else name
            else:
                head = (name + " = " + source) if source else name
                display = head + (
                    ", " + province_name if province_name else ""
                )
        row: dict = {
            "unit_id": uid,
            "level": level,
            "name": name,
            "province": province_ref,
            "source_text": (obs.get("raw_phrase") if obs else None),
            "display": display,
            "evidence": list(obs.get("evidence", [])) if obs else [],
        }
        if obs is not None:
            row["observation_id"] = obs.get("id")
        return row

    def lookup(self, payload) -> dict:
        # --- payload validation (length checked on the RAW query first) ---
        if not isinstance(payload, dict) or set(payload) != {"query", "presentation"}:
            return self._invalid(
                self.ledger.get("dataset_version"), self.ledger.get("revision")
            )
        query, presentation = payload.get("query"), payload.get("presentation")
        if presentation not in ("drafting", "full"):
            return self._invalid(
                self.ledger.get("dataset_version"), self.ledger.get("revision")
            )
        if (
            not isinstance(query, str)
            or not 1 <= len(query) <= MAX_QUERY_LEN
        ):
            return self._invalid(
                self.ledger.get("dataset_version"), self.ledger.get("revision")
            )

        clusters = split_query(query)
        if not clusters:
            return self._empty("not_found", presentation)

        # Per-cluster comparison mode decided BEFORE abbreviation expansion.
        prepared = []
        for raw in clusters:
            nfc = unicodedata.normalize("NFC", raw)
            undiacritic = not _has_diacritics(nfc)
            expanded = expand_abbreviation(raw)
            prepared.append((expanded, _norm(expanded, undiacritic), undiacritic))

        seen: set[tuple] = set()
        commune_rows: list[dict] = []
        province_rows: list[dict] = []

        def emit(uid: str, obs):
            key = (uid, obs.get("id") if obs else None)
            if key in seen:
                return
            seen.add(key)
            row = self._row(uid, obs, presentation)
            if self.units[uid].get("level") == "province":
                province_rows.append(row)
            else:
                commune_rows.append(row)

        # Ledger order within each level group; communes before provinces.
        # Tên khớp → trả mọi observation đang hoạt động của đơn vị; chỉ
        # raw khớp → trả riêng từng observation có raw khớp (không dừng ở
        # dòng đầu). Trùng cùng (unit_id, observation_id) qua nhiều cụm bỏ
        # nhờ emit().
        for uid in self.unit_order:
            unit = self.units[uid]
            if unit.get("level") not in ("commune", "province"):
                continue
            name = self.official_name(uid)
            if not name:
                continue
            unit_obs = self.obs_by_unit.get(uid, [])
            name_matches = any(needle in _norm(name, plain)
                               for _, needle, plain in prepared)
            # Iterate source rows, not query clauses, to preserve ledger order.
            for obs in unit_obs:
                if name_matches or any(needle in _norm(obs.get("raw_phrase") or "", plain)
                                       for _, needle, plain in prepared):
                    emit(uid, obs)
            if name_matches and not unit_obs:
                emit(uid, None)

        rows = commune_rows + province_rows
        total = len(rows)
        if total == 0:
            return self._empty("not_found", presentation)
        if presentation == "drafting" and total > DRAFTING_LIMIT:
            return self._empty("too_many", presentation, total=total)
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "found",
            "presentation": presentation,
            "total": total,
            "results": rows,
            "dataset_version": self.ledger.get("dataset_version"),
            "revision": self.ledger.get("revision"),
        }


class AddressLookup:
    def __init__(self, folder=None):
        self.folder = Path(folder or timeline.DEFAULT_FOLDER)
        self.index = None
        self.signature = None
        self.lock = threading.Lock()

    def _signature(self, ledger):
        paths = [self.folder / "ledger.json", timeline.SCHEMA] + [
            self.folder / s["snapshot"]
            for s in ledger["sources"]
            if s.get("snapshot")
        ]
        return tuple(
            (str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in paths
        )

    def _cached_version(self):
        if self.index is None:
            return None, None
        return (
            self.index.ledger.get("dataset_version"),
            self.index.ledger.get("revision"),
        )

    def lookup(self, payload):
        # Payload shape is validated inside the index so that invalid_input
        # never needs the ledger; only load it for well-formed requests.
        if (
            not isinstance(payload, dict)
            or set(payload) != {"query", "presentation"}
            or payload.get("presentation") not in ("drafting", "full")
            or not isinstance(payload.get("query"), str)
            or not 1 <= len(payload["query"]) <= MAX_QUERY_LEN
        ):
            version, revision = self._cached_version()
            return {
                "schema_version": SCHEMA_VERSION,
                "status": "invalid_input",
                "presentation": None,
                "total": 0,
                "results": [],
                "dataset_version": version,
                "revision": revision,
            }
        try:
            with self.lock:
                # Stat check is cheap; ledger/snapshot validation is per content
                # revision, never a ledger scan on each keystroke.
                if self.index is None or self._signature(
                    self.index.ledger
                ) != self.signature:
                    ledger = timeline.read_ledger(self.folder)
                    before = self._signature(ledger)
                    timeline.validate(ledger, self.folder)
                    index = AddressIndex(ledger)
                    if before != self._signature(ledger):
                        raise timeline.LedgerError("ledger changed while loading")
                    self.index, self.signature = index, before
                return self.index.lookup(payload)
        except (timeline.LedgerError, json.JSONDecodeError):
            return self._reload_failure(payload)
        except (ValueError, TypeError, KeyError, AttributeError):
            return self._reload_failure(payload)
        except OSError:
            return self._reload_failure(payload)

    def _reload_failure(self, payload=None):
        presentation = None
        if isinstance(payload, dict) and payload.get("presentation") in (
            "drafting",
            "full",
        ):
            presentation = payload["presentation"]
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "reload_failed",
            "presentation": presentation,
            "total": 0,
            "results": [],
            "dataset_version": self.index.ledger["dataset_version"]
            if self.index
            else None,
            "revision": self.index.ledger["revision"] if self.index else None,
        }


_LOOKUP = AddressLookup()


def lookup_address(payload):
    return _LOOKUP.lookup(payload)
