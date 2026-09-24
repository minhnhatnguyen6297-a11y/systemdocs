"""migrate_shell_data.py — copy da kiem chung du lieu upload_lab legacy.

Chuyen mot *working dir* cu (chua .env, registry.sqlite3, output/, runs/,
downloads/, upload_runs/, nd_storage_state.json, uploader_staff_options.json,
logs/) sang vung du lieu theo website cua shell:

    <data_root>/websites/<website_id>/

Nguyen tac (plan MIN-69 §3.2):

- Nguon chi doc — khong bao gio ghi/xoa/sua source.
- Target phai rong (chua ton tai hoac thu muc trong) — khong overwrite.
- Chi anh xa khi cau hinh nguon xac minh duoc website da dang ky
  (hien chi `nam_dinh` qua ND_BASE_URL trong .env).
- Backup SQLite bang API snapshot `Connection.backup`; rewrite cac duong dan
  noi bo (output_json_path/artifact_dir/verify_json) trong BAN SAO — duong
  dan tai lieu goc cua nguoi dung (file_path) giu nguyen.
- Thieu JSON/manifest duoc bao ro va KHONG kich hoat target chua day du:
  apply that bai thi don sach phan da tao, target tro lai rong, chay lai
  duoc (idempotent).
- Log network dump (*.jsonl) co the chua header nhay cam — bo qua, khong in
  noi dung file phien/cookie ra bao cao.

CLI:

    python tools/migrate_shell_data.py --inspect --source PATH --target PATH
    python tools/migrate_shell_data.py --apply   --source PATH --target PATH
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
import urllib.parse
from pathlib import Path

# Cho phep chay truc tiep `python tools/migrate_shell_data.py` tu repo root
# hoac bat ky cwd nao: them repo root (cha cua tools/) vao sys.path.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import providers  # noqa: E402
from playwright_uploader import UPLOADER_ENV_KEYS  # noqa: E402

COPY_DIRS = ("output", "runs", "downloads", "upload_runs")
COPY_FILES = ("nd_storage_state.json", "uploader_staff_options.json")
REGISTRY_NAME = "registry.sqlite3"
ENV_NAME = ".env"
LOGS_DIR = "logs"
# Network dumps co the chua request header — khong copy, khong in noi dung.
SKIP_FILE_SUFFIXES = {".jsonl"}
# Cot path noi bo trong registry tro vao source → rewrite trong ban sao.
# file_path (tai lieu goc cua user) KHONG doi.
REGISTRY_PATH_COLUMNS = ("output_json_path", "artifact_dir", "verify_json")


class MigrationError(Exception):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_env_file(env_path: Path) -> dict:
    """Doc .env truc tiep (khong merge os.environ — tranh gia nguon)."""
    values = {}
    try:
        text = env_path.read_text(encoding="utf-8")
    except OSError:
        return values
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _url_host(url: str) -> str:
    try:
        return (urllib.parse.urlparse(str(url or "").strip()).netloc or "").lower()
    except ValueError:
        return ""


def verify_source_website(source: Path) -> str:
    """Xac minh source la working dir cua website da dang ky.

    Tra website_id ('nam_dinh') hoac raise MigrationError. Thieu .env /
    thieu ND_BASE_URL → website_not_verified; host khac → website_mismatch.
    """
    env_path = source / ENV_NAME
    env_values = _read_env_file(env_path)
    base_url = (env_values.get("ND_BASE_URL") or "").strip()
    if not env_values or not base_url:
        raise MigrationError(
            "website_not_verified",
            f"khong xac minh duoc website nguon: thieu {ENV_NAME} hoac "
            f"ND_BASE_URL trong {source}")
    host = _url_host(base_url)
    if not host:
        raise MigrationError(
            "website_not_verified",
            f"ND_BASE_URL khong doc duoc: {base_url!r}")
    for entry in providers.list_websites():
        if _url_host(entry["display_url"]) == host:
            return entry["website_id"]
    raise MigrationError(
        "website_mismatch",
        f"ND_BASE_URL {base_url!r} khong khop website da dang ky "
        f"(chi co: {', '.join(w['website_id'] for w in providers.list_websites())})")


def _connect_readonly(db_path: Path) -> sqlite3.Connection:
    uri = "file:" + urllib.parse.quote(db_path.as_posix(), safe="/:") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _rel_to(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False


def _count_files(directory: Path) -> int:
    if not directory.is_dir():
        return 0
    return sum(1 for p in directory.rglob("*") if p.is_file())


def inspect_source(source) -> dict:
    """Kiem ke chi-doc: website xac minh, dem so luong/trang thai, file
    duoc tham chieu nhung thieu. Khong ghi gi vao source/target."""
    source = Path(source).resolve()
    report = {
        "source": str(source),
        "website": {"website_id": None, "verified": False,
                    "base_url": None, "problems": []},
        "counts": {},
        "missing": {"output_json": [], "run_manifests": [],
                    "other_files": [], "external": []},
        "problems": [],
    }
    if not source.is_dir():
        report["problems"].append(f"source khong ton tai: {source}")
        return report

    env_values = _read_env_file(source / ENV_NAME)
    report["website"]["base_url"] = env_values.get("ND_BASE_URL") or None
    try:
        website_id = verify_source_website(source)
        report["website"]["website_id"] = website_id
        report["website"]["verified"] = True
    except MigrationError as exc:
        report["website"]["problems"].append(f"{exc.code}: {exc}")

    counts = {
        "env": (source / ENV_NAME).is_file(),
        "storage_state": (source / "nd_storage_state.json").is_file(),
        "staff_options": (source / "uploader_staff_options.json").is_file(),
        "registry": (source / REGISTRY_NAME).is_file(),
        "registry_rows": 0,
        "by_status": {},
        "registry_run_ids": 0,
        "run_manifests": 0,
        "output_json": _count_files(source / "output"),
        "downloads": _count_files(source / "downloads"),
        "upload_runs": _count_files(source / "upload_runs"),
        "logs": _count_files(source / LOGS_DIR),
    }

    run_ids_in_registry = set()
    if counts["registry"]:
        try:
            conn = _connect_readonly(source / REGISTRY_NAME)
            try:
                for row in conn.execute(
                        "SELECT status, COUNT(*) AS n FROM file_registry "
                        "GROUP BY status"):
                    counts["by_status"][str(row["status"])] = int(row["n"])
                    counts["registry_rows"] += int(row["n"])
                run_ids_in_registry = {
                    str(r[0]) for r in conn.execute(
                        "SELECT DISTINCT run_id FROM file_registry "
                        "WHERE run_id IS NOT NULL AND run_id != ''")}
                counts["registry_run_ids"] = len(run_ids_in_registry)
                for row in conn.execute(
                        "SELECT output_json_path, artifact_dir, verify_json "
                        "FROM file_registry"):
                    for col, bucket in (
                            ("output_json_path", "output_json"),
                            ("artifact_dir", "other_files"),
                            ("verify_json", "other_files")):
                        raw = row[col]
                        if not raw:
                            continue
                        p = Path(raw)
                        if p.exists():
                            continue
                        if _is_under(p, source):
                            report["missing"][bucket].append(
                                _rel_to(p, source))
                        else:
                            report["missing"]["external"].append(str(p))
            finally:
                conn.close()
        except sqlite3.Error as exc:
            report["problems"].append(f"khong doc duoc registry: {exc}")

    manifest_run_ids = set()
    runs_dir = source / "runs"
    if runs_dir.is_dir():
        for manifest in sorted(runs_dir.glob("*.json")):
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                report["problems"].append(
                    f"manifest khong doc duoc: {manifest.name}")
                continue
            run_id = str(data.get("run_id") or "").strip()
            if run_id:
                manifest_run_ids.add(run_id)
        counts["run_manifests"] = len(manifest_run_ids)
    report["missing"]["run_manifests"] = sorted(
        run_ids_in_registry - manifest_run_ids)

    report["counts"] = counts
    return report


def _assert_paths(source, target) -> tuple[Path, Path]:
    src = Path(source).resolve()
    tgt = Path(target).resolve()
    if not src.is_dir():
        raise MigrationError("source_not_found",
                             f"source khong ton tai: {src}")
    if src == tgt:
        raise MigrationError("invalid_target",
                             "target trung voi source")
    if _is_under(tgt, src) or _is_under(src, tgt):
        raise MigrationError("invalid_target",
                             "target khong duoc nam trong/cha cua source")
    if tgt.exists():
        if not tgt.is_dir():
            raise MigrationError("target_not_empty",
                                 f"target la file, khong phai thu muc: {tgt}")
        if any(tgt.iterdir()):
            raise MigrationError("target_not_empty",
                                 f"target da co du lieu: {tgt}")
    return src, tgt


def _copy_tree_files(src_dir: Path, dst_dir: Path, *, copied: list,
                     skipped: list):
    if not src_dir.is_dir():
        return
    for path in sorted(src_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(src_dir)
        if path.suffix.lower() in SKIP_FILE_SUFFIXES:
            skipped.append(str(rel))
            continue
        dst = dst_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)
        copied.append((path, dst))


def _write_filtered_env(src_env: Path, dst_env: Path, src_root: Path,
                        tgt_root: Path):
    """Copy .env chi giu key engine cong nhan (UPLOADER_ENV_KEYS); rewrite
    path tuyet doi tro vao source → target. Key la (vi du secret) bi loai."""
    values = _read_env_file(src_env)
    lines = ["# Cau hinh uploader cho tool standalone", ""]
    for key in UPLOADER_ENV_KEYS:
        value = values.get(key, "")
        if key == "ND_STORAGE_STATE_PATH" and value:
            p = Path(value)
            if p.is_absolute() and _is_under(p, src_root):
                value = str(tgt_root / p.resolve().relative_to(src_root))
        lines.append(f"{key}={value}")
    dst_env.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _rewrite_registry_paths(db_path: Path, src_root: Path, tgt_root: Path) -> int:
    """Rewrite cot path noi bo trong BAN SAO registry sang target."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rewritten = 0
    try:
        rows = conn.execute(
            "SELECT id, output_json_path, artifact_dir, verify_json "
            "FROM file_registry").fetchall()
        for row in rows:
            updates = {}
            for col in REGISTRY_PATH_COLUMNS:
                raw = row[col]
                if not raw:
                    continue
                p = Path(raw)
                if _is_under(p, src_root):
                    updates[col] = str(
                        tgt_root / p.resolve().relative_to(src_root))
            if updates:
                sets = ", ".join(f"{c} = ?" for c in updates)
                conn.execute(
                    f"UPDATE file_registry SET {sets} WHERE id = ?",
                    (*updates.values(), row["id"]))
                rewritten += 1
        conn.commit()
    finally:
        conn.close()
    return rewritten


