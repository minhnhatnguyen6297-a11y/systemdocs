"""Tool test core regex cho nhan vien: test 1 file / ca thu muc, luu log co dinh.

Chay: nhap doi chay-test.bat (lan dau chay cai-dat.bat de cai Python).
Khong can chon loai van ban — engine tu nhan dien (phan chia, tu choi,
khai nhan, chuyen nhuong, tang cho, the chap, ...).
Moi lan chay deu ghi noi them vao logs/ket-qua-test.jsonl de gui ve.
"""
from __future__ import annotations

import json
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import extract_contract
import kiem_tra_trich_xuat
from ket_qua_log import (
    BAO_HIEM_CAN_THIEU,
    DECEASED_CAN_THIEU,
    LOG_PATH,
    PERSON_CAN_THIEU,
    STK_CAN_THIEU,
    THUA_CAN_THIEU,
    doc_ban_ghi,
    ghi_ban_ghi,
    hang_thieu_truong,
    mo_thu_muc_log,
    payload_thanh_ban_ghi,
    tom_tat_ban_ghi,
    truong_trong,
)

ENGINE_VERSION = getattr(extract_contract, "ENGINE_VERSION", "khong-ro")

PERSON_COLUMNS = ("stt", "nguon", "gioi_tinh", "ho_ten", "ngay_sinh", "cccd", "ngay_cap", "dia_chi")
PERSON_HEADERS = ("STT", "Nguồn", "Giới tính", "Họ tên", "Ngày sinh", "CCCD", "Ngày cấp", "Địa chỉ")
PERSON_WIDTHS = (40, 90, 70, 200, 90, 120, 90, 260)
PERSON_THIEU = (3, 4, 5, 7)
DECEASED_COLUMNS = ("stt", "gioi_tinh", "ho_ten", "ten_khac", "ngay_sinh", "ngay_chet", "trich_luc", "dia_chi")
DECEASED_HEADERS = ("STT", "Giới tính", "Họ tên", "Tên gọi khác", "Ngày sinh", "Ngày chết", "Trích lục", "Địa chỉ cuối")
DECEASED_WIDTHS = (40, 70, 200, 160, 90, 90, 160, 260)
DECEASED_THIEU = (2, 4, 5, 7)
SAVINGS_COLUMNS = ("stt", "loai", "so_hieu", "ngan_hang", "chi_nhanh", "ngay_ph", "chu_so")
SAVINGS_HEADERS = ("STT", "Loại sổ", "Số hiệu", "Ngân hàng", "Chi nhánh", "Ngày phát hành", "Chủ sổ")
SAVINGS_WIDTHS = (40, 140, 130, 220, 180, 110, 180)
SAVINGS_THIEU = (2,)
INSURANCE_COLUMNS = ("stt", "so_hd", "ben_bh", "ben_mua", "doi_tuong", "ngay_ky")
INSURANCE_HEADERS = ("STT", "Số hợp đồng", "Bên bảo hiểm", "Bên mua", "Đối tượng", "Ngày ký")
INSURANCE_WIDTHS = (40, 170, 220, 200, 220, 100)
INSURANCE_THIEU = (1,)
PARCEL_COLUMNS = ("stt", "thua", "to", "dien_tich", "muc_dich", "thoi_han", "gcn", "loai_so", "ngay_cap", "dia_chi")
PARCEL_HEADERS = ("STT", "Thửa", "Tờ", "Diện tích", "Mục đích", "Thời hạn", "Serial", "Loại sổ", "Ngày cấp sổ", "Địa chỉ")
PARCEL_WIDTHS = (40, 70, 90, 90, 120, 100, 90, 150, 90, 220)
PARCEL_THIEU = (1, 3)
BATCH_COLUMNS = ("file", "loai", "nguoi", "thua", "ghi_chu")
BATCH_HEADERS = ("File", "Loại", "Người", "Thửa/STK/BH", "Ghi chú")
BATCH_WIDTHS = (300, 140, 60, 100, 300)

