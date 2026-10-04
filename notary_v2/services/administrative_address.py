"""Read-only, indexed address lookup over the administrative timeline ledger.

Bando prose contributes search aliases, never historical identities or dates.
No customer input is sent over HTTP and this consumer never writes the ledger.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import re
import threading
import unicodedata

try:  # Engine services are imported as top-level modules in the packaged sidecar.
    import administrative_timeline as timeline
except ImportError:
    from notary_v2 import administrative_timeline as timeline


PREFIX = r"(?:thành phố|thị trấn|thị xã|đặc khu|phường|tỉnh|huyện|quận|xã|tp\.?)"
# Greedy toi cuoi de bat ca "(nay là X (y))" — ten dich chua ngoac van
# duoc nhan dien, khong noi them suffix lan hai.
SUFFIX = re.compile(r" \(nay là .*\)\s*$", re.I)


def normalize(value):
    value = unicodedata.normalize("NFC", value or "").casefold().strip()
    value = re.sub(r"^(?:ubnd|ủy ban nhân dân)\s+", "", value)
    value = re.sub(r"^(?:" + PREFIX + r"\s+)+", "", value)
    value = "".join(c for c in unicodedata.normalize("NFD", value) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", value.replace("đ", "d")).strip(" .")


def parse_address(address, source_date):
    """Right-to-left components; hamlet text is retained, never translated."""
    date.fromisoformat(source_date)
    original = SUFFIX.sub("", address)
    parts = [p.strip() for p in re.split(r"[,;]|\s*[-–—]\s*", original) if p.strip()]
    # "Bà Rịa - Vũng Tàu" la mot ten tinh co gach ngang — noi lai khi phan
    # sau khong co prefix cap va phan truoc da la don vi cap tinh day du.
    merged = parts[:1]
    for part in parts[1:]:
        if (not re.match(r"^(?:" + PREFIX + r")\s", part, re.I)
                and re.match(r"^(tỉnh|thành phố|tp\.?)\s", merged[-1], re.I)):
            merged[-1] += " - " + part
        else:
            merged.append(part)
    parts = merged
    if len(parts) < 2:
        # Prefixes also delimit addresses entered without punctuation.
        starts = [m.start() for m in re.finditer(r"(?<!\w)" + PREFIX + r"\s+", original, re.I)]
        if len(starts) >= 2:
            parts = [original[a:b].strip() for a, b in zip([0] + starts, starts + [len(original)]) if b > a]
    old = source_date < "2025-07-01"
    if len(parts) < 2:
        raise ValueError("address requires commune and province")
    # Nguoi dung doi khi viet lon truoc nho sau ("tỉnh P, huyện H, xã X").
    if (re.match(r"^(tỉnh|thành phố|tp\.?)\s", parts[0], re.I) and
            not re.match(r"^(tỉnh|thành phố|tp\.?)\s", parts[-1], re.I)):
        parts.reverse()
    province = parts[-1]
    district = None
    # Don vi cap huyen duoc nhan dien bang prefix bat ke moc 2025 — giay
    # cap sau sap nhap van co the ghi dia chi ba cap cu.
    if len(parts) >= 3 and (re.match(r"^(huyện|quận|thị xã|thành phố)\s", parts[-2], re.I) or
                            (old and not re.match(r"^(xã|phường|thị trấn|đặc khu)\s", parts[-2], re.I))):
        district, commune = parts[-2], parts[-3]
        hamlet = parts[:-3]
    else:
        commune, hamlet = parts[-2], parts[:-2]
    return {"province": province, "district": district, "commune": commune,
            "hamlet": ", ".join(hamlet), "format": "old" if old else "new"}


def predecessor_names(phrase):
    """Conservative prefixed names, including partial territory and qualifiers.

    Returned aliases point to one observation, not a fabricated historical unit.
    Unprefixed prose is deliberately left unparsed.
    """
    phrase = unicodedata.normalize("NFC", phrase)
    pattern = r"(?<!\w)(?:" + PREFIX + r")\s+([^,;()]+?)(?:\s*\(([^)]*)\))?(?:\s+sau khi[^,;]*)?(?=\s+" + PREFIX + r"\s|[,;]|\s*$)"
    for match in re.finditer(pattern, phrase, re.I):
        name = re.split(r"\s+và\s+|\s+và$|\s+một phần|\s+phần còn lại|\s+sau khi", match.group(1), flags=re.I)[0].strip(" .")
        if name and not re.search(r"diện tích|dân số|tự nhiên|quy mô", name, re.I):
            qualifier = match.group(2)
            yield (normalize(name), normalize(qualifier) if qualifier else None,
                   bool(qualifier and re.search(r"huyện|quận|thị xã|thành phố", qualifier, re.I)))


def apply_address(original, destination):
    """Only explicit user acceptance calls this; retain original exact text."""
    return SUFFIX.sub("", original) + " (nay là " + destination + ")"


def _covers(record, day):
    return (record["status"] == "confirmed" and record["valid_from"] is not None and
            record["valid_from"] <= day and (record["valid_to"] is None or day < record["valid_to"]))


class AddressIndex:
    def __init__(self, ledger):
        self.ledger = ledger
        self.units = {u["id"]: u for u in ledger["units"]}
        self.names, self.parents, self.events = defaultdict(list), defaultdict(list), defaultdict(list)
        self.named, self.aliases = defaultdict(set), defaultdict(list)
        self.current = {o["unit_id"]: o for o in ledger["observations"] if o["dataset_version"] == ledger["dataset_version"]}
        for row in ledger["names"]:
            self.names[row["unit_id"]].append(row)
            if row["status"] == "confirmed":
                self.named[normalize(row["value"])].add(row["unit_id"])
        for row in ledger["parents"]:
            self.parents[row["unit_id"]].append(row)
        for event in ledger["events"]:
            if event["status"] == "confirmed":
                for ref in event["from"]:
                    if ref["kind"] == "unit":
                        self.events[ref["id"]].append(event)
        for events in self.events.values():
            events.sort(key=lambda e: e["effective_on"])
        for uid, observation in self.current.items():
            current_name = observation["details"].get("ten")
            if not current_name:
                current_name = next((n["value"] for n in reversed(self.names[uid]) if n["status"] == "observed"), "")
            self.aliases[normalize(current_name)].append((uid, observation, None, False, False))
            for name, qualifier, qualifier_district in predecessor_names(observation["raw_phrase"]):
                self.aliases[name].append((uid, observation, qualifier, qualifier_district, True))

    def name_at(self, uid, day):
        return next((n for n in self.names[uid] if _covers(n, day)), None)

    def province_at(self, uid, day):
        seen = set()
        while uid not in seen:
            seen.add(uid)
            if self.units[uid]["level"] == "province":
                return uid
            parent = next((p for p in self.parents[uid] if _covers(p, day)), None)
            if not parent:
                return None
            uid = parent["parent_id"]
        return None

    def descendants(self, uid, source, target):
        queue, finals = [(uid, source, [])], []
        while queue:
            current, after, trace = queue.pop()
            events = [e for e in self.events[current] if after < e["effective_on"] <= target and
                      e["type"] not in ("rename", "reparent", "type_change")]
            if not events:
                local = [e for e in self.events[current] if after < e["effective_on"] <= target and
                         e["type"] in ("rename", "reparent", "type_change")]
                finals.append((current, trace + local))
                continue
            first_date = events[0]["effective_on"]
            trace = trace + [e for e in self.events[current] if after < e["effective_on"] <= first_date and
                             e["type"] in ("rename", "reparent", "type_change")]
            batch = [e for e in events if e["effective_on"] == first_date]
            consumed, queued = False, False
            for event in batch:
                outputs = [r["id"] for r in event["to"] if r["kind"] == "unit"]
                if event["territory"] == "unknown":
                    finals.append((current, trace + [event]))
                    continue
                consumed |= event["territory"] == "whole" and current not in outputs
                for output in outputs:
                    queued = True
                    queue.append((output, first_date, trace + [event]))
            if not consumed and not any(current == r["id"] for e in batch for r in e["to"]):
                queue.append((current, first_date, trace + batch))
            elif consumed and not queued:
                # Su kien whole nuot unit khong de don vi ke thua (abolition):
                # giu terminal de caller danh dau thieu bang chung thay vi de
                # nhanh nay bien mat nhu chua tung ton tai.
                finals.append((current, trace + batch))
        return finals

    def lookup(self, payload):
        source, target = payload["source_date"], payload["target_date"]
        # Loi parse = loi input phia client → invalid_input, khong de no
        # lot vao except du lieu ledger ben ngoai.
        try:
            parsed = parse_address(payload["address"], source) if payload.get("address") else {
                "province": payload["province"], "commune": payload["commune"], "district": payload.get("district"), "hamlet": ""}
        except ValueError:
            return {"schema_version": "notary.address-lookup.v1", "status": "invalid_input", "candidates": [],
                    "dataset_version": self.ledger["dataset_version"], "revision": self.ledger["revision"],
                    "coverage": {"kind": "invalid_input", "historical": False, "reason": "invalid_address_or_date"},
                    "provenance": []}
        result = {"schema_version": "notary.address-lookup.v1", "status": "not_found", "candidates": [], "parsed": parsed,
                  "dataset_version": self.ledger["dataset_version"], "revision": self.ledger["revision"],
                  "coverage": {"kind": "insufficient_confirmed_history", "historical": False,
                               "reason": "missing_confirmed_identity_or_dates"}, "provenance": []}
        if target < source:
            result["status"] = "invalid_input"
            result["coverage"] = {"kind": "invalid_input", "historical": False, "reason": "target_before_source"}
            return result
        commune, province = normalize(parsed["commune"]), normalize(parsed["province"])
        seeds = []
        for uid in sorted(self.named[commune]):
            n = self.name_at(uid, source)
            puid = self.province_at(uid, source)
            pn = self.name_at(puid, source) if puid else None
            if self.units[uid]["level"] == "commune" and n and normalize(n["value"]) == commune and pn and normalize(pn["value"]) == province:
                seeds.append(uid)
        historical = []
        complete = bool(seeds)
        for seed in seeds:
            for uid, trace in self.descendants(seed, source, target):
                name = self.name_at(uid, target)
                puid = self.province_at(uid, target)
                pn = self.name_at(puid, target) if puid else None
                if not name or not pn or any(e["territory"] == "unknown" for e in trace):
                    complete = False
                    continue
                historical.append({"unit_id": uid, "commune": name["value"], "province": pn["value"],
                                   "address": name["value"] + ", " + pn["value"], "historical": True,
                                   "event_ids": [e["id"] for e in trace],
                                   "evidence": name["evidence"] + pn["evidence"] + [v for e in trace for v in e["evidence"]]})
        if complete and historical:
            result["coverage"] = {"kind": "confirmed_history", "historical": True, "reason": None}
            candidates = historical
        elif historical:
            # Mot phan chuoi confirmed (nhanh con lai chua du bang chung):
            # van tra cac nhanh da xac nhan, coverage giu insufficient —
            # thong tin confirmed khong duoc bo di chi vi nhanh ben thieu,
            # nhung khong duoc trinh nhu lich su day du.
            candidates = historical
        else:
            candidates = []
            # Province aliases only narrow possible current destinations. They do
            # not assign a predecessor commune to one merged old province.
            province_ids = {uid for uid, _, _, _, _ in self.aliases[province] if self.units[uid]["level"] == "province"}
            for uid, obs, qualifier, qualifier_district, predecessor in self.aliases[commune]:
                if self.units[uid]["level"] != "commune":
                    continue
                parent = next((p for p in reversed(self.parents[uid]) if p["status"] == "observed"), None)
                if not parent or parent["parent_id"] not in province_ids:
                    continue
                # Qualifier chi la dau hieu phan biet khi no thuc su chi mot
                # huyen — "(moi)", "(phan con lai)" khong duoc loai ung vien;
                # khong co quan he thi giu moi lua chon, khong bao gio doan.
                if (qualifier_district and parsed.get("district")
                        and qualifier != normalize(parsed["district"])):
                    continue
                current = next((n["value"] for n in reversed(self.names[uid]) if n["status"] == "observed"), None)
                pname = next((n["value"] for n in reversed(self.names[parent["parent_id"]]) if n["status"] == "observed"), None)
                if current and pname:
                    candidates.append({"unit_id": uid, "commune": current, "province": pname,
                                       "address": current + ", " + pname, "historical": False,
                                       "observation_id": obs["id"], "raw_phrase": obs["raw_phrase"],
                                       "partial": bool(re.search("một phần|phần còn lại", obs["raw_phrase"], re.I)),
                                       "old_parent_unconfirmed": predecessor, "evidence": obs["evidence"]})
            if candidates:
                result["coverage"]["kind"] = "current_catalog_candidates"
        distinct = {}
        for c in candidates:
            distinct.setdefault(c["unit_id"], c)
        # Sap xep de cung mot cau hoi tra ve cung thu tu ung vien moi lan.
        result["candidates"] = sorted(distinct.values(), key=lambda c: c["unit_id"])
        result["status"] = ("ambiguous" if any(c.get("old_parent_unconfirmed") for c in distinct.values()) else
                            "match" if len(distinct) == 1 else "ambiguous" if distinct else "not_found")
        result["provenance"] = [e for c in result["candidates"] for e in c["evidence"]]
        return result


class AddressLookup:
    def __init__(self, folder=None):
        self.folder = Path(folder or timeline.DEFAULT_FOLDER)
        self.index = None
        self.signature = None
        self.lock = threading.Lock()

    def _signature(self, ledger):
        paths = [self.folder / "ledger.json", timeline.SCHEMA] + [self.folder / s["snapshot"] for s in ledger["sources"] if s["snapshot"]]
        return tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in paths)

    def lookup(self, payload):
        invalid = {"schema_version": "notary.address-lookup.v1", "status": "invalid_input", "candidates": [], "provenance": [], "dataset_version": None,
                   "revision": None, "coverage": {"kind": "invalid_input", "historical": False, "reason": "invalid_address_or_date"}}
        try:
            if not isinstance(payload, dict) or set(payload) - {"address", "province", "commune", "district", "source_date", "target_date"}:
                return invalid
            for field in ("source_date", "target_date"):
                value = payload.get(field)
                if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                    return invalid
                try:
                    date.fromisoformat(value)
                except ValueError:
                    return invalid
            if not payload.get("address") and not (payload.get("province") and payload.get("commune")):
                return invalid
            if any(not isinstance(v, str) or len(v) > 4000 for v in payload.values()):
                return invalid
            with self.lock:
                # Stat check is cheap; ledger/snapshot validation is per content
                # revision, never a ledger scan on each keystroke.
                if self.index is None or self._signature(self.index.ledger) != self.signature:
                    ledger = timeline.read_ledger(self.folder)
                    before = self._signature(ledger)
                    timeline.validate(ledger, self.folder)
                    index = AddressIndex(ledger)
                    if before != self._signature(ledger):
                        raise timeline.LedgerError("ledger changed while loading")
                    self.index, self.signature = index, before
                return self.index.lookup(payload)
        except (timeline.LedgerError, json.JSONDecodeError):
            return self._reload_failure()
        except (ValueError, TypeError, KeyError, AttributeError):
            # Validation loi input da return o tren — exception o day la
            # loi du lieu ledger (khoa treo, thieu field) → reload_failed,
            # khong gan nhan nham invalid_input.
            return self._reload_failure()
        except OSError:
            return self._reload_failure()

    def _reload_failure(self):
        return {"schema_version": "notary.address-lookup.v1", "status": "not_found", "candidates": [], "provenance": [],
                "dataset_version": self.index.ledger["dataset_version"] if self.index else None,
                "revision": self.index.ledger["revision"] if self.index else None,
                "coverage": {"kind": "reload_failed", "historical": False, "reason": "local_reference_unavailable"}}


_LOOKUP = AddressLookup()


def lookup_address(payload):
    return _LOOKUP.lookup(payload)