def _verify_registry_copy(src_db: Path, dst_db: Path):
    src = _connect_readonly(src_db)
    dst = _connect_readonly(dst_db)
    try:
        def stats(conn):
            total = conn.execute(
                "SELECT COUNT(*) FROM file_registry").fetchone()[0]
            by_status = dict(conn.execute(
                "SELECT status, COUNT(*) FROM file_registry GROUP BY status"
            ).fetchall())
            ids = [r[0] for r in conn.execute(
                "SELECT id FROM file_registry ORDER BY id").fetchall()]
            runs = [r[0] for r in conn.execute(
                "SELECT DISTINCT run_id FROM file_registry "
                "WHERE run_id IS NOT NULL AND run_id != '' ORDER BY run_id"
            ).fetchall()]
            return total, by_status, ids, runs
        s_total, s_status, s_ids, s_runs = stats(src)
        d_total, d_status, d_ids, d_runs = stats(dst)
    finally:
        src.close()
        dst.close()
    problems = []
    if s_total != d_total:
        problems.append(f"row count {s_total} != {d_total}")
    if s_status != d_status:
        problems.append(f"status {s_status} != {d_status}")
    if s_ids != d_ids:
        problems.append("record_id khong khop")
    if s_runs != d_runs:
        problems.append("run_id khong khop")
    if problems:
        raise MigrationError("verify_failed",
                             "registry copy sai: " + "; ".join(problems))
    return d_total


