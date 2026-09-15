'use strict';

// G1 shell renderer — display logic thuan (MIN-67, spec MIN-32 §1-4).
// Khong DOM, khong Node, khong electron: dung duoc trong renderer (<script>)
// va node --test (UMD export). Renderer.js chi build DOM tu cac descriptor
// o day — moi mapping trang thai/vocabulary tap trung mot cho de test.

const NAV_SPEC = [
  // 7 muc theo spec MIN-32 §1; placeholder van hien, khong an.
  // id khop module registry (main/registry.js) tru 'overview' la view shell.
  { id: 'overview', title: 'Tổng quan', registry: null },
  { id: 'upload', title: 'Upload/Audit', registry: 'upload' },
  { id: 'document-review', title: 'Hồ sơ', registry: 'document-review' },
  { id: 'excel-word', title: 'Excel/Word', registry: 'excel-word' },
  { id: 'office', title: 'Văn phòng', registry: 'office' },
  { id: 'search', title: 'Tìm kiếm', registry: 'search' },
  // 'Trạng thái/Cài đặt' gop status + settings (registry §6) trong mot view.
  { id: 'status', title: 'Trạng thái/Cài đặt', registry: 'status' },
];

const TERMINAL_STATUS = new Set(
  ['succeeded', 'failed', 'canceled', 'partial']);
const CANCELABLE_STATUS = new Set(
  ['accepted', 'running', 'waiting_user', 'checking']);

// Tien trinh trang thai MIN-32 §2 — label hien thi cho nguoi dung.
const STATUS_LABEL = {
  idle: 'Chờ',
  checking: 'Đang kiểm tra',
  accepted: 'Đã tiếp nhận',
  running: 'Đang chạy',
  waiting_user: 'Chờ người dùng',
  canceling: 'Đang hủy',
  canceled: 'Đã hủy',
  failed: 'Thất bại',
  partial: 'Hoàn tất một phần',
  succeeded: 'Hoàn tất',
};

// Badge nhom mau theo nghia, khong theo raw status.
const STATUS_TONE = {
  idle: 'muted', checking: 'info', accepted: 'info', running: 'info',
  waiting_user: 'warn', canceling: 'warn', canceled: 'muted',
  failed: 'error', partial: 'warn', succeeded: 'ok',
};

// waiting_user KHONG phai loi — CTA ro hanh dong nguoi can lam (spec §4).
const WAITING_CTA = {
  login: 'Đăng nhập trên cửa sổ Chromium, rồi quay lại xác nhận tại đây',
  review: 'Rà soát các trường cần người xác nhận',
  finalize: 'Quyết định Finalize — chỉ người bấm, hệ thống không tự ghi',
  confirm: 'Xác nhận thông tin để job tiếp tục',
};

const ENGINE_STATE_LABEL = {
  stopped: 'đã dừng',
  starting: 'đang khởi động',
  ready: 'sẵn sàng',
  restarting: 'đang khởi động lại',
  unavailable: 'không khả dụng',
};

// Ly do module unavailable (registry.reason / error code).
const UNAVAILABLE_REASON = {
  not_implemented: 'Chưa triển khai',
  engine_not_installed: 'Engine chưa cài đặt',
  engine_unavailable: 'Engine không khả dụng',
  engine_version_mismatch: 'Engine sai phiên bản',
  ocr_stack_parked: 'Không khả dụng (stack parked)',
};

function isTerminal(status) {
  return TERMINAL_STATUS.has(status);
}

function statusLabel(status) {
  return STATUS_LABEL[status] || String(status || '—');
}

function engineStateLabel(state) {
  return ENGINE_STATE_LABEL[state] || String(state || '—');
}

function unavailableReason(code) {
  return UNAVAILABLE_REASON[code] || String(code || 'không rõ lý do');
}

function navEntry(id) {
  // Nav allowlist: chi muc trong NAV_SPEC duoc route; id la bi tu choi.
  return NAV_SPEC.find((n) => n.id === id) || null;
}

function moduleFace(mod) {
  // Mat trang thai cap module: placeholder (office) / unavailable / ready.
  if (!mod) return 'unavailable';
  if (mod.kind === 'placeholder' || mod.reason === 'not_implemented') {
    return 'placeholder';
  }
  if (mod.status === 'unavailable') return 'unavailable';
  return 'ready';
}

// Descriptor 4 mat trang thai man hinh (spec §3) — renderer build DOM tu day.
function faceLoading(label) {
  return { kind: 'loading', title: 'Đang tải',
           detail: label || 'Đang kiểm tra…' };
}

function faceEmpty(title, actionLabel) {
  return { kind: 'empty', title: title || 'Chưa có dữ liệu',
           detail: null, actionLabel: actionLabel || null };
}

function faceError(err) {
  const e = err || {};
  return {
    kind: 'error',
    title: e.code || 'error',
    detail: e.message || '',
    retryable: Boolean(e.retryable),
    nextAction: e.next_action || null,
    diagnosticsHint: 'Xem Trạng thái/Cài đặt → diagnostics',
  };
}

function faceUnavailable(name, reason, hint) {
  return { kind: 'unavailable',
           title: `${name || 'Module'} — Không khả dụng`,
           detail: unavailableReason(reason),
           hint: hint || null };
}

// Model hien thi mot job — renderer khong tu suy luan trang thai.
function jobDisplay(job) {
  const j = job || {};
  const status = j.status || 'idle';
  const waiting = status === 'waiting_user' && j.waiting_on
    ? { on: j.waiting_on,
        cta: WAITING_CTA[j.waiting_on] || 'Cần hành động của người dùng' }
    : null;
  const p = j.progress;
  const progressText = p
    ? `${p.done ?? 0}/${p.total ?? '?'}${p.current_label ? ' — ' + p.current_label : ''}`
    : null;
  const breakdown = status === 'partial' && j.result && j.result.data
    && j.result.data.breakdown ? j.result.data.breakdown : null;
  return {
    jobId: j.job_id || '',
    commandId: j.command_id || '',
    command: j.command || '',
    status,
    label: statusLabel(status),
    tone: STATUS_TONE[status] || 'muted',
    progressText,
    waiting,
    error: j.error || null,
    breakdown,
    resultJson: j.result ? JSON.stringify(j.result, null, 2) : null,
    cancelable: CANCELABLE_STATUS.has(status),
    terminal: isTerminal(status),
    updatedAt: j.updated_at || '',
  };
}

// Dong suc khoe module cho Tổng quan: id, title, mat trang thai, ly do.
function moduleHealth(modules) {
  return (modules || []).map((m) => ({
    id: m.id,
    title: m.title || m.id,
    kind: m.kind || 'engine',
    face: moduleFace(m),
    status: m.status || 'unknown',
    reason: m.reason ? unavailableReason(m.reason) : null,
  }));
}

const api = {
  NAV_SPEC, TERMINAL_STATUS, CANCELABLE_STATUS, STATUS_LABEL, STATUS_TONE,
  WAITING_CTA, ENGINE_STATE_LABEL, UNAVAILABLE_REASON,
  isTerminal, statusLabel, engineStateLabel, unavailableReason, navEntry,
  moduleFace, faceLoading, faceEmpty, faceError, faceUnavailable,
  jobDisplay, moduleHealth,
};

// Electron sandboxed renderer VAN co module/exports (CommonJS-lite cho
// builtin whitelist) — kiem `module` truoc se bo lo window.G1_LIB va lam
// renderer trang. Set ca hai khi ton tai.
if (typeof window !== 'undefined') window.G1_LIB = api;
if (typeof module !== 'undefined' && module.exports) module.exports = api;
