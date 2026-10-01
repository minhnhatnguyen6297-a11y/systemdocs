import uuid
from sqlalchemy import Column, Integer, String, Date, Boolean, Float, ForeignKey, Text, DateTime, JSON, UniqueConstraint, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Customer(Base):
    """Bảng lưu thông tin người (sống hoặc đã chết)."""
    __tablename__ = "customers"

    id           = Column(Integer, primary_key=True, index=True)
    ho_ten       = Column(String(200), nullable=False)
    gioi_tinh    = Column(String(10),  nullable=True)           # Nam / Nữ
    ngay_sinh    = Column(Date,        nullable=True)
    ngay_chet    = Column(Date,        nullable=True)            # NULL = còn sống
    so_giay_to   = Column(String(50),  nullable=True,  unique=True)
    ngay_cap     = Column(Date,        nullable=True)
    dia_chi      = Column(Text,        nullable=True)
    created_at   = Column(DateTime,    server_default=func.now())

    # Quan hệ
    participations   = relationship(
        "InheritanceParticipant",
        back_populates="customer",
        cascade="all, delete-orphan",
        foreign_keys="InheritanceParticipant.customer_id",
    )
    inheritance_cases = relationship("InheritanceCase", back_populates="nguoi_chet", foreign_keys="InheritanceCase.nguoi_chet_id")

    @property
    def con_song(self):
        return self.ngay_chet is None

    @property
    def _moc_cccd_moi(self):
        """01/10/2024 — ngưỡng phân biệt CCCD cũ/mới."""
        from datetime import date
        return self.ngay_cap and self.ngay_cap >= date(2024, 10, 1)

    @property
    def loai_giay_to(self):
        """Loại giấy tờ định danh.
        - Người sống: theo mốc `ngay_cap` 01/10/2024 → `Căn cước công dân`
          (trước) / `Căn cước` (từ mốc); thiếu `ngay_cap` → None — chưa
          xác định, không tự suy (MIN-141 đợt 3).
        - Người chết: KHÔNG gán cứng — loại giấy khai tử lấy từ bằng chứng
          OCR được xác nhận / lựa chọn lưu trong snapshot hồ sơ
          (`stage[].loai_giay_to`); model trả None khi chưa có bằng chứng.
        """
        if not self.con_song:
            return None
        if not self.ngay_cap:
            return None
        return "Căn cước" if self._moc_cccd_moi else "Căn cước công dân"

    @property
    def noi_cap(self):
        """Nơi cấp giấy tờ định danh.
        - Người sống: mốc `ngay_cap` 01/10/2024 → `Cục CSQLHC về TTXH`
          (trước) / `Bộ Công an` (từ mốc); thiếu `ngay_cap` → None.
        - Người chết: chưa có bảng xã NAIA-9 nên KHÔNG suy tên xã cũ/mới
          — nơi cấp lấy từ snapshot/bằng chứng đã xác nhận; None khi
          chưa có."""
        if not self.con_song:
            return None
        if not self.ngay_cap:
            return None
        return ("Bộ Công an" if self._moc_cccd_moi
                else "Cục cảnh sát quản lý hành chính về trật tự xã hội")

    @property
    def loaicutru(self):
        """'Cư trú' (từ 01/10/2024) / 'Thường trú' (trước); 'Nơi chết' với
        người chết (diachi = nơi chết/nơi thường trú cuối — entities.md
        §8.1); thiếu `ngay_cap` người sống → None (chưa xác định)."""
        if not self.con_song:
            return "Nơi chết"
        if not self.ngay_cap:
            return None
        return "Cư trú" if self._moc_cccd_moi else "Thường trú"

    @property
    def loai_dia_chi(self):
        """'Cư trú tại' / 'Thường trú tại' theo mốc 01/10/2024; 'Nơi chết'
        với người chết; thiếu `ngay_cap` người sống → None."""
        if not self.con_song:
            return "Nơi chết"
        if not self.ngay_cap:
            return None
        return "Cư trú tại" if self._moc_cccd_moi else "Thường trú tại"


