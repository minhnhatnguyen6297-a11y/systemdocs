"""Tool test core regex: chon 1 file Word -> xem Nguoi + Thua dat trich duoc.

Chay: nhap doi (double-click) file run_regex_test.bat o thu muc upload_lab,
hoac:  python tools/regex_test_tool.py
Chi can Python + python-docx (khong can PySide6, khong can browser).
"""
from __future__ import annotations

import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import extract_contract


PERSON_COLUMNS = ("stt", "nguon", "gioi_tinh", "ho_ten", "ngay_sinh", "cccd", "ngay_cap", "dia_chi")
PERSON_HEADERS = ("STT", "Nguồn", "Giới tính", "Họ tên", "Ngày sinh", "CCCD", "Ngày cấp", "Địa chỉ")
PERSON_WIDTHS = (40, 90, 70, 200, 90, 120, 90, 260)
DECEASED_COLUMNS = ("stt", "gioi_tinh", "ho_ten", "ten_khac", "ngay_sinh", "ngay_chet", "trich_luc", "dia_chi")
DECEASED_HEADERS = ("STT", "Giới tính", "Họ tên", "Tên gọi khác", "Ngày sinh", "Ngày chết", "Trích lục", "Địa chỉ cuối")
DECEASED_WIDTHS = (40, 70, 200, 160, 90, 90, 160, 260)
SAVINGS_COLUMNS = ("stt", "loai", "so_hieu", "ngan_hang", "chi_nhanh", "ngay_ph", "chu_so")
SAVINGS_HEADERS = ("STT", "Loại sổ", "Số hiệu", "Ngân hàng", "Chi nhánh", "Ngày phát hành", "Chủ sổ")
SAVINGS_WIDTHS = (40, 140, 130, 220, 180, 110, 180)
INSURANCE_COLUMNS = ("stt", "so_hd", "ben_bh", "ben_mua", "doi_tuong", "ngay_ky")
INSURANCE_HEADERS = ("STT", "Số hợp đồng", "Bên bảo hiểm", "Bên mua", "Đối tượng", "Ngày ký")
INSURANCE_WIDTHS = (40, 170, 220, 200, 220, 100)
PARCEL_COLUMNS = ("stt", "thua", "to", "dien_tich", "muc_dich", "thoi_han", "gcn", "loai_so", "ngay_cap", "dia_chi")
PARCEL_HEADERS = ("STT", "Thửa", "Tờ", "Diện tích", "Mục đích", "Thời hạn", "Serial", "Loại sổ", "Ngày cấp sổ", "Địa chỉ")
PARCEL_WIDTHS = (40, 70, 90, 90, 120, 100, 90, 150, 90, 220)


def run_extract(path: str | Path) -> dict:
    """Chay engine len 1 file; loi thi tra {"error": ...} thay vi no tung."""
    try:
        return extract_contract.extract(str(path))
    except Exception as exc:  # noqa: BLE001 - hien loi ra UI cho nguoi test
        return {"error": str(exc)}


def summarize(payload: dict) -> str:
    if payload.get("error"):
        return f"Lỗi: {payload['error']}"
    raw = payload.get("raw", {})
    web = payload.get("web_form", {})
    n_party = len(raw.get("ben_a", {}).get("nguoi", [])) + len(raw.get("ben_b", {}).get("nguoi", []))
    n_loi_chung = len(raw.get("loi_chung_nguoi", []))
    n_chet = len(raw.get("nguoi_chet", []))
    n_thua = len(raw.get("danh_sach_thua_dat", []))
    n_stk = len(raw.get("danh_sach_so_tiet_kiem", []))
    n_bh = len(raw.get("danh_sach_bao_hiem", []))
    missing = ", ".join(raw.get("missing_web_form_fields", [])) or "không thiếu"
    return (
        f"Loại: {raw.get('document_kind', '?')} | Tên: {web.get('ten_hop_dong', '')} | "
        f"Người (đầu văn bản): {n_party} | Người (lời chứng): {n_loi_chung} | "
        f"Người đã chết: {n_chet} | Thửa đất: {n_thua} | Sổ TK: {n_stk} | Bảo hiểm: {n_bh} | Thiếu: {missing}"
    )


