from __future__ import annotations

DEFAULT_STATUS_TEXT = "Đã công chứng"

LOGIN_SELECTORS = {
    "username": [
        {"type": "css", "value": "input[name='username']"},
        {"type": "css", "value": "input[type='text']"},
    ],
    "password": [
        {"type": "css", "value": "input[name='password']"},
        {"type": "css", "value": "input[type='password']"},
    ],
    "submit": [
        {"type": "role", "role": "button", "name": "Đăng nhập"},
        {"type": "text", "value": "Đăng nhập"},
    ],
}

FORM_FIELD_ORDER = [
    "ten_hop_dong",
    "ngay_cong_chung",
    "so_cong_chung",
    "tinh_trang",
    "nhom_hop_dong",
    "loai_tai_san",
    "cong_chung_vien",
    "thu_ky",
    "nguoi_yeu_cau",
    "duong_su",
    "tai_san",
    "file_hop_dong",
]

FORM_SELECTORS = {
    "ten_hop_dong": {
        "kind": "dropdown",
        "label": "Tên hợp đồng",
        "strategies": [
            {"type": "css", "value": r"#hopdong\.tenhopdong"},
        ],
        "verify": True,
        "free_solo": True,
    },
    "ngay_cong_chung": {
        "kind": "text",
        "label": "Ngày công chứng",
        "strategies": [
            {"type": "css", "value": "input[placeholder='dd/mm/yyyy']"},
        ],
    },
    "so_cong_chung": {
        "kind": "text",
        "label": "Số công chứng",
        "strategies": [
            {"type": "css", "value": r"#hopdong\.sohopdong"},
        ],
        "verify": True,
    },
    "tinh_trang": {
        "kind": "dropdown",
        "label": "Tình trạng",
        "strategies": [
            {"type": "css", "value": r"#hopdong\.tinhtrang"},
        ],
    },
    "nhom_hop_dong": {
        "kind": "dropdown",
        "label": "Nhóm hợp đồng",
        "strategies": [
            {"type": "css", "value": "#nhomhopdongId"},
        ],
        "verify": True,
    },
    "loai_tai_san": {
        "kind": "dropdown",
        "label": "Loại tài sản",
        "strategies": [
            {"type": "css", "value": "#loaiTaisan"},
        ],
        "verify": True,
    },
    "cong_chung_vien": {
        "kind": "dropdown",
        "label": "Công chứng viên",
        "strategies": [
            {"type": "css", "value": r"#hopdong\.congchungvien\.id"},
        ],
        "verify": True,
    },
    "thu_ky": {
        "kind": "dropdown",
        "label": "Thư ký",
        "strategies": [
            {"type": "css", "value": r"#hopdong\.thuky"},
        ],
        "verify": True,
        "free_solo": True,
    },
    "nguoi_yeu_cau": {
        "kind": "editor",
        "label": "Thông tin người yêu cầu công chứng",
        "strategies": [
            {
                "type": "xpath",
                "value": "//div[contains(@class,'Field-container')][.//label[contains(normalize-space(.), 'Thông tin người yêu cầu công chứng')]]//*[@contenteditable='true'][1]",
            },
        ],
    },
    "duong_su": {
        "kind": "editor",
        "label": "Đương sự",
        "strategies": [
            {
                "type": "xpath",
                "value": "//div[contains(@class,'Field-container')][.//label[contains(normalize-space(.), 'Đương sự')]]//*[@contenteditable='true'][1]",
            },
        ],
    },
    "tai_san": {
        "kind": "editor",
        "label": "Tài sản",
        "strategies": [
            {
                "type": "xpath",
                "value": "//div[contains(@class,'Field-container')][.//label[contains(normalize-space(.), 'Tài sản')]]//*[@contenteditable='true'][1]",
            },
        ],
    },
    "file_hop_dong": {
        "kind": "file",
        "label": "Văn bản hợp đồng",
        "strategies": [
            {"type": "css", "value": r"#hopdong\.fileHopdong"},
        ],
        "verify_upload": True,
    },
}


VERIFY_FIELDS = [
    "ten_hop_dong",
    "so_cong_chung",
    "tinh_trang",
    "nhom_hop_dong",
    "loai_tai_san",
    "cong_chung_vien",
    "thu_ky",
    "file_hop_dong",
]