class Property(Base):
    """Bảng lưu thông tin Giấy chứng nhận quyền sử dụng đất (sổ đỏ)."""
    __tablename__ = "properties"

    id                = Column(Integer, primary_key=True, index=True)
    so_serial         = Column(String(100), nullable=False, unique=True)
    so_vao_so         = Column(String(100), nullable=True)
    so_thua_dat       = Column(String(100), nullable=True)
    so_to_ban_do      = Column(String(100), nullable=True)
    dia_chi           = Column(Text,        nullable=False)
    loai_dat          = Column(String(100), nullable=True)
    dien_tich         = Column(Float,        nullable=True)
    loai_so           = Column(String(200), nullable=True)   # Loại GCN (3 loại)
    land_rows_json    = Column(Text,        nullable=True)   # JSON: [{loai_dat, dien_tich, thoi_han}]
    hinh_thuc_su_dung = Column(String(100), nullable=True)
    thoi_han          = Column(String(100), nullable=True)
    nguon_goc         = Column(Text,        nullable=True)
    ngay_cap          = Column(Date,        nullable=True)
    co_quan_cap       = Column(String(200), nullable=True)
    created_at        = Column(DateTime,    server_default=func.now())

    # Quan hệ
    inheritance_cases = relationship("InheritanceCase", back_populates="tai_san")
    case_links = relationship("InheritanceCaseProperty", back_populates="property", cascade="all, delete-orphan")
    # Cụm đất — bảng con là nguồn lưu chính (MIN-141 đợt 2);
    # land_rows_json chỉ còn vai trò tương thích/chuyển đổi.
    land_rows = relationship("PropertyLandRow", back_populates="property",
                             cascade="all, delete-orphan",
                             order_by="PropertyLandRow.vitri")


class InheritanceCase(Base):
    """Bảng lưu Hồ sơ thừa kế — trung tâm của hệ thống."""
    __tablename__ = "inheritance_cases"

    id               = Column(Integer, primary_key=True, index=True)
    nguoi_chet_id    = Column(Integer, ForeignKey("customers.id"), nullable=False)
    tai_san_id       = Column(Integer, ForeignKey("properties.id"), nullable=False)
    ngay_lap_ho_so   = Column(Date,    nullable=False)
    loai_van_ban     = Column(String(50), default="khai_nhan")   # khai_nhan / thoa_thuan
    trang_thai       = Column(String(20), default="draft")       # draft / locked
    noi_niem_yet     = Column(String(200), nullable=True)        # Tên xã/thị trấn nơi lập văn bản / nơi có đất
    nguoi_nhan_uy_quyen = Column(String(200), nullable=True)     # Người nhận ủy quyền (tên hiển thị — denormalized)
    nguoi_nhan_uy_quyen_id = Column(Integer, ForeignKey("customers.id"), nullable=True)  # Tham chiếu ổn định tới danh bạ (MIN-141 đợt 3)
    noi_dung_viec       = Column(Text,        nullable=True)     # Cụm nội dung việc nhập thủ công
    ghi_chu          = Column(Text,    nullable=True)
    engine_state_json = Column(Text,   nullable=True)            # JSON state cua engine/sơ đồ thừa kế mới
    case_state_json   = Column(Text,   nullable=True)            # JSON SSoT V2 cho stage/pool/diagram
    workspace_revision = Column(Integer, nullable=False, default=1, server_default=text("1"))  # revision workspace (notary.case-drafting.v2)
    workspace_idempotency_key = Column(String(64), nullable=True, index=True)  # idempotency_key của notary.workspace_create
    updated_at       = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at       = Column(DateTime, server_default=func.now())

    # Quan hệ
    nguoi_chet   = relationship("Customer", back_populates="inheritance_cases", foreign_keys=[nguoi_chet_id])
    tai_san      = relationship("Property", back_populates="inheritance_cases")
    property_links = relationship("InheritanceCaseProperty", back_populates="case", cascade="all, delete-orphan")
    participants = relationship("InheritanceParticipant", back_populates="ho_so", cascade="all, delete-orphan")

    @property
    def is_locked(self):
        return self.trang_thai == "locked"

    @property
    def tong_ty_le(self):
        return sum(p.ty_le or 0 for p in self.participants if p.co_nhan_tai_san)