def apply_migration(source, target) -> dict:
    """Copy + kiem chung. Raise MigrationError; khi that bai sau khi da tao
    file o target thi don sach ve trang thai rong (khong kich hoat target
    thieu du lieu)."""
    src, tgt = _assert_paths(source, target)
    website_id = verify_source_website(src)

    inventory = inspect_source(src)
    missing_internal = (
        inventory["missing"]["output_json"]
        + inventory["missing"]["other_files"])
    if missing_internal or inventory["missing"]["run_manifests"]:
        raise MigrationError(
            "missing_source_files",
            "source thieu file duoc tham chieu — khong kich hoat target: "
            + json.dumps({
                "files": missing_internal,
                "run_manifests": inventory["missing"]["run_manifests"],
            }, ensure_ascii=False),
            details=inventory["missing"])

    provider = providers.get_provider(website_id)
    try:
        # Target phai co dang .../websites/<website_id> — loi shape la loi
        # nguoi dung (exit 2), khong phai crash ProviderDataDirError.
        provider.assert_data_dir(tgt)
    except providers.ProviderDataDirError as exc:
        raise MigrationError("invalid_target", str(exc)) from exc
    created_root = not tgt.exists()
    copied: list[tuple[Path, Path]] = []
    skipped: list[str] = []
    try:
        provider.ensure_data_layout(tgt)

        # .env da loc + rewrite path noi bo
        if (src / ENV_NAME).is_file():
            _write_filtered_env(src / ENV_NAME, tgt / ENV_NAME, src, tgt)

        for name in COPY_FILES:
            f = src / name
            if f.is_file():
                dst = tgt / name
                shutil.copy2(f, dst)
                copied.append((f, dst))

        for sub in COPY_DIRS:
            _copy_tree_files(src / sub, tgt / sub,
                             copied=copied, skipped=skipped)
        _copy_tree_files(src / LOGS_DIR, tgt / LOGS_DIR,
                         copied=copied, skipped=skipped)

        # Registry: backup API snapshot → ban sao nhat quan, roi rewrite path.
        rewritten = 0
        rows_copied = 0
        if (src / REGISTRY_NAME).is_file():
            src_conn = _connect_readonly(src / REGISTRY_NAME)
            dst_conn = sqlite3.connect(str(tgt / REGISTRY_NAME))
            try:
                src_conn.backup(dst_conn)
            finally:
                dst_conn.close()
                src_conn.close()
            rewritten = _rewrite_registry_paths(
                tgt / REGISTRY_NAME, src, tgt)
            rows_copied = _verify_registry_copy(
                src / REGISTRY_NAME, tgt / REGISTRY_NAME)

        # Kiem hash tung file da copy.
        hash_bad = [
            str(dst.relative_to(tgt))
            for src_f, dst in copied
            if not dst.is_file() or _sha256(src_f) != _sha256(dst)
        ]
        if hash_bad:
            raise MigrationError(
                "verify_failed",
                f"hash khong khop: {hash_bad[:5]}"
                + ("..." if len(hash_bad) > 5 else ""))

        # Duong dan da rewrite trong registry phai tro toi file ton tai.
        if (tgt / REGISTRY_NAME).is_file():
            conn = _connect_readonly(tgt / REGISTRY_NAME)
            try:
                dangling = [
                    r[0] for r in conn.execute(
                        "SELECT output_json_path FROM file_registry "
                        "WHERE output_json_path IS NOT NULL "
                        "AND output_json_path != ''")
                    if _is_under(Path(r[0]), tgt)
                    and not Path(r[0]).exists()
                ]
            finally:
                conn.close()
            if dangling:
                raise MigrationError(
                    "verify_failed",
                    f"output_json_path sau rewrite khong ton tai: "
                    f"{dangling[:5]}")

        return {
            "status": "complete",
            "website_id": website_id,
            "source": str(src),
            "target": str(tgt),
            "copied": {
                "files": len(copied),
                "registry_rows": rows_copied,
                "rewritten_paths": rewritten,
            },
            "verified": {
                "files_copied": len(copied),
                "files_hashed": len(copied),
                "registry_rows": rows_copied,
            },
            "skipped": skipped,
            "missing": inventory["missing"],
            "warnings": ([
                "file ngoai source khong ton tai: "
                + "; ".join(inventory["missing"]["external"][:5])
            ] if inventory["missing"]["external"] else []),
        }
    except Exception:
        # Khong kich hoat target chua day du: xoa phan da tao ve trong.
        if created_root and tgt.exists():
            shutil.rmtree(tgt, ignore_errors=True)
        elif tgt.is_dir():
            for child in tgt.iterdir():
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    child.unlink(missing_ok=True)
        raise