def _ngay_sinh_hien_thi(person: dict) -> str:
    ngay = person.get("ngay_sinh", "")
    if ngay and person.get("chi_co_nam_sinh"):
        return f"{ngay} (chỉ có năm)"
    return ngay


def person_rows(payload: dict) -> list[tuple]:
    raw = payload.get("raw", {})
    rows: list[tuple] = []
    for nguon, key in (("Đầu văn bản", "ben_a"), ("Đầu văn bản", "ben_b")):
        for person in raw.get(key, {}).get("nguoi", []):
            rows.append((
                len(rows) + 1,
                nguon,
                person.get("gioi_tinh", ""),
                person.get("ho_ten", ""),
                _ngay_sinh_hien_thi(person),
                person.get("cccd", ""),
                person.get("ngay_cap_cccd", ""),
                person.get("dia_chi", ""),
            ))
    for person in raw.get("loi_chung_nguoi", []):
        rows.append((
            len(rows) + 1,
            "Lời chứng",
            person.get("gioi_tinh", ""),
            person.get("ho_ten", ""),
            _ngay_sinh_hien_thi(person),
            person.get("cccd", ""),
            person.get("ngay_cap_cccd", ""),
            person.get("dia_chi", ""),
        ))
    return rows


def deceased_rows(payload: dict) -> list[tuple]:
    rows: list[tuple] = []
    for idx, person in enumerate(payload.get("raw", {}).get("nguoi_chet", []), start=1):
        trich_luc = person.get("so_trich_luc", "")
        if person.get("ngay_trich_luc"):
            trich_luc = f"{trich_luc} ({person['ngay_trich_luc']})".strip(" ()")
        rows.append((
            idx,
            person.get("gioi_tinh", ""),
            person.get("ho_ten", ""),
            person.get("ten_goi_khac", ""),
            _ngay_sinh_hien_thi(person),
            person.get("ngay_chet", ""),
            trich_luc,
            person.get("dia_chi_cuoi", ""),
        ))
    return rows


def parcel_rows(payload: dict) -> list[tuple]:
    rows: list[tuple] = []
    for idx, thua in enumerate(payload.get("raw", {}).get("danh_sach_thua_dat", []), start=1):
        rows.append((
            idx,
            thua.get("so_thua_dat", ""),
            thua.get("so_to_ban_do", ""),
            thua.get("dien_tich", ""),
            thua.get("muc_dich_su_dung", ""),
            thua.get("thoi_han_su_dung", ""),
            thua.get("so_gcn", ""),
            thua.get("loai_gcn", ""),
            thua.get("ngay_cap_gcn", ""),
            thua.get("dia_chi", ""),
        ))
    return rows


def savings_rows(payload: dict) -> list[tuple]:
    rows: list[tuple] = []
    for idx, so in enumerate(payload.get("raw", {}).get("danh_sach_so_tiet_kiem", []), start=1):
        rows.append((
            idx,
            so.get("loai_so", ""),
            so.get("so_hieu", ""),
            so.get("ngan_hang", ""),
            so.get("chi_nhanh", ""),
            so.get("ngay_phat_hanh", ""),
            so.get("chu_so", ""),
        ))
    return rows


def insurance_rows(payload: dict) -> list[tuple]:
    rows: list[tuple] = []
    for idx, bh in enumerate(payload.get("raw", {}).get("danh_sach_bao_hiem", []), start=1):
        rows.append((
            idx,
            bh.get("so_hop_dong", ""),
            bh.get("ben_bao_hiem", ""),
            bh.get("ben_mua", ""),
            bh.get("doi_tuong", ""),
            bh.get("ngay_ky", ""),
        ))
    return rows


def payload_to_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


class RegexTestWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Test core regex — Người + Tài sản")
        self.geometry("1100x700")

        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)
        self.path_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(top, text="Chọn file Word...", command=self.pick_file).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(top, text="Chạy trích xuất", command=self.run).pack(side=tk.LEFT, padx=(8, 0))

        self.summary_var = tk.StringVar(value="Chưa chạy. Chọn 1 file .doc/.docx rồi bấm Chạy trích xuất.")
        ttk.Label(self, textvariable=self.summary_var, wraplength=1050, padding=(10, 4)).pack(fill=tk.X)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))

        self.copy_status = tk.StringVar(value="Chuột phải vào ô để copy ngay. Nút cuối dòng để copy cả dòng.")
        ttk.Label(self, textvariable=self.copy_status, wraplength=1050, padding=(10, 4)).pack(fill=tk.X)

        self.person_tree = self._make_table(("Người", PERSON_COLUMNS, PERSON_HEADERS, PERSON_WIDTHS))
        self.deceased_tree = self._make_table(("Người đã chết", DECEASED_COLUMNS, DECEASED_HEADERS, DECEASED_WIDTHS))
        self.parcel_tree = self._make_table(("Thửa đất", PARCEL_COLUMNS, PARCEL_HEADERS, PARCEL_WIDTHS))
        self.savings_tree = self._make_table(("Sổ tiết kiệm", SAVINGS_COLUMNS, SAVINGS_HEADERS, SAVINGS_WIDTHS))
        self.insurance_tree = self._make_table(("Bảo hiểm", INSURANCE_COLUMNS, INSURANCE_HEADERS, INSURANCE_WIDTHS))
        json_frame = ttk.Frame(self.notebook)
        self.notebook.add(json_frame, text="JSON thô")
        self.json_text = tk.Text(json_frame, wrap=tk.NONE, font=("Consolas", 10))
        json_yscroll = ttk.Scrollbar(json_frame, orient=tk.VERTICAL, command=self.json_text.yview)
        self.json_text.configure(yscrollcommand=json_yscroll.set)
        self.json_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        json_yscroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _make_table(self, spec: tuple) -> ttk.Treeview:
        title, columns, headers, widths = spec
        columns = (*columns, "copy")
        headers = (*headers, "")
        widths = (*widths, 70)
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=title)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col, header, width in zip(columns, headers, widths):
            tree.heading(col, text=header)
            tree.column(col, width=width, anchor=tk.W)
        tree.column("copy", anchor=tk.CENTER)
        yscroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        xscroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree.bind("<Button-3>", lambda event, t=tree: self._copy_o_ngay(t, event))
        tree.bind("<ButtonRelease-1>", lambda event, t=tree: self._copy_dong_neu_bam_nut(t, event))
        return tree

    def _o_duoi_chuot(self, tree: ttk.Treeview, event: tk.Event) -> tuple[str, int, tuple] | None:
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

    def pick_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn file Word",
            filetypes=[("Word", "*.docx *.doc"), ("Tất cả", "*.*")],
        )
        if path:
            self.path_var.set(path)
            self.run()

    def run(self) -> None:
        path = self.path_var.get().strip().strip('"')
        if not path or not Path(path).exists():
            messagebox.showwarning("Thiếu file", "Chọn 1 file Word (.doc/.docx) trước.")
            return
        payload = run_extract(path)
        self.summary_var.set(summarize(payload))
        for tree, rows in (
            (self.person_tree, person_rows(payload)),
            (self.deceased_tree, deceased_rows(payload)),
            (self.parcel_tree, parcel_rows(payload)),
            (self.savings_tree, savings_rows(payload)),
            (self.insurance_tree, insurance_rows(payload)),
        ):
            tree.delete(*tree.get_children())
            for row in rows:
                tree.insert("", tk.END, values=(*row, "⧉ Copy"))
        self.json_text.delete("1.0", tk.END)
        self.json_text.insert("1.0", payload_to_json(payload))


def main() -> None:
    app = RegexTestWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