class InheritanceCaseProperty(Base):
    """Lien ket nhieu tai san cho mot ho so."""
    __tablename__ = "inheritance_case_properties"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("inheritance_cases.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    case = relationship("InheritanceCase", back_populates="property_links")
    property = relationship("Property", back_populates="case_links")


class PropertyLandRow(Base):
    """Một cụm đất của tài sản — nguồn lưu chính của cụm đất
    (MIN-141 đợt 2). Unique (property_id, vitri); vitri là vị trí 1-based
    trong mảng land_rows của Stage (giữ nguyên vị trí trống).

    Ba cột nghiệp vụ dùng tên chuẩn mới: loaidat / dientich / thoihan
    (tương đương key wire legacy loai_dat / dien_tich / thoi_han)."""

    __tablename__ = "property_land_rows"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(
        Integer, ForeignKey("properties.id"), nullable=False, index=True)
    vitri = Column(Integer, nullable=False)
    loaidat = Column(String(200))
    dientich = Column(Float)
    thoihan = Column(String(200))

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())

    property = relationship("Property", back_populates="land_rows")

    __table_args__ = (
        UniqueConstraint("property_id", "vitri",
                         name="uq_property_land_row_vitri"),
    )


class InheritanceParticipant(Base):
    """Bảng lưu những người tham gia hồ sơ thừa kế."""
    __tablename__ = "inheritance_participants"

    id               = Column(Integer, primary_key=True, index=True)
    ho_so_id         = Column(Integer, ForeignKey("inheritance_cases.id"),  nullable=False)
    customer_id      = Column(Integer, ForeignKey("customers.id"),          nullable=False)
    vai_tro          = Column(String(50),  nullable=False)   # Vợ/Chồng, Con, Cha/Mẹ, Anh/Chị/Em
    hang_thua_ke     = Column(Integer,     default=1)        # Hàng thừa kế 1, 2, 3
    co_nhan_tai_san  = Column(Boolean,     default=True)     # True = nhận, False = từ chối
    ty_le            = Column(Float,       default=0.0)      # Tỷ lệ % sở hữu sau phân chia
    ghi_chu          = Column(Text,        nullable=True)
    parent_customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    # Quan hệ
    ho_so    = relationship("InheritanceCase", back_populates="participants")
    customer = relationship("Customer",        foreign_keys=[customer_id], back_populates="participations")
    parent_customer = relationship("Customer", foreign_keys=[parent_customer_id])