KIND_LABELS = {
    "transfer_contract": "Chuyển nhượng",
    "gift_contract": "Tặng cho",
    "asset_commitment": "Cam kết tài sản",
    "transfer_cancellation": "Hủy bỏ",
    "mortgage_contract": "Thế chấp",
    "inheritance_partition": "Phân chia di sản",
    "inheritance_refusal": "Từ chối di sản",
    "inheritance_declaration": "Khai nhận di sản",
    "generic": "Chung chung",
}


def kind_label(kind: str) -> str:
    return KIND_LABELS.get(str(kind or ""), str(kind or "?"))


def run_extract(path: str | Path) -> dict:
    try:
        return extract_contract.extract(str(path))
    except Exception as exc:  # noqa: BLE001 - hien loi ra UI cho nguoi test
        return {"error": str(exc)}


def _ngay_sinh_hien_thi(person: dict) -> str:
    ngay = person.get("ngay_sinh", "")
    if ngay and person.get("chi_co_nam_sinh"):
        return f"{ngay} (chỉ có năm)"
    return ngay


def ban_ghi_thanh_payload(record: dict) -> dict:
    return {
        "raw": {
            "ben_a": {"nguoi": record.get("nguoi", [])},
            "ben_b": {"nguoi": []},
            "nguoi_chet": record.get("nguoi_chet", []),
            "danh_sach_thua_dat": record.get("thua", []),
            "tai_san_chua_ho_tro": record.get("tai_san_chua_ho_tro", []),
            "document_kind": record.get("kind", ""),
        },
        "web_form": {"ten_hop_dong": record.get("ten_hd", ""), "tai_san": record.get("tai_san", "")},
    }


def person_rows(payload: dict) -> list[tuple]:
    raw = payload.get("raw", {})
    rows: list[tuple] = []
    for nguon, key in (("Đầu văn bản", "ben_a"), ("Đầu văn bản", "ben_b")):
        for person in raw.get(key, {}).get("nguoi", []):
            rows.append((
                len(rows) + 1, nguon,
                person.get("gioi_tinh", ""), person.get("ho_ten", ""),
                _ngay_sinh_hien_thi(person), person.get("cccd", ""),
                person.get("ngay_cap_cccd", ""), person.get("dia_chi", ""),
            ))
    return rows


def deceased_rows(payload: dict) -> list[tuple]:
    rows: list[tuple] = []
    for idx, person in enumerate(payload.get("raw", {}).get("nguoi_chet", []), start=1):
        trich_luc = person.get("so_giay_to", "")
        if person.get("ngay_cap"):
            trich_luc = f"{trich_luc} ({person['ngay_cap']})".strip(" ()")
        rows.append((
            idx, person.get("gioi_tinh", ""), person.get("ho_ten", ""),
            person.get("ten_goi_khac", ""), _ngay_sinh_hien_thi(person),
            person.get("ngay_chet", ""), trich_luc, person.get("dia_chi", ""),
        ))
    return rows


def parcel_rows(payload: dict) -> list[tuple]:
    rows: list[tuple] = []
    for idx, thua in enumerate(payload.get("raw", {}).get("danh_sach_thua_dat", []), start=1):
        rows.append((
            idx, thua.get("so_thua_dat", ""), thua.get("so_to_ban_do", ""),
            thua.get("dien_tich", ""), thua.get("muc_dich_su_dung", ""),
            thua.get("thoi_han_su_dung", ""), thua.get("so_gcn", ""),
            thua.get("loai_gcn", ""), thua.get("ngay_cap_gcn", ""), thua.get("dia_chi", ""),
        ))
    return rows


def _ts_chua_ho_tro(payload: dict, key: str) -> bool:
    return key in (payload.get("raw", {}).get("tai_san_chua_ho_tro") or [])


def savings_rows(payload: dict) -> list[tuple]:
    if not _ts_chua_ho_tro(payload, "so_tiet_kiem"):
        return []
    return [(1, "Phát hiện sổ tiết kiệm", "— chưa bóc dòng (tạm dừng)", "", "", "", "")]