def _print_inventory(report: dict, out):
    w = report["website"]
    counts = report["counts"]
    print(f"Source: {report['source']}", file=out)
    if w["verified"]:
        print(f"Website: {w['website_id']} (xac minh qua ND_BASE_URL "
              f"{w['base_url']})", file=out)
    else:
        print("Website: KHONG XAC MINH DUOC — "
              + "; ".join(w["problems"]), file=out)
    print("Counts:", file=out)
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}", file=out)
    missing = report["missing"]
    for bucket in ("output_json", "run_manifests", "other_files", "external"):
        items = missing.get(bucket) or []
        if items:
            print(f"Missing {bucket}: {len(items)}", file=out)
            for item in items[:10]:
                print(f"  - {item}", file=out)
            if len(items) > 10:
                print(f"  ... +{len(items) - 10}", file=out)
    for problem in report["problems"]:
        print(f"Problem: {problem}", file=out)


def _print_target_check(report: dict, target: Path, out):
    """--inspect co --target: bao target co san sang nhan du lieu khong
    (dung shape websites/<website_id>, ton tai/rong)."""
    tgt = Path(target).resolve()
    print(f"Target: {tgt}", file=out)
    website_id = report["website"].get("website_id")
    if not website_id:
        print("  shape: chua kiem — website nguon chua xac minh", file=out)
        return
    try:
        provider = providers.get_provider(website_id)
        provider.assert_data_dir(tgt)
        print(f"  shape: ok (websites/{website_id})", file=out)
    except providers.ProviderDataDirError as exc:
        print(f"  shape: KHONG HOP LE — {exc}", file=out)
        return
    if not tgt.exists():
        print("  trang thai: chua ton tai (se tao moi khi --apply)", file=out)
    elif not tgt.is_dir():
        print("  trang thai: LA FILE — --apply se tu choi", file=out)
    elif any(tgt.iterdir()):
        print("  trang thai: KHONG RONG — --apply se tu choi", file=out)
    else:
        print("  trang thai: thu muc rong — san sang --apply", file=out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="migrate_shell_data",
        description="Copy da kiem chung du lieu upload_lab legacy sang "
                    "vung du lieu theo website (khong sua nguon).")
    parser.add_argument("--inspect", action="store_true",
                        help="in kiem ke chi-doc cua source")
    parser.add_argument("--apply", action="store_true",
                        help="copy sang target (chi khi target rong)")
    parser.add_argument("--source", required=True)
    parser.add_argument("--target",
                        help="bat buoc voi --apply; voi --inspect thi in "
                             "check san sang cua target")
    args = parser.parse_args(argv)

    if not args.inspect and not args.apply:
        parser.error("can it nhat mot trong --inspect / --apply")
    if args.apply and not args.target:
        parser.error("--apply can --target")

    source = Path(args.source)
    try:
        if args.inspect:
            report = inspect_source(source)
            _print_inventory(report, sys.stdout)
            if args.target:
                _print_target_check(report, Path(args.target), sys.stdout)
        if args.apply:
            report = apply_migration(source, Path(args.target))
            print(f"Da copy xong ({report['status']}): "
                  f"{report['copied']['files']} file, "
                  f"{report['copied']['registry_rows']} dong registry, "
                  f"{report['copied']['rewritten_paths']} duong dan da rewrite.")
            if report["skipped"]:
                print(f"Bo qua {len(report['skipped'])} file nhay cam: "
                      + "; ".join(report["skipped"][:5]))
            for warning in report["warnings"]:
                print("Canh bao: " + warning)
    except MigrationError as exc:
        print(f"{exc.code}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 — CLI boundary, khong traceback
        print(f"migration_failed: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