class WordTemplate(Base):
    """Luu cac file mau Word do nguoi dung tai len de xuat van ban."""
    __tablename__ = "word_templates"

    id = Column(Integer, primary_key=True, index=True)
    ten_mau = Column(String(200), nullable=False)
    ten_file_goc = Column(String(255), nullable=False)
    duong_dan_file = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class ExtractedDocument(Base):
    """Kho luu tru du lieu da boc tach sau khi user xac nhan."""
    __tablename__ = "extracted_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    document_type = Column(String(50), nullable=False)
    raw_text = Column(Text, nullable=True)
    parsed_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ZaloConnectorAccount(Base):
    __tablename__ = "zalo_connector_accounts"

    id = Column(String(36), primary_key=True)
    bound_zalo_id = Column(String(100), nullable=True)
    session_state = Column(String(30), nullable=False, default="login_required")
    listener_generation = Column(Integer, nullable=False, default=0)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    qr_image = Column(Text, nullable=True)
    qr_generated_at = Column(DateTime(timezone=True), nullable=True)
    qr_expires_at = Column(DateTime(timezone=True), nullable=True)
    storage_full = Column(Boolean, nullable=False, default=False)
    intake_consented_at = Column(DateTime(timezone=True), nullable=True)
    policy_version = Column(Integer, nullable=False, default=0, server_default=text("0"))
    policy_acked_version = Column(Integer, nullable=False, default=0, server_default=text("0"))
    source_sync_request_version = Column(Integer, nullable=False, default=0, server_default=text("0"))
    source_sync_acked_version = Column(Integer, nullable=False, default=0, server_default=text("0"))
    gap_started_at = Column(DateTime(timezone=True), nullable=True)
    text_storage_full = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ZaloSource(Base):
    __tablename__ = "zalo_sources"
    __table_args__ = (
        UniqueConstraint("connector_account_id", "conversation_id", name="uq_zalo_source_conversation"),
    )

    id = Column(String(36), primary_key=True)
    connector_account_id = Column(String(36), ForeignKey("zalo_connector_accounts.id"), nullable=False, index=True)
    conversation_id = Column(String(200), nullable=False)
    conversation_type = Column(String(20), nullable=False)
    display_name = Column(String(300), nullable=False)
    enabled = Column(Boolean, nullable=False, default=False)
    source_type = Column(String(20), nullable=True)
    enabled_explicit = Column(Boolean, nullable=True, default=False, server_default=text("0"))
    acked_enabled = Column(Boolean, nullable=True)
    policy_version = Column(Integer, nullable=False, default=0, server_default=text("0"))
    policy_acked_version = Column(Integer, nullable=False, default=0, server_default=text("0"))
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ZaloMedia(Base):
    __tablename__ = "zalo_media"
    __table_args__ = (
        UniqueConstraint(
            "connector_account_id",
            "conversation_id",
            "msg_id",
            "attachment_index",
            name="uq_zalo_media_attachment",
        ),
    )

    id = Column(String(36), primary_key=True)
    connector_account_id = Column(String(36), ForeignKey("zalo_connector_accounts.id"), nullable=False, index=True)
    source_id = Column(String(36), ForeignKey("zalo_sources.id"), nullable=False, index=True)
    conversation_id = Column(String(200), nullable=False)
    msg_id = Column(String(200), nullable=False)
    attachment_index = Column(Integer, nullable=False)
    media_object_key = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=False)
    payload_digest = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ZaloMessageText(Base):
    __tablename__ = "zalo_message_texts"
    __table_args__ = (
        UniqueConstraint("connector_account_id", "conversation_id", "msg_id", name="uq_zalo_message_text"),
    )

    id = Column(String(36), primary_key=True)
    connector_account_id = Column(String(36), ForeignKey("zalo_connector_accounts.id"), nullable=False, index=True)
    source_id = Column(String(36), ForeignKey("zalo_sources.id"), nullable=False, index=True)
    conversation_id = Column(String(200), nullable=False)
    msg_id = Column(String(200), nullable=False)
    sender_id = Column(String(200), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    raw_text = Column(Text, nullable=False)
    payload_digest = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ZaloDataSyncRun(Base):
    __tablename__ = "zalo_data_sync_runs"
    __table_args__ = (
        Index(
            "uq_zalo_data_sync_running_account",
            "connector_account_id",
            unique=True,
            sqlite_where=text("status = 'running'"),
        ),
    )

    id = Column(String(36), primary_key=True)
    connector_account_id = Column(String(36), ForeignKey("zalo_connector_accounts.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False)
    cutoff_at = Column(DateTime(timezone=True), nullable=False)
    deadline_at = Column(DateTime(timezone=True), nullable=False)
    source_ids_json = Column(JSON, nullable=False, default=list, server_default=text("'[]'"))
    counters_json = Column(JSON, nullable=False, default=dict, server_default=text("'{}'"))
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class ZaloBatch(Base):
    __tablename__ = "zalo_batches"

    id = Column(String(36), primary_key=True)
    connector_account_id = Column(String(36), ForeignKey("zalo_connector_accounts.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="preparing")
    items_json = Column(JSON, nullable=False, default=list)
    selection_json = Column(JSON(none_as_null=True), nullable=True)
    outputs_json = Column(JSON, nullable=False, default=dict)
    ocr_status = Column(String(30), nullable=False, default="not_selected")
    raw_ocr_json = Column(JSON, nullable=True)
    confirmed_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# =============================================================================
# MIN-99 — Zalo raw-package consumer (contract intake.*.v1, repo doc lap Zalo)
#
# Bang nay thuoc exchange consumer moi — KHONG dung lai bang legacy
# zalo_sources/zalo_batches (duong webhook cu, giu nguyen toi MIN-101).
# Khong FK sang business tables: raw import khong cham nghiep vu truoc duyet.
# =============================================================================


class ZaloRawRecord(Base):
    """Raw intake records da nhap nguyen ven tu goi (khong anh)."""

    __tablename__ = "zalo_raw_records"

    record_id       = Column(String(36), primary_key=True)
    logical_id      = Column(String(36), nullable=False, index=True)
    revision        = Column(Integer,    nullable=False)
    kind            = Column(String(40), nullable=False, index=True)
    package_id      = Column(String(36), nullable=False, index=True)
    package_sequence = Column(Integer,   nullable=False)
    captured_at     = Column(DateTime(timezone=True), nullable=False)
    recorded_at     = Column(DateTime(timezone=True), nullable=False)
    canonical_sha256 = Column(String(64), nullable=False)
    payload_json    = Column(Text,       nullable=False)   # raw-record.v1 verbatim
    imported_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("logical_id", "revision", name="uq_zalo_raw_logical_rev"),
    )


class ZaloImportLedger(Base):
    """So nhap goi: mot dong mot package_id — replay idempotent."""

    __tablename__ = "zalo_import_ledger"

    package_id      = Column(String(36), primary_key=True)
    consumer_id     = Column(String(36), nullable=False)
    sequence        = Column(Integer,    nullable=False, index=True)
    manifest_sha256 = Column(String(64), nullable=False)
    record_count    = Column(Integer,    nullable=False)
    sealed_at       = Column(DateTime(timezone=True), nullable=True)
    decision        = Column(String(20), nullable=False)   # imported | quarantined
    quarantine_reason = Column(Text,     nullable=True)
    receipt_status  = Column(String(20), nullable=True)    # accepted | rejected | null (chua gui)
    receipt_id      = Column(String(36), nullable=True)
    imported_at     = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ZaloSyncState(Base):
    """Cursor/kv cua sync loop (last_sequence, last_run_at, last_error...)."""

    __tablename__ = "zalo_sync_state"

    key   = Column(String(60), primary_key=True)
    value = Column(Text,       nullable=False)


class ZaloParseJob(Base):
    """Hang parse ben vung: parser loi khong huy ACK raw, retry tu raw."""

    __tablename__ = "zalo_parse_jobs"

    job_id     = Column(String(36), primary_key=True)
    package_id = Column(String(36), nullable=False, index=True)
    state      = Column(String(20), nullable=False, default="pending")   # pending|running|succeeded|failed
    attempts   = Column(Integer,    nullable=False, default=0)
    error      = Column(Text,       nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ZaloIntakeResult(Base):
    """Ket qua parser local per package — revision tang dan, khong ghi de
    du lieu nguoi dung da duyet (chi suggestion, chua apply)."""

    __tablename__ = "zalo_intake_results"

    result_id   = Column(String(36), primary_key=True)
    package_id  = Column(String(36), nullable=False, index=True)
    revision    = Column(Integer,    nullable=False)
    parser_version = Column(String(40), nullable=False)
    result_json = Column(Text,       nullable=False)   # {persons, properties, raw_results, warnings}
    warnings_json = Column(Text,     nullable=False, server_default=text("'[]'"))
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)