def insurance_rows(payload: dict) -> list[tuple]:
    if not _ts_chua_ho_tro(payload, "bao_hiem"):
        return []
    return [(1, "Phát hiện bảo hiểm — chưa bóc dòng (tạm dừng)", "", "", "", "")]


def summarize(payload: dict) -> str:
    if payload.get("error"):
        return f"Lỗi: {payload['error']}"
    raw = payload.get("raw", {})
    web = payload.get("web_form", {})
    kind = str(raw.get("document_kind", ""))
    n_party = len(raw.get("ben_a", {}).get("nguoi", [])) + len(raw.get("ben_b", {}).get("nguoi", []))
    chua_ho_tro = raw.get("tai_san_chua_ho_tro") or []
    note = ""
    if kind not in kiem_tra_trich_xuat.KIND_THUA_KE:
        note = " | loại này chưa có luật kiểm tra"
    return (
        f"Loại: {kind} (tự nhận diện, không cần chọn){note} | "
        f"Tên: {web.get('ten_hop_dong', '')} | "
        f"Người: {n_party} | Chết: {len(raw.get('nguoi_chet', []))} | "
        f"Thửa: {len(raw.get('danh_sach_thua_dat', []))}"
        + (f" | Chưa hỗ trợ: {', '.join(chua_ho_tro)}" if chua_ho_tro else "")
    )


class StaffTestWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Test trích xuất văn bản (engine {ENGINE_VERSION})")
        self.geometry("1150x720")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 4))

        self._build_single_tab()
        self._build_batch_tab()
        self._build_log_tab()

        self.copy_status = tk.StringVar(value="Chuột phải vào ô để copy ngay. Nút cuối dòng để copy cả dòng.")
        ttk.Label(self, textvariable=self.copy_status, wraplength=1100, padding=(10, 4)).pack(fill=tk.X)

    # ---------- dùng chung ----------
    def _make_table(self, parent: ttk.Notebook, title: str, columns: tuple, headers: tuple, widths: tuple) -> ttk.Treeview:
        columns = (*columns, "copy")
        headers = (*headers, "")
        widths = (*widths, 70)
        frame = ttk.Frame(parent)
        parent.add(frame, text=title)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col, header, width in zip(columns, headers, widths):
            tree.heading(col, text=header)
            tree.column(col, width=width, anchor=tk.W)
        tree.column("copy", anchor=tk.CENTER)
        tree.tag_configure("thieu", background="#FFF2CC")
        yscroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        xscroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree.bind("<Button-3>", lambda event, t=tree: self._copy_o_ngay(t, event))
        tree.bind("<ButtonRelease-1>", lambda event, t=tree: self._copy_dong_neu_bam_nut(t, event))
        return tree

    def _o_duoi_chuot(self, tree: ttk.Treeview, event: tk.Event) -> tuple | None:
        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)
        if not row_id or not col_id or not col_id.startswith("#"):
            return None
        col_index = int(col_id[1:]) - 1
        values = tree.item(row_id, "values")
        if not (0 <= col_index < len(values)):
            return None
        return row_id, col_index, values

    def _copy_o_ngay(self, tree: ttk.Treeview, event: tk.Event) -> None:
        """Chuot phai: copy ngay o dang bam, khong menu."""
        found = self._o_duoi_chuot(tree, event)
        if found is None:
            return
        row_id, col_index, values = found
        cols = tree.cget("columns")
        if isinstance(cols, str):
            cols = cols.split()
        if col_index == len(cols) - 1:
            return
        tree.selection_set(row_id)
        self._copy_text(str(values[col_index]))

    def _copy_dong_neu_bam_nut(self, tree: ttk.Treeview, event: tk.Event) -> None:
        """Bam nut rieng cuoi dong thi copy ca dong (cach nhau bang tab)."""
        found = self._o_duoi_chuot(tree, event)
        if found is None:
            return
        row_id, col_index, values = found
        cols = tree.cget("columns")
        if isinstance(cols, str):
            cols = cols.split()
        if col_index != len(cols) - 1:
            return
        tree.selection_set(row_id)
        self._copy_text("\t".join(str(v) for v in values[:-1]))

    def _copy_text(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        ngan = text if len(text) <= 60 else text[:60] + "..."
        self.copy_status.set(f"Đã copy: {ngan}")

    def _fill_tree(self, tree: ttk.Treeview, rows: list[tuple], thieu_idx: tuple) -> None:
        tree.delete(*tree.get_children())
        for row in rows:
            full = (*["" if value is None else value for value in row], "⧉ Copy")
            tag = "thieu" if any(not str(full[i]).strip() for i in thieu_idx if i < len(full)) else ""
            tree.insert("", tk.END, values=full, tags=(tag,) if tag else ())

    # ---------- tab 1: test 1 file ----------
    def _build_single_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Test 1 file")

        top = ttk.Frame(tab, padding=10)
        top.pack(fill=tk.X)
        self.path_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(top, text="Chọn file Word...", command=self.pick_file).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(top, text="Chạy trích xuất", command=self.run_single).pack(side=tk.LEFT, padx=(8, 0))

        self.single_summary = tk.StringVar(value="Chọn 1 file .doc/.docx rồi bấm Chạy. Kết quả tự lưu vào log.")
        ttk.Label(tab, textvariable=self.single_summary, wraplength=1080, padding=(10, 4)).pack(fill=tk.X)

        self.single_books = ttk.Notebook(tab)
        self.single_books.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.s_person = self._make_table(self.single_books, "Người", PERSON_COLUMNS, PERSON_HEADERS, PERSON_WIDTHS)
        self.s_deceased = self._make_table(self.single_books, "Người đã chết", DECEASED_COLUMNS, DECEASED_HEADERS, DECEASED_WIDTHS)
        self.s_parcel = self._make_table(self.single_books, "Thửa đất", PARCEL_COLUMNS, PARCEL_HEADERS, PARCEL_WIDTHS)
        self.s_savings = self._make_table(self.single_books, "Sổ tiết kiệm", SAVINGS_COLUMNS, SAVINGS_HEADERS, SAVINGS_WIDTHS)
        self.s_insurance = self._make_table(self.single_books, "Bảo hiểm", INSURANCE_COLUMNS, INSURANCE_HEADERS, INSURANCE_WIDTHS)
        json_frame = ttk.Frame(self.single_books)
        self.single_books.add(json_frame, text="JSON thô")
        self.s_json = tk.Text(json_frame, wrap=tk.NONE, font=("Consolas", 10))
        yscroll = ttk.Scrollbar(json_frame, orient=tk.VERTICAL, command=self.s_json.yview)
        self.s_json.configure(yscrollcommand=yscroll.set)
        self.s_json.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

    def pick_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn file Word",
            filetypes=[("Word", "*.docx *.doc"), ("Tất cả", "*.*")],
        )
        if path:
            self.path_var.set(path)
            self.run_single()

    def run_single(self) -> None:
        path = self.path_var.get().strip().strip('"')
        if not path or not Path(path).exists():
            messagebox.showwarning("Thiếu file", "Chọn 1 file Word (.doc/.docx) trước.")
            return
        payload = run_extract(path)
        record = payload_thanh_ban_ghi(payload, path, ENGINE_VERSION)
        try:
            record["kiem_tra"] = kiem_tra_trich_xuat.kiem_tra_payload(payload)
        except Exception:  # noqa: BLE001 - log van ghi duoc khi thieu luat
            record["kiem_tra"] = []
        try:
            ghi_ban_ghi(record)
            saved = "Đã lưu vào log."
        except OSError as exc:
            saved = f"KHÔNG lưu được log: {exc}"
        self.single_summary.set(summarize(payload) + f" | {saved} | Loại: {kind_label(payload.get('raw', {}).get('document_kind', ''))}")
        for tree, rows, thieu in (
            (self.s_person, person_rows(payload), PERSON_THIEU),
            (self.s_deceased, deceased_rows(payload), DECEASED_THIEU),
            (self.s_parcel, parcel_rows(payload), PARCEL_THIEU),
            (self.s_savings, savings_rows(payload), SAVINGS_THIEU),
            (self.s_insurance, insurance_rows(payload), INSURANCE_THIEU),
        ):
            self._fill_tree(tree, rows, thieu)
        self.s_json.delete("1.0", tk.END)
        self.s_json.insert("1.0", json.dumps(payload, ensure_ascii=False, indent=2))

    # ---------- tab 2: test cả thư mục ----------
    def _build_batch_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Test cả thư mục")

        top = ttk.Frame(tab, padding=10)
        top.pack(fill=tk.X)
        self.folder_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.folder_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(top, text="Chọn thư mục...", command=self.pick_folder).pack(side=tk.LEFT, padx=(8, 0))
        self.batch_run_btn = ttk.Button(top, text="Chạy tất cả", command=self.run_batch)
        self.batch_run_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.batch_summary = tk.StringVar(value="Chọn thư mục chứa file Word rồi bấm Chạy tất cả. Mỗi file ghi 1 dòng vào log.")
        ttk.Label(tab, textvariable=self.batch_summary, wraplength=1080, padding=(10, 4)).pack(fill=tk.X)

        prog_row = ttk.Frame(tab, padding=(10, 0, 10, 4))
        prog_row.pack(fill=tk.X)
        self.batch_progress = ttk.Progressbar(prog_row, mode="determinate")
        self.batch_progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.batch_stop_btn = ttk.Button(prog_row, text="Dừng", command=self.stop_batch, state=tk.DISABLED)
        self.batch_stop_btn.pack(side=tk.LEFT, padx=(8, 0))
        self._batch_dung = False

        frame = ttk.Frame(tab, padding=(10, 0, 10, 10))
        frame.pack(fill=tk.BOTH, expand=True)
        self.batch_tree = ttk.Treeview(frame, columns=BATCH_COLUMNS, show="headings")
        for col, header, width in zip(BATCH_COLUMNS, BATCH_HEADERS, BATCH_WIDTHS):
            self.batch_tree.heading(col, text=header)
            self.batch_tree.column(col, width=width, anchor=tk.W)
        self.batch_tree.tag_configure("thieu", background="#FFF2CC")
        yscroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.batch_tree.yview)
        self.batch_tree.configure(yscrollcommand=yscroll.set)
        self.batch_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

    def pick_folder(self) -> None:
        path = filedialog.askdirectory(title="Chọn thư mục chứa file Word")
        if path:
            self.folder_var.set(path)

    def stop_batch(self) -> None:
        self._batch_dung = True

    def run_batch(self) -> None:
        folder = self.folder_var.get().strip().strip('"')
        if not folder or not Path(folder).is_dir():
            messagebox.showwarning("Thiếu thư mục", "Chọn thư mục chứa file Word trước.")
            return
        files: list[Path] = []
        for root, _dirs, names in os.walk(folder):
            for name in sorted(names):
                if name.startswith("~"):
                    continue
                if name.lower().endswith((".doc", ".docx")):
                    files.append(Path(root) / name)
        if not files:
            messagebox.showinfo("Trống", "Thư mục không có file .doc/.docx.")
            return
        self.batch_tree.delete(*self.batch_tree.get_children())
        self._batch_dung = False
        self.batch_run_btn.config(state=tk.DISABLED)
        self.batch_stop_btn.config(state=tk.NORMAL)
        self.batch_progress.config(maximum=max(len(files), 1), value=0)
        done = 0
        loi = 0
        canh_bao = 0
        theo_loai: dict[str, int] = {}
        for path in files:
            if self._batch_dung:
                break
            self.batch_summary.set(f"Đang chạy: {path.name} ({done + 1}/{len(files)})...")
            payload = run_extract(path)
            record = payload_thanh_ban_ghi(payload, str(path), ENGINE_VERSION)
            try:
                record["kiem_tra"] = kiem_tra_trich_xuat.kiem_tra_payload(payload)
            except Exception:  # noqa: BLE001 - log van ghi duoc khi thieu luat
                record["kiem_tra"] = []
            try:
                ghi_ban_ghi(record)
            except OSError:
                pass
            raw = payload.get("raw", {})
            kind = raw.get("document_kind", "") if not payload.get("error") else "ERROR"
            theo_loai[kind_label(kind)] = theo_loai.get(kind_label(kind), 0) + 1
            n_person: int | str = ""
            n_asset: int | str = ""
            flags = [f for f in record["kiem_tra"] if f.get("muc") != "bo-qua"]
            if payload.get("error"):
                ghi_chu = f"LỖI: {payload['error']}"[:120]
                loi += 1
                tag = "thieu"
            elif any(f.get("muc") == "loi" for f in flags):
                ghi_chu = "LỖI " + ", ".join(f["id"] for f in flags if f.get("muc") == "loi")
                loi += 1
                tag = "thieu"
            else:
                n_person = len(raw.get("ben_a", {}).get("nguoi", [])) + len(raw.get("ben_b", {}).get("nguoi", []))
                n_asset = len(raw.get("danh_sach_thua_dat", []))
                if raw.get("tai_san_chua_ho_tro"):
                    n_asset = f"{n_asset} (+{','.join(raw['tai_san_chua_ho_tro'])} chưa hỗ trợ)"
                canh_bao += 1 if flags else 0
                ghi_chu = ("cảnh báo " + ", ".join(f["id"] for f in flags)) if flags else "đủ"
                tag = "thieu" if flags else ""
            self.batch_tree.insert(
                "", tk.END,
                values=(path.name, kind_label(kind),
                        n_person, n_asset, ghi_chu, "⧉ Copy"),
                tags=(tag,) if tag else (),
            )
            done += 1
            self.batch_progress.config(value=done)
            self.update()
        self.batch_stop_btn.config(state=tk.DISABLED)
        self.batch_run_btn.config(state=tk.NORMAL)
        ket_qua = "; ".join(f"{loai}: {sl}" for loai, sl in sorted(theo_loai.items()))
        het = "" if done >= len(files) else f" (dừng giữa chừng ở {done}/{len(files)})"
        self.batch_summary.set(
            f"Xong {done}/{len(files)} file{het} | lỗi: {loi} | cảnh báo: {canh_bao} | {ket_qua}. Tất cả đã ghi vào log."
        )

    # ---------- tab 3: xem log ----------
    def _build_log_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Xem log")

        top = ttk.Frame(tab, padding=10)
        top.pack(fill=tk.X)
        self.log_var = tk.StringVar(value=str(LOG_PATH))
        ttk.Entry(top, textvariable=self.log_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(top, text="Mở log khác...", command=self.pick_log).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(top, text="Tải lại", command=self.reload_log).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(top, text="Mở thư mục chứa log", command=self.open_log_folder).pack(side=tk.LEFT, padx=(8, 0))

        filter_row = ttk.Frame(tab, padding=(10, 0, 10, 4))
        filter_row.pack(fill=tk.X)
        ttk.Label(filter_row, text="Lọc loại:").pack(side=tk.LEFT)
        self.kind_var = tk.StringVar(value="Tất cả")
        self.kind_combo = ttk.Combobox(
            filter_row, textvariable=self.kind_var, state="readonly",
            values=["Tất cả"] + sorted(set(KIND_LABELS.values())), width=22,
        )
        self.kind_combo.pack(side=tk.LEFT, padx=(8, 0))
        self.kind_combo.bind("<<ComboboxSelected>>", lambda _e: self.reload_log())
        self.log_summary = tk.StringVar(value="Chưa tải log.")
        ttk.Label(filter_row, textvariable=self.log_summary, padding=(16, 0, 0, 0)).pack(side=tk.LEFT)

        body = ttk.PanedWindow(tab, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        left = ttk.Frame(body)
        body.add(left, weight=1)
        self.file_list = tk.Listbox(left, font=("Consolas", 10))
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=list_scroll.set)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_list.bind("<<ListboxSelect>>", lambda _e: self.show_selected_record())

        right = ttk.Frame(body)
        body.add(right, weight=3)
        self.log_detail_label = tk.StringVar(value="Chọn 1 dòng bên trái để xem chi tiết.")
        ttk.Label(right, textvariable=self.log_detail_label, wraplength=700).pack(fill=tk.X)
        self.log_books = ttk.Notebook(right)
        self.log_books.pack(fill=tk.BOTH, expand=True)
        self.l_person = self._make_table(self.log_books, "Người", PERSON_COLUMNS, PERSON_HEADERS, PERSON_WIDTHS)
        self.l_deceased = self._make_table(self.log_books, "Người đã chết", DECEASED_COLUMNS, DECEASED_HEADERS, DECEASED_WIDTHS)
        self.l_parcel = self._make_table(self.log_books, "Thửa đất", PARCEL_COLUMNS, PARCEL_HEADERS, PARCEL_WIDTHS)
        self.l_savings = self._make_table(self.log_books, "Sổ tiết kiệm", SAVINGS_COLUMNS, SAVINGS_HEADERS, SAVINGS_WIDTHS)
        self.l_insurance = self._make_table(self.log_books, "Bảo hiểm", INSURANCE_COLUMNS, INSURANCE_HEADERS, INSURANCE_WIDTHS)

        self._records: list[dict] = []
        self.reload_log()

    def pick_log(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn file log",
            filetypes=[("Log JSONL", "*.jsonl *.log *.txt"), ("Tất cả", "*.*")],
        )
        if path:
            self.log_var.set(path)
            self.reload_log()

    def open_log_folder(self) -> None:
        mo_thu_muc_log(self.log_var.get().strip().strip('"') or LOG_PATH)

    def reload_log(self) -> None:
        records = doc_ban_ghi(self.log_var.get().strip().strip('"'))
        wanted = self.kind_var.get()
        if wanted != "Tất cả":
            records = [r for r in records if kind_label(r.get("kind", "")) == wanted]
        self._records = records
        self.file_list.delete(0, tk.END)
        for record in records:
            flags = [f for f in (record.get("kiem_tra") or [])
                     if isinstance(f, dict) and f.get("muc") in ("loi", "canh-bao")]
            mark = "(!) " if record.get("loi") or flags or "THIẾU" in tom_tat_ban_ghi(record) else ""
            self.file_list.insert(
                tk.END,
                f"{mark}{record.get('ten_file', '?')} [{record.get('thoi_gian', '?')}]",
            )
        self.log_summary.set(f"{len(records)} lượt test trong log. (!) = có lỗi hoặc thiếu trường (ô vàng).")

    def show_selected_record(self) -> None:
        picked = self.file_list.curselection()
        if not picked:
            return
        record = self._records[picked[0]]
        payload = ban_ghi_thanh_payload(record)
        self.log_detail_label.set(
            f"{record.get('ten_file', '?')} | engine {record.get('engine_version', '?')} | {tom_tat_ban_ghi(record)}"
        )
        for tree, rows, thieu in (
            (self.l_person, person_rows(payload), PERSON_THIEU),
            (self.l_deceased, deceased_rows(payload), DECEASED_THIEU),
            (self.l_parcel, parcel_rows(payload), PARCEL_THIEU),
            (self.l_savings, savings_rows(payload), SAVINGS_THIEU),
            (self.l_insurance, insurance_rows(payload), INSURANCE_THIEU),
        ):
            self._fill_tree(tree, rows, thieu)


def main() -> None:
    app = StaffTestWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
