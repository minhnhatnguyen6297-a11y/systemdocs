"""Migrate bộ mẫu Word thừa kế (.doc/.docx) sang hệ placeholder v2.

Phạm vi NAIA-12: chỉ đọc file nguồn, ghi file mới ra thư mục đích. Không bao giờ
sửa file gốc - manifest ghi sha256 để đối chiếu.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
import uuid
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from docx import Document

from .word_engine import (
    LAND_ROW_SLOTS,
    NO_SOURCE_PLACEHOLDERS,
    _normalize_token,
    collect_placeholder_occurrences,
    is_fixed_form_code,
    replace_in_doc,
    verified_fixed_codes,
)

# Chỉ loại file khoá/tạm/workbook theo AC1 NAIA-12 — KHÔNG loại theo tên
# (" - Copy.docx", "_old"... vẫn là mẫu thật phải chuyển).
EXCLUDED_SUFFIXES = (".tmp", ".wbk", ".asd", ".xls", ".xlsx", ".xlsm", ".xlsb", ".pdf")
TEMPLATE_SUFFIXES = (".docx", ".doc")

def _normalize(token: str) -> str:
    text = unicodedata.normalize("NFC", token).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _token_key(token: str) -> str:
    """Khóa PHÂN LOẠI/match placeholder theo đúng ngữ nghĩa producer
    (``word_engine._normalize_token`` — bỏ dấu, đ->d, gộp khoảng trắng):
    ``replace_in_doc`` và normalized_mapping của engine khớp occurrence
    theo dạng này nên `[Số công chứng]` lẫn `[So cong chung]` là MỘT
    token với producer. ``_normalize`` giữ nguyên cho tên file/stem và
    khóa lineage manifest — không dùng lẫn hai ngữ nghĩa (review NAIA-12:
    spelling không dấu bị xếp unmapped dù producer đã gỡ)."""
    return _normalize_token(token[1:-1])


# Quyết định Owner (02/10/2026): gỡ hẳn các token này khỏi bộ mẫu.
#  - ``fill``: giữ nhãn/đơn vị in sẵn của biểu mẫu hành chính, chỉ bỏ token và chừa chỗ
#    điền tay (Owner: "giữ cấu trúc/nhãn biểu mẫu... báo ô đó cần người dùng điền tay").
#  - ``remove_line``: xoá cả dòng vì phần chữ còn lại chỉ là dấu câu thừa / câu lỗi.
DROP_TOKENS: dict[str, tuple[str, str]] = {
    "[Giá chuyển nhượng]": ("fill", "…………"),
    "[Giá trị chuyển nhượng]": ("fill", "…………"),
    "[Số công chứng]": ("fill", "…………"),
    "[Số CC]": ("fill", "…………"),
    "[Người ủy quyền2]": ("remove_line", ""),
    "[Ngườ ủy quyền2]": ("remove_line", ""),
}

# Sau khi bỏ token mà dòng chỉ còn dấu câu/số thứ tự -> cả dòng là phần thừa.
_ORPHAN_LINE_RE = re.compile(r"^[\s\d.,;:()\-–—]*$")
DROP_KEYS = {_token_key(token) for token in DROP_TOKENS}
_DROP_LOOKUP = {_token_key(token): action for token, action in DROP_TOKENS.items()}


@dataclass
class TokenMigration:
    old: str
    new: str
    count: int          # số LẦN XUẤT HIỆN thật trong file (không khử trùng lặp)
    status: str         # renamed | kept | fixed_code | dropped | no_source | unmapped | context_fix
    note: str = ""
    applied: int = 0    # số lần đã đổi tên/gỡ thực tế trong file đích


@dataclass
class FileMigration:
    source_name: str
    output_name: str
    source_sha256: str
    converted_from_doc: bool
    tokens: list[TokenMigration] = field(default_factory=list)
    # Đoạn CHỮ IN CỨNG (nhãn loại đất / liệt kê ENUM) đổi thành placeholder —
    # KHÔNG phải placeholder nguồn nên tách khỏi ``tokens``/occurrence
    # (review NAIA-12: cộng nhầm literal events vào placeholder counts).
    literal_fixes: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    applied: bool = False
    removed_lines: int = 0  # số đoạn bị xoá cùng token Owner gỡ (remove_line)

    def status_counts(self) -> dict[str, int]:
        """Số TOKEN (đã gom theo tên) theo status — không phải số lần xuất hiện."""
        out: dict[str, int] = {}
        for token in self.tokens:
            out[token.status] = out.get(token.status, 0) + 1
        return out

    def occurrence_counts(self) -> dict[str, int]:
        """Số LẦN XUẤT HIỆN theo status — mỗi occurrence đếm một.

        Token chỉ bị đổi MỘT PHẦN occurrence (ví dụ ``[ONT]`` ×2: một lần
        nằm trong liệt kê bị gỡ, một lần giữ nguyên) phải tách đúng:
        ``applied`` occurrence nhận status hành động, phần còn lại đếm là
        ``kept`` (giữ nguyên trong output) — không được biến cả ``count``
        thành status hành động (review NAIA-12: count=2 applied=1 từng
        báo 2 context_fix, 0 kept)."""
        out: dict[str, int] = {}
        for token in self.tokens:
            if 0 < token.applied < token.count:
                out[token.status] = out.get(token.status, 0) + token.applied
                out["kept"] = out.get("kept", 0) + (token.count - token.applied)
            else:
                out[token.status] = out.get(token.status, 0) + token.count
        out["_applied"] = sum(token.applied for token in self.tokens)
        out["_occurrences"] = sum(token.count for token in self.tokens)
        return out

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status_counts"] = self.status_counts()
        data["occurrence_counts"] = self.occurrence_counts()
        return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_identity(handle) -> tuple[int, int]:
    """Danh tính file (volume, index) đọc TỪ HANDLE đang mở.

    Trên Windows dùng ``GetFileInformationByHandle`` — cùng biểu diễn
    ``dwVolumeSerialNumber`` (32-bit) + chỉ số file 64-bit mà receipt
    producer PowerShell báo (``Get-Naia12ConvId``). ``os.fstat`` KHÔNG
    so được với producer: ``st_dev`` của Python trên Windows là số
    64-bit nội bộ CRT, không phải volume serial NTFS (review NAIA-12:
    Python báo 10377554075783421026 trong khi C# báo 75127906 — inode
    khớp nhưng volume lệch nên guard từ chối output owned). Nơi khác
    (POSIX) fallback ``(st_dev, st_ino)``."""
    import os

    if os.name != "nt":
        stat = os.fstat(handle.fileno())
        return (stat.st_dev, stat.st_ino)
    import ctypes
    import msvcrt
    from ctypes import wintypes

    class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    info = _BY_HANDLE_FILE_INFORMATION()
    os_handle = msvcrt.get_osfhandle(handle.fileno())
    kernel32 = ctypes.windll.kernel32
    kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
    if not kernel32.GetFileInformationByHandle(
            ctypes.c_void_p(os_handle), ctypes.byref(info)):
        raise ctypes.WinError()
    ino = (int(info.nFileIndexHigh) << 32) | int(info.nFileIndexLow)
    return (int(info.dwVolumeSerialNumber), ino)


def is_template_candidate(path: Path) -> bool:
    """True nếu file là mẫu thật, không phải file tạm/khoá/workbook."""
    name = path.name.lower()
    if name.startswith("~$") or name.startswith("."):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if path.suffix.lower() not in TEMPLATE_SUFFIXES:
        return False
    if path.is_symlink() or not path.is_file():
        return False
    return True


def _iter_files_following_links(root: Path):
    """Yield mọi file dưới ``root``, ĐI THEO cả junction/symlink thư mục.

    ``Path.rglob`` (Python 3.13+) không đệ quy vào thư mục link nên file nằm
    sau junction không được liệt kê để loại trừ — chúng sẽ âm thầm biến mất
    khỏi manifest thay vì hiện trong ``excluded``. Đi tay để thấy đủ.

    Mỗi nhánh mang theo realpath của tổ tiên; gặp lại một realpath đã có
    trên chính nhánh đó nghĩa là vòng link -> dừng nhánh, không lặp vô hạn."""
    stack: list[tuple[Path, frozenset[str]]] = [(Path(root), frozenset())]
    while stack:
        directory, ancestors = stack.pop()
        try:
            real = os.path.normcase(os.path.realpath(str(directory)))
        except OSError:
            continue
        if real in ancestors:
            continue
        chain = ancestors | {real}
        try:
            with os.scandir(directory) as entries:
                children = sorted(entries, key=lambda entry: entry.name)
        except OSError:
            continue
        subdirs: list[Path] = []
        for entry in children:
            path = directory / entry.name
            try:
                if entry.is_dir():
                    subdirs.append(path)
                elif entry.is_file():
                    yield path
            except OSError:
                continue
        # đẩy ngược để pop() duyệt theo thứ tự tên
        stack.extend((path, chain) for path in reversed(subdirs))


def scan_source_templates(src_dir: Path) -> tuple[list[Path], list[str]]:
    """Liệt kê mẫu hợp lệ và cả file bị loại trừ (để manifest ghi rõ).

    Entry nằm dưới thư mục con là JUNCTION/symlink trỏ ra ngoài ``src_dir``
    (file tự nó không phải link nên ``is_symlink()`` không bắt được) bị loại —
    đọc file ngoài thư mục được cấp quyền là thoát scope, giống
    ``word_batch_export.scan_template_dir``."""
    src_dir = Path(src_dir)
    try:
        src_root_key = _norm_key(src_dir).rstrip("\\/")
    except OSError:
        src_root_key = ""
    kept: list[Path] = []
    excluded: list[str] = []
    seen_real: set[str] = set()
    for path in sorted(_iter_files_following_links(src_dir)):
        path_key = _norm_key(path)
        if src_root_key and not _contained_key(path_key, src_root_key):
            excluded.append(path.relative_to(src_dir).as_posix())
            continue
        if not is_template_candidate(path):
            excluded.append(path.relative_to(src_dir).as_posix())
            continue
        # Junction/symlink TRONG src trỏ tới thư mục khác trong src: đi được
        # cả hai đường nên cùng một file thật xuất hiện 2 lần. Chỉ giữ đường
        # đầu (theo thứ tự tên) — nếu không sẽ migrate trùng, đếm file_count
        # sai. File trùng bị bỏ khỏi ``kept`` chứ không vào ``excluded``:
        # nó vẫn được migrate qua đường còn lại.
        if path_key in seen_real:
            continue
        seen_real.add(path_key)
        kept.append(path)
    return kept, excluded


class WordUnavailableError(RuntimeError):
    """Không gọi được Microsoft Word qua COM để chuyển .doc -> .docx."""


# AC1 NAIA-12: tắt macro TRƯỚC khi mở (AutomationSecurity=3 —
# msoAutomationSecurityForceDisable) và không cập nhật link ngoài. Document luôn
# đóng (SaveChanges=0) và Word luôn Quit trong finally, kể cả khi lỗi giữa chừng.
_POWERSHELL_CONVERT = r"""
$ErrorActionPreference = 'Stop'
$src = $env:NAIA_SRC
$dst = $env:NAIA_DST
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using Microsoft.Win32.SafeHandles;
public static class Naia12Conv {
  [StructLayout(LayoutKind.Sequential)]
  public struct BY_HANDLE_FILE_INFORMATION {
    public uint dwFileAttributes;
    public System.Runtime.InteropServices.ComTypes.FILETIME ftCreationTime;
    public System.Runtime.InteropServices.ComTypes.FILETIME ftLastAccessTime;
    public System.Runtime.InteropServices.ComTypes.FILETIME ftLastWriteTime;
    public uint dwVolumeSerialNumber;
    public uint nFileSizeHigh;
    public uint nFileSizeLow;
    public uint nNumberOfLinks;
    public uint nFileIndexHigh;
    public uint nFileIndexLow;
  }
  [DllImport("kernel32.dll", SetLastError = true)]
  public static extern bool GetFileInformationByHandle(
      SafeHandle hFile, out BY_HANDLE_FILE_INFORMATION lpFileInformation);
}
'@
function Get-Naia12ConvId($fs) {
  # Danh tính NTFS (volume:dev, index:ino) đọc từ HANDLE đang mở — không
  # đi qua path nên file bị thay sau khi mở không đánh tráo được.
  $info = New-Object Naia12Conv+BY_HANDLE_FILE_INFORMATION
  if (-not [Naia12Conv]::GetFileInformationByHandle(
      $fs.SafeFileHandle, [ref]$info)) { return $null }
  $ino = ([uint64]$info.nFileIndexHigh -shl 32) -bor [uint64]$info.nFileIndexLow
  return "$($info.dwVolumeSerialNumber):$ino"
}
# Đích phải là staging do caller tạo: danh tính expected đi qua env, kiểm
# TRƯỚC khi dispatch. Handle $guard GIỮ MỞ suốt vòng đời producer với
# FileShare.ReadWrite (KHÔNG Delete) — Windows không cho Move/Rename/
# Delete trên một file còn handle không share-delete, nên inode staging
# bị khoá tại $dst: swap file ngoài vào path giữa guard và SaveAs2 không
# thực hiện được, bytes foreign không bao giờ bị chạm (review NAIA-12:
# check rồi ĐÓNG handle trước SaveAs2 từng để foreign swap vào rồi bị
# ghi đè trong khi receipt vẫn nhận). Nếu producer thật ghi bằng cơ chế
# đổi inode (temp+rename), pin chặn rename -> SaveAs2 thất bại -> từ
# chối bảo thủ thay vì bỏ chứng nhận ownership.
$guard = $null
if ($env:NAIA_DST_DEV -and $env:NAIA_DST_INO) {
  $guard = [System.IO.File]::Open(
      $dst, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read,
      [System.IO.FileShare]::ReadWrite)
  $current = Get-Naia12ConvId $guard
  if ($current -ne "$($env:NAIA_DST_DEV):$($env:NAIA_DST_INO)") {
    $guard.Close()
    $guard = $null
    throw "đích không phải staging của run (identity $current)"
  }
}
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $null
try {
  $word.AutomationSecurity = 3
  try { $word.Options.UpdateLinksAtOpen = $false } catch {}
  $doc = $word.Documents.Open($src, $false, $true, $false)
  try {
    $doc.SaveAs2($dst, 12)
  } catch {
    # Word may publish SaveAs2 using a rename, which our no-delete pin
    # correctly rejects. WordOpenXML returns the complete package in
    # memory; write that package through the already verified handle.
    # No second output path and no release of the ownership guard.
    if ($null -eq $guard) { throw }
    Add-Type -AssemblyName System.IO.Compression
    [xml]$flat = $doc.WordOpenXML
    $pkgNs = 'http://schemas.microsoft.com/office/2006/xmlPackage'
    $parts = $flat.GetElementsByTagName('part', $pkgNs)
    if ($parts.Count -eq 0) { throw 'WordOpenXML contains no package parts' }
    $memory = [System.IO.MemoryStream]::new()
    $zip = [System.IO.Compression.ZipArchive]::new(
        $memory, [System.IO.Compression.ZipArchiveMode]::Create, $true)
    try {
      $types = [System.Xml.XmlDocument]::new()
      $typeRoot = $types.CreateElement('Types',
          'http://schemas.openxmlformats.org/package/2006/content-types')
      [void]$types.AppendChild($typeRoot)
      $utf8 = [System.Text.UTF8Encoding]::new($false)
      foreach ($part in $parts) {
        $name = $part.GetAttribute('name', $pkgNs)
        $contentType = $part.GetAttribute('contentType', $pkgNs)
        if (-not $name.StartsWith('/') -or $name.Contains('..')) {
          throw 'unsafe WordOpenXML package part'
        }
        $entry = $zip.CreateEntry($name.Substring(1))
        $stream = $entry.Open()
        try {
          $binary = $part.GetElementsByTagName('binaryData', $pkgNs)
          if ($binary.Count -gt 0) {
            $bytes = [Convert]::FromBase64String($binary[0].InnerText)
          } else {
            $xmlData = $part.GetElementsByTagName('xmlData', $pkgNs)
            if ($xmlData.Count -ne 1) { throw 'missing WordOpenXML part data' }
            $bytes = $utf8.GetBytes($xmlData[0].InnerXml)
          }
          $stream.Write($bytes, 0, $bytes.Length)
        } finally { $stream.Dispose() }
        $override = $types.CreateElement('Override', $typeRoot.NamespaceURI)
        $override.SetAttribute('PartName', $name)
        $override.SetAttribute('ContentType', $contentType)
        [void]$typeRoot.AppendChild($override)
      }
      $entry = $zip.CreateEntry('[Content_Types].xml')
      $stream = $entry.Open()
      try {
        $bytes = $utf8.GetBytes($types.OuterXml)
        $stream.Write($bytes, 0, $bytes.Length)
      } finally { $stream.Dispose() }
    } finally { $zip.Dispose() }
    $writer = [System.IO.File]::Open(
        $dst, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::ReadWrite)
    try {
      if ((Get-Naia12ConvId $writer) -ne (Get-Naia12ConvId $guard)) {
        throw 'WordOpenXML writer is not the pinned staging file'
      }
      $writer.Position = 0
      $writer.SetLength(0)
      $memory.Position = 0
      $memory.CopyTo($writer)
      $writer.Flush()
    } finally { $writer.Dispose(); $memory.Dispose() }
  }
  # Receipt RÀNG BUỘC LIFECYCLE: đọc TRÊN HANDLE $guard ĐÃ PIN — cùng
  # inode staging từ trước New-Object — NGAY SAU SaveAs2 và TRƯỚC
  # Close(0). Producer chứng nhận bằng tay cầm đã khoá liên tục qua ghi,
  # không mở lại theo path (path chỉ còn trỏ đúng inode trong lúc pin
  # giữ): swap trong/sau Close không đổi được bytes caller sẽ đọc — và
  # nếu path bị thay sau khi pin nhả, caller đọc về hash/identity khác
  # receipt -> từ chối publish (review NAIA-12).
  if ($guard -ne $null) {
    $fs = $guard
  } else {
    $fs = [System.IO.File]::Open(
        $dst, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::ReadWrite)
  }
  try {
    $fs.Position = 0
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
      $hash = ($sha.ComputeHash($fs) |
          ForEach-Object { $_.ToString('x2') }) -join ''
    } finally { $sha.Dispose() }
    $identity = Get-Naia12ConvId $fs
    Write-Output "NAIA12_CONV_SHA256=$hash"
    if ($identity) { Write-Output "NAIA12_CONV_ID=$identity" }
  } finally { if ($null -eq $guard) { $fs.Close() } }
  $doc.Close(0)
  $doc = $null
} finally {
  if ($doc -ne $null) { try { $doc.Close(0) } catch {} }
  try { $word.Quit() } catch {}
  # Dọn COM là best-effort: receipt đã phát — lỗi dọn dẹp không được
  # đánh chìm một conversion đã chứng nhận xong.
  try {
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject(
        $word) | Out-Null
  } catch {}
  if ($guard -ne $null) { try { $guard.Close() } catch {} }
}
# Thoát TƯỜNG MINH: powershell -Command trả exit code theo $? của lệnh
# cuối — một lỗi đã catch (ví dụ Quit/ReleaseComObject hỏng) để lại
# $? = $false -> rc=1 dù conversion + receipt hoàn tất. Lỗi chưa bắt
# vẫn abort trước dòng này nên rc=1 vẫn đúng nghĩa thất bại.
exit 0
"""


def convert_doc_to_docx(
    src: Path,
    dst: Path,
    *,
    staging_identity: tuple[int, int] | None = None,
) -> dict[str, Any] | None:
    """Chuyển .doc -> .docx qua Word COM, chỉ đọc nguồn, không cập nhật link/macro.

    Nguồn được mở read-only và đóng với SaveChanges=0 nên file gốc không đổi.
    Đích luôn phải là staging do LẦN GỌI NÀY sở hữu:

    - ``staging_identity=None`` (gọi trực tiếp): đích chưa tồn tại thì tự
      tạo ``xb`` (run sở hữu từ lúc tạo); đích đã tồn tại — kể cả file
      RỖNG — là file ngoài -> ``FileExistsError`` TRƯỚC khi gọi Word
      (review NAIA-12: đích 0-byte lạ từng được chấp nhận rồi dispatch).
    - ``staging_identity`` cho sẵn (caller ``migrate_templates`` đã tạo
      staging + ``_file_identity`` trên fd tạo): đích phải còn đúng
      (volume, index) đó ngay trước khi dispatch — staging bị thay ->
      ``ValueError``, không gọi Word.

    Bên trong producer, handle guard mở theo path đích được GIỮ MỞ suốt
    ``New-Object`` -> ``SaveAs2`` -> receipt -> ``Close`` với share
    ReadWrite nhưng KHÔNG Delete: inode staging khoá tại đích nên file
    ngoài không swap vào path được trong khi ghi, bytes foreign không
    bị chạm (review NAIA-12: check rồi nhả handle trước ``SaveAs2`` từng
    để foreign bị đè mà receipt vẫn hợp lệ). Producer nào ghi bằng
    temp+rename qua đích sẽ thất bại dưới pin -> từ chối bảo thủ.

    Trả receipt ``{"sha256": ..., "identity": (volume, index) | None}``
    của file converter vừa ghi — hash và danh tính NTFS đều đọc trên
    CHÍNH handle guard đã pin, NGAY TRƯỚC ``Close(0)`` trong chính tiến
    trình converter — để caller chứng minh file đọc về đúng là output của
    LẦN convert này kể cả khi path bị thay sau khi document đóng.
    ``None`` khi converter không xuất receipt được."""
    import os
    import subprocess

    src, dst = Path(src).resolve(), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if staging_identity is not None:
        try:
            with open(dst, "rb") as owned:
                owned_identity = _file_identity(owned)
        except OSError as exc:
            raise ValueError(
                f"staging đích không mở được để kiểm danh tính: {dst}") from exc
        if owned_identity != tuple(staging_identity):
            raise ValueError(
                f"đích không phải staging do run tạo: {dst}")
        expected = tuple(staging_identity)
    else:
        if dst.exists() or dst.is_symlink():
            raise FileExistsError(
                f"file đích đã tồn tại, từ chối ghi đè: {dst}")
        with open(dst, "xb") as created:
            expected = _file_identity(created)
    env = dict(os.environ)
    env["NAIA_SRC"] = str(src)
    env["NAIA_DST"] = str(dst.resolve())
    env["NAIA_DST_DEV"] = str(expected[0])
    env["NAIA_DST_INO"] = str(expected[1])
    try:
        proc = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                _POWERSHELL_CONVERT,
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:  # pragma: no cover - môi trường
        raise WordUnavailableError(f"không chạy được Word COM: {exc}") from exc
    if proc.returncode != 0 or not dst.exists():
        detail = (proc.stderr or proc.stdout or "").strip()[:500]
        raise WordUnavailableError(f"Word COM không chuyển được {src.name}: {detail}")
    receipt_sha = None
    receipt_id = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith("NAIA12_CONV_SHA256="):
            receipt_sha = line.split("=", 1)[1].strip().lower() or None
        elif line.startswith("NAIA12_CONV_ID="):
            parts = line.split("=", 1)[1].strip().split(":", 1)
            try:
                receipt_id = (int(parts[0]), int(parts[1]))
            except (IndexError, ValueError):
                receipt_id = None
    if receipt_sha is None:
        return None
    return {"sha256": receipt_sha, "identity": receipt_id}


def old_to_new_map(aliases: dict[str, str] | None = None) -> dict[str, str]:
    """Bảng alias token cũ -> chuẩn mới (catalog §8)."""
    base = {
        "[Niêm Yết]": "[Nơi niêm yết]",
        "[Người yêu cầu]": "[Người yêu cầu cung cấp]",
        "[Thời hạn]": "[Thời hạn 1]",
        "[Tờ khai số]": "[Số tờ khai]",
        "[Ngày tiếp nhận]": "[Ngày nhận hồ sơ]",
        "[Danh sách người thừa kế]": "[Danh sách hàng thừa kế]",
        "[Đoạn mô tả quan hệ]": "[Đoạn quan hệ gia đình]",
        # Owner: [Người ủy quyền] là người ĐƯỢC ủy quyền. Trong "3. UQ.docx"
        # token đứng một mình sau "tôi uỷ quyền cho:" -> cần đoạn dựng sẵn đầy
        # đủ (tên, năm sinh, giấy tờ, địa chỉ), không chỉ họ tên.
        "[Người ủy quyền]": "[Dòng người được ủy quyền 1]",
        "[Ngườ ủy quyền]": "[Dòng người được ủy quyền 1]",
    }
    if aliases:
        base.update(aliases)
    return base


def diff_tokens(
    present: Iterable[str],
    *,
    alias_map: dict[str, str] | None = None,
    registry: Iterable[str] = (),
    no_source: Iterable[str] = (),
    verified_codes: Iterable[str] = (),
) -> list[TokenMigration]:
    """Đối chiếu token trong mẫu với registry engine; phân loại từng token.

    ``count`` = số LẦN XUẤT HIỆN thật (không khử trùng lặp). ``verified_codes``
    là danh sách mã in cứng đã xác minh của ĐÚNG mẫu này — token dạng số ngoài
    danh sách đó rơi vào ``unmapped`` thay vì được gán nhãn ``fixed_code``.
    """
    # Catalog tra theo đúng khóa producer/engine match occurrence
    # (`_token_key` — review NAIA-12); record vẫn giữ spelling nguồn.
    aliases = {_token_key(k): (k, v) for k, v in old_to_new_map(alias_map).items()}
    registry_map = {_token_key(t): t for t in registry}
    no_source_map = {_token_key(t): t for t in no_source}
    verified = set(verified_codes)

    counts: dict[str, int] = {}
    for token in present:
        counts[token] = counts.get(token, 0) + 1

    results: list[TokenMigration] = []
    for token in sorted(counts):
        count = counts[token]
        if is_fixed_form_code(token) and token in verified:
            results.append(TokenMigration(token, token, count, "fixed_code", "nhãn in cứng đã xác minh"))
            continue
        key = _token_key(token)
        if key in DROP_KEYS:
            results.append(
                TokenMigration(token, "", count, "dropped", "Owner gỡ khỏi bộ mẫu (02/10/2026)")
            )
            continue
        if key in aliases:
            old, new = aliases[key]
            results.append(TokenMigration(token, new, count, "renamed", f"alias catalog §8 của {old}"))
            continue
        if key in registry_map:
            results.append(TokenMigration(token, registry_map[key], count, "kept", "đã có trong registry"))
            continue
        if key in no_source_map:
            results.append(TokenMigration(token, token, count, "no_source", "chưa có nguồn dữ liệu (catalog §9)"))
            continue
        results.append(TokenMigration(token, "", count, "unmapped", "không có trong registry"))
    return results


def drop_tokens_in_doc(doc: Any, drops: dict[str, tuple[str, str]]) -> tuple[dict[str, int], int]:
    """Bỏ hẳn token Owner đã gỡ, dọn luôn dấu câu/chữ thừa phụ thuộc token.

    Trả ``(số lần bỏ theo token, số đoạn bị xoá)``. Chỉ những đoạn CHỨA token bị gỡ
    mới được xét xoá, nên không đụng tới các đoạn trống khác của biểu mẫu.
    """
    touched = _paragraphs_containing(doc, drops)
    counts: dict[str, int] = {}
    for token, (_mode, replacement) in drops.items():
        counts[token] = replace_in_doc(doc, {token: replacement})

    if not any(mode == "remove_line" for mode, _ in drops.values()):
        return counts, 0

    removed = 0
    dirty_parts: set[int] = set()
    for para, part_root in touched:
        element = para._element
        if element.getparent() is None:
            continue
        if _ORPHAN_LINE_RE.match(para.text.strip()):
            element.getparent().remove(element)
            removed += 1
            if part_root is not None:
                dirty_parts.add(id(part_root))
    for para, part_root in touched:
        if part_root is not None and id(part_root) in dirty_parts:
            part_root.commit()  # part blob (footnotes/endnotes) phải ghi ngược
            dirty_parts.discard(id(part_root))
    return counts, removed


def _paragraphs_containing(doc: Any, drops: dict[str, tuple[str, str]]) -> list[Any]:
    """Mọi đoạn trong mọi part (body, bảng, header/footer, textbox) có token bị gỡ."""
    from docx.oxml.ns import qn
    from docx.text.paragraph import Paragraph

    from .word_engine import _iter_part_paragraphs, _iter_word_part_roots

    found: list[Any] = []
    for part_root in _iter_word_part_roots(doc):
        for element in _iter_part_paragraphs(part_root.element, qn):
            para = Paragraph(element, doc)
            if any(token in para.text for token in drops):
                found.append((para, part_root))
    return found


def _read_tokens(path: Path) -> list[str]:
    """Mọi lần xuất hiện token (giữ trùng lặp) để manifest đếm occurrence thật."""
    return collect_placeholder_occurrences(Document(str(path)))


# ---------------------------------------------------------------------------
# Context fix theo quyết định Owner (review NAIA-12; nguồn quyết định NAIA-8
# comment 01a0fd42-5cbe-7076-976e-ef907c8ca086 và 01a0fd54-f78f-713f-9b58-
# 3422ea736e42). Alias [ONT]/[CLN]/[NTS]/[LUC]( N) là diện tích theo VỊ TRÍ
# dòng loại đất — giữ nguyên. Nhưng nhãn chữ in cứng kèm chúng ("Loại đất 1:
# ONT") là DỮ LIỆU hồ sơ, không phải mã biểu mẫu hành chính: phải thay bằng
# placeholder động để đầu ra in đúng loại đất thật của từng dòng.
# ---------------------------------------------------------------------------

# Token đổi tên theo NGỮ CẢNH file (khoá = stem nguồn đã normalize): mẫu
# "DK18, thuế N" là tờ khai của tài sản N — mọi token đất thiếu hậu tố hoặc
# alias vị trí dùng ở nghĩa "tổng tài sản" phải chỉ đúng tài sản N, không
# phải tài sản 1. [Địa chỉ đất]/[Diện tích]/[Loại đất N] trong các mẫu này
# đều thuộc mục kê khai của đúng thửa đất đang khai.
_CONTEXT_TOKEN_RENAMES: dict[str, dict[str, str]] = {
    "2. dk18, thuế 2": {
        "[Diện tích]": "[Diện tích tài sản 2]",
        "[Diện tích 2]": "[Diện tích tài sản 2]",
        "[Loại đất 2]": "[Loại đất tài sản 2]",
        "[Địa chỉ đất]": "[Địa chỉ đất tài sản 2]",
    },
    "2. dk18, thuế 3": {
        "[Diện tích]": "[Diện tích tài sản 3]",
        "[Diện tích 3]": "[Diện tích tài sản 3]",
        "[Loại đất 3]": "[Loại đất tài sản 3]",
        "[Địa chỉ đất]": "[Địa chỉ đất tài sản 3]",
    },
}

# Mẫu có nhãn loại đất in cứng kèm token vị trí: "+ Loại đất 1: ONT; ...
# Diện tích: [ONT N] m2" -> "Loại đất 1: [Loại đất tài sản N.1]; ..." để
# nhãn in theo dữ liệu thật của dòng đó (nhãn sai cứng là lỗi nội dung).
_LAND_LABEL_STEMS = {"2. dk18, thuế 1", "2. dk18, thuế 2", "2. dk18, thuế 3"}

# Mẫu liệt kê in cứng "Mục đích sử dụng: ONT: [ONT] m2; CLN: [CLN] m2; ...":
# cụm này là cách cũ liệt kê từng "loại: diện tích" — thay trọn bằng
# [Mục đích sử dụng 1] để chỉ in các dòng đất THẬT của hồ sơ (giữ cứng sẽ
# in sai loại đất và để lại đuôi ":  m2" cho vị trí vắng).
_PURPOSE_ENUM_STEMS = {"1. khai nhận di sản vũ dương", "1. pcds"}

_LAND_CODE_TOKEN_RE = re.compile(r"^\[(ONT|CLN|NTS|LUC)(?:\s+(\d+))?\]$")
_LAND_CODE_LITERAL_RE = re.compile(r"(?<![\[\w])(ONT|CLN|NTS|LUC)(?![\]\w])")
_PURPOSE_ITEM_RE = re.compile(
    r"(?<![\[\w])(ONT|CLN|NTS|LUC)\s*:\s*\[(ONT|CLN|NTS|LUC)(?:\s+(\d+))?\]\s*m2")


def _context_spans(
    paragraph_text: str, stem_key: str,
) -> tuple[list[tuple[int, int, str, str]], list[str]]:
    """Các đoạn LITERAL cần sửa theo ngữ cảnh trong 1 paragraph đã nối text.

    Trả ``(spans, warnings)`` — span là ``(start, end, replacement,
    old_desc)``; warnings liệt kê ngữ cảnh chưa hỗ trợ/mơ hồ được GIỮ NGUYÊN
    để manifest báo rõ. Chỉ đụng chữ in cứng NGOÀI token ``[...]`` — token
    xử lý qua ``_CONTEXT_TOKEN_RENAMES``.
    """
    from .word_engine import _PLACEHOLDER_RE

    spans: list[tuple[int, int, str, str]] = []
    warnings: list[str] = []
    token_spans = [m.span() for m in _PLACEHOLDER_RE.finditer(paragraph_text)]

    def _inside_token(start: int, end: int) -> bool:
        return any(start < e and end > s for s, e in token_spans)

    if stem_key in _LAND_LABEL_STEMS:
        # Mỗi nhãn "ONT" ghép với đúng TOKEN vị trí của MỤC chứa nó (token
        # cùng mã gần nhất phía sau, hoặc gần nhất phía trước) — hai mục cùng
        # mã ONT nhưng thuộc tài sản 1/2 phải nhận nhãn đúng tài sản đó,
        # không dùng chung một tài sản theo mã cho cả đoạn (review NAIA-12).
        code_tokens: list[tuple[int, str, int, bool]] = []  # (pos, code, asset, used)
        for match in _PLACEHOLDER_RE.finditer(paragraph_text):
            mm = _LAND_CODE_TOKEN_RE.match(match.group(0))
            if mm:
                code_tokens.append(
                    (match.start(), mm.group(1), int(mm.group(2) or 1), False))
        if code_tokens:
            for match in _LAND_CODE_LITERAL_RE.finditer(paragraph_text):
                if _inside_token(match.start(), match.end()):
                    continue
                code = match.group(1)
                token_idx = next(
                    (i for i, (pos, tcode, _a, used) in enumerate(code_tokens)
                     if tcode == code and not used and pos > match.start()),
                    None)
                if token_idx is None:
                    token_idx = next(
                        (i for i in range(len(code_tokens) - 1, -1, -1)
                         if code_tokens[i][1] == code
                         and not code_tokens[i][3]),
                        None)
                if token_idx is None:
                    warnings.append(
                        f"nhãn in cứng \"{code}\" không ghép được token vị "
                        f"trí cùng mục — giữ nguyên")
                    continue
                pos, _code, asset, _used = code_tokens[token_idx]
                code_tokens[token_idx] = (pos, code, asset, True)
                position = LAND_ROW_SLOTS[code]
                spans.append((
                    match.start(), match.end(),
                    f"[Loại đất tài sản {asset}.{position}]",
                    f"nhãn in cứng \"{code}\""))

    if stem_key in _PURPOSE_ENUM_STEMS:
        items = [m for m in _PURPOSE_ITEM_RE.finditer(paragraph_text)
                 if m.group(1) == m.group(2)]
        # Chỉ gộp các mục LIÊN TIẾP hợp lệ (giữa hai mục chỉ có dấu
        # phân cách) — ghi chú/token nằm giữa làm cụm tách rời, không bị
        # span từ mục đầu tới mục cuối nuốt mất (review NAIA-12).
        runs: list[list[Any]] = []
        for item in items:
            if (runs
                    and re.fullmatch(r"[\s;,.]*",
                                     paragraph_text[runs[-1][-1].end()
                                                    :item.start()])):
                runs[-1].append(item)
            else:
                runs.append([item])
        for run in runs:
            assets = {int(m.group(3) or 1) for m in run}
            if len(run) >= 2 and len(assets) == 1:
                spans.append((
                    run[0].start(), run[-1].end(),
                    f"[Mục đích sử dụng {assets.pop()}]",
                    "liệt kê in cứng \"CODE: [CODE] m2\""))
            elif len(run) >= 2:
                warnings.append(
                    "cụm liệt kê \"CODE: [CODE] m2\" trộn nhiều tài sản "
                    f"{sorted(assets)} — ngữ cảnh mơ hồ, giữ nguyên")
    return spans, warnings


def _replace_spans_in_nodes(
    nodes: list[Any], spans: list[tuple[int, int, str, str]],
) -> list[tuple[int, int, str, str]]:
    """Thay các đoạn text ``(start, end)`` trên cụm w:t — literal, không phải
    token. Cùng cơ chế ghép-rồi-thay của ``_replace_pass_in_text_nodes``:
    vùng cắt qua nhiều run ghi vào run đầu, xoá phần text của các run sau.

    Trả các span ĐÃ áp được (để manifest đếm applied chính xác)."""
    texts = [node.text or "" for node in nodes]
    boundaries: list[tuple[int, int, Any]] = []
    offset = 0
    for node, text in zip(nodes, texts):
        boundaries.append((offset, offset + len(text), node))
        offset += len(text)

    applied: list[tuple[int, int, str, str]] = []
    # Duyệt phải -> trái để offset các đoạn bên trái không đổi.
    for span in sorted(spans, reverse=True):
        start, end, value, _desc = span
        segs = [
            (node, max(start, s) - s, min(end, e) - s)
            for s, e, node in boundaries
            if e > start and s < end]
        if not segs:
            continue
        node0, s0, e0 = segs[0]
        node0.text = (node0.text or "")[:s0] + value + (node0.text or "")[e0:]
        for node, s, e in segs[1:]:
            node.text = (node.text or "")[:s] + (node.text or "")[e:]
        applied.append(span)
    return applied


def _apply_context_fixes(
    doc: Any, source_stem: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Sửa ngữ cảnh TRÊN doc đích đang mở theo quyết định Owner.

    Trả ``(fixes, warnings)``: mỗi fix là ``{kind, old, new, applied, note,
    removed_tokens}`` với ``kind`` = ``literal`` (đoạn chữ in cứng — KHÔNG
    phải placeholder nguồn) hoặc ``token`` (đổi tên placeholder thật);
    warnings ghi ngữ cảnh chưa hỗ trợ được giữ nguyên. Không đụng file nào
    ngoài ``doc``; caller giữ quyền ghi — doc được mở/lưu qua fd ràng buộc
    inode của run (review NAIA-12: ghi theo path từng đuổi junction sang
    sentinel và swap sau rewrite từng được manifest chứng nhận)."""
    from docx.oxml.ns import qn

    from .word_engine import (
        _iter_part_paragraphs, _iter_word_part_roots, _paragraph_text_nodes,
        _PLACEHOLDER_RE)

    stem_key = _normalize(source_stem)
    fixes: list[dict[str, Any]] = []
    warnings: list[str] = []
    literal_fix = (stem_key in _LAND_LABEL_STEMS
                   or stem_key in _PURPOSE_ENUM_STEMS)
    renames = _CONTEXT_TOKEN_RENAMES.get(stem_key, {})
    if not literal_fix and not renames:
        return fixes, warnings

    if literal_fix:
        counts: dict[tuple[str, str], int] = {}
        # Token bị thay cùng đoạn gom theo (mô tả đoạn, placeholder đích) —
        # hai cụm cùng mô tả nhưng khác đích KHÔNG đếm chéo removed_tokens
        # (review NAIA-12).
        removed: dict[tuple[str, str], dict[str, int]] = {}
        for part_root in _iter_word_part_roots(doc):
            changed = 0
            for paragraph in _iter_part_paragraphs(part_root.element, qn):
                nodes = _paragraph_text_nodes(paragraph, qn)
                if not nodes:
                    continue
                full = "".join(node.text or "" for node in nodes)
                spans, span_warnings = _context_spans(full, stem_key)
                warnings.extend(span_warnings)
                if not spans:
                    continue
                applied = _replace_spans_in_nodes(nodes, spans)
                changed += len(applied)
                for start, end, new, old_desc in applied:
                    counts[(old_desc, new)] = counts.get((old_desc, new), 0) + 1
                    # Token nằm TRỌN trong đoạn bị thay (liệt kê
                    # "CODE: [CODE] m2") -> gỡ khỏi file, ghi context_fix.
                    bucket = removed.setdefault((old_desc, new), {})
                    for tm in _PLACEHOLDER_RE.finditer(full[start:end]):
                        if _LAND_CODE_TOKEN_RE.match(tm.group(0)):
                            bucket[tm.group(0)] = \
                                bucket.get(tm.group(0), 0) + 1
            if changed:
                part_root.commit()
        for (old_desc, new), count in counts.items():
            fixes.append({
                "kind": "literal",
                "old": old_desc, "new": new, "applied": count,
                "removed_tokens": dict(removed.get((old_desc, new), {})),
                "note": "nhãn/liệt kê in cứng -> placeholder dữ liệu dòng đất "
                        "(Owner 02/10/2026, review NAIA-12)"})
    for old, new in renames.items():
        applied = replace_in_doc(doc, {old: new})
        if applied:
            fixes.append({
                "kind": "token",
                "old": old, "new": new, "applied": applied,
                "removed_tokens": {},
                "note": "đổi tên theo ngữ cảnh tài sản của mẫu "
                        "(Owner 02/10/2026, review NAIA-12)"})
    return fixes, warnings


def _real_path(path: Path) -> Path:
    """Đường dẫn thực (resolve symlink/junction) để so trùng nguồn/đích."""
    import os

    return Path(os.path.realpath(str(path)))


def _norm_key(path: Path) -> str:
    """Khóa so sánh đường dẫn: realpath + normcase (Windows không phân biệt hoa/thường)."""
    import os

    return os.path.normcase(str(_real_path(path)))


def _contained_key(child_key: str, root_key: str) -> bool:
    """``child_key`` (đã realpath+normcase) nằm TRONG ``root_key``?

    Junction Windows không phải symlink (``is_symlink()`` False) nhưng
    ``realpath`` vẫn lộ đích thật — kể cả khi node cuối chưa tồn tại — nên
    containment trên khóa realpath chặn được cả junction lẫn symlink."""
    return child_key.startswith(root_key + "\\") or child_key.startswith(
        root_key + "/")


class _WriteGuard:
    """Guard containment + danh tính file cho mọi lần ghi SAU copy ban đầu.

    ``_plan_migration`` kiểm containment MỘT lần trước khi chạy — nhưng giữa
    plan và từng lần ``doc.save``/rename về sau, một thư mục con của đích
    có thể bị đổi thành junction (Leader tái hiện NAIA-12: context save
    từng đuổi theo junction ghi vào sentinel ngoài đích mà migration vẫn
    success; lượt sau junction đổi sang thư mục khác VẪN TRONG root — key
    realpath mới chưa đăng ký nên guard bỏ qua kiểm danh tính và vẫn ghi đè
    sentinel).

    ``capture_handle`` ghi nhận (realpath key, st_dev, st_ino) của file do
    lần migrate này tạo TỪ CHÍNH fd tạo file còn mở — chứng minh ownership
    mà không đọc lại path sau khi handle đóng (review NAIA-12: ``register``
    từng ``stat()`` path sau đóng handle nên nhận nhầm file cạnh tranh được
    swap vào trước đăng ký). ``register`` chỉ CHỐT danh tính đã capture và
    đối chiếu path vẫn trỏ đúng inode đó — phân biệt đăng ký file MỚI với
    validate file đã đăng ký (``check``/``open_for_rewrite``). ``check``
    raise ``ValueError`` khi:
      - path resolve ra ngoài root;
      - path ĐÃ đăng ký nay resolve sang realpath khác (junction đổi hướng
        sang file khác trong hay ngoài root đều bị bắt);
      - file tại path đã đăng ký không còn cùng danh tính (bị xoá/đổi link/
        đổi inode giữa chừng);
      - path CHƯA đăng ký mà file/link đã tồn tại — chỉ file do run tạo
        mới được phép ghi; file lạ xuất hiện giữa chừng không bị ghi đè.
    """

    def __init__(self, root: Path):
        self.root_key = _norm_key(root).rstrip("\\/")
        # logical path đã plan -> (realpath key lúc đăng ký, file identity)
        self._files: dict[str, tuple[str, tuple[int, int] | None]] = {}
        # logical path -> danh tính đã fstat từ handle tạo, chờ register chốt
        self._pending: dict[str, tuple[str, tuple[int, int]]] = {}

    @staticmethod
    def _logical_key(path: Path) -> str:
        """Khoá đường dẫn logic (KHÔNG resolve junction/link) — file đăng ký
        tại path này phải mãi resolve về đúng realpath đã ghi nhận."""
        import os

        return os.path.normcase(
            os.path.normpath(os.path.abspath(str(path))))

    def capture_handle(self, path: Path, handle) -> None:
        """Ghi nhận danh tính file do run tạo TỪ fd còn mở (``os.fstat``).

        Phải gọi TRƯỚC khi handle tạo đóng — ``os.fstat`` trên fd chứng minh
        inode thuộc run bất kể path bị thay ngay sau đó."""
        import os

        stat = os.fstat(handle.fileno())
        self._pending[self._logical_key(path)] = (
            _norm_key(path), (stat.st_dev, stat.st_ino))

    def register(self, path: Path) -> None:
        """Chốt đăng ký file do run tạo — danh tính lấy từ ``capture_handle``
        của fd tạo file, KHÔNG từ ``stat()`` path (path có thể đã bị đổi
        sang file cạnh tranh sau khi handle đóng — review NAIA-12).

        File bị thay/xoá hoặc path resolve lạc giữa tạo và đăng ký -> raise
        ``ValueError`` thay vì nhận nhầm danh tính file ngoài."""
        key = self._logical_key(path)
        pending = self._pending.pop(key, None)
        if pending is None:
            raise ValueError(
                f"đăng ký file chưa capture handle tạo của run: {path}")
        expected_real, expected = pending
        real_key = _norm_key(path)
        if real_key != expected_real:
            raise ValueError(
                f"đăng ký: {path} không còn resolve về file vừa tạo")
        try:
            stat = Path(path).stat()
        except OSError:
            stat = None
        current = (stat.st_dev, stat.st_ino) if stat is not None else None
        if current != expected:
            raise ValueError(
                f"đăng ký: {path} bị thay/xoá sau khi handle tạo đóng")
        self._files[key] = pending

    def unregister(self, path: Path) -> None:
        key = self._logical_key(path)
        self._files.pop(key, None)
        self._pending.pop(key, None)

    def check(self, path: Path, what: str = "đầu ra") -> None:
        real_key = _norm_key(path)
        if not _contained_key(real_key, self.root_key):
            raise ValueError(
                f"{what} resolve ra ngoài thư mục đích: {path}")
        key = self._logical_key(path)
        entry = self._files.get(key) or self._pending.get(key)
        if entry is None:
            # Đường ghi CHƯA đăng ký chỉ hợp lệ khi là file sắp tạo — một
            # file/link lạ đã xuất hiện tại đây không được phép ghi đè.
            if Path(path).exists() or Path(path).is_symlink():
                raise ValueError(
                    f"{what} đã tồn tại nhưng không phải file do lần "
                    f"migrate này tạo: {path}")
            return
        expected_real, expected = entry
        if real_key != expected_real:
            raise ValueError(
                f"{what} không còn resolve về file đã đăng ký: {path}")
        try:
            stat = Path(path).stat()
        except OSError:
            stat = None
        current = (stat.st_dev, stat.st_ino) if stat is not None else None
        if current != expected:
            raise ValueError(
                f"{what} không còn là file do lần migrate này tạo: {path}")

    def open_bound(self, path: Path, what: str = "đầu ra"):
        """Mở file ĐÃ ĐĂNG KÝ bằng fd ràng buộc đúng inode của run.

        ``check`` + ``doc.save(path)`` còn khe TOCTOU nhỏ (file bị thay giữa
        kiểm và ghi). Mở ``r+b`` rồi ``fstat`` trên chính handle đó chứng
        minh fd trỏ tới inode run đã đăng ký — rename/link ngoài kia không
        đổi được inode mà fd đã mở. Trả handle CHƯA truncate để caller đọc
        nội dung qua cùng fd rồi tự ``seek(0)+truncate(0)`` trước khi save —
        đọc và ghi đều rơi vào inode của run bất kể path bị swap giữa chừng.
        """
        import os

        real_key = _norm_key(path)
        if not _contained_key(real_key, self.root_key):
            raise ValueError(
                f"{what} resolve ra ngoài thư mục đích: {path}")
        key = self._logical_key(path)
        entry = self._files.get(key)
        if entry is None or entry[0] != real_key or entry[1] is None:
            raise ValueError(
                f"{what} không phải file do lần migrate này tạo: {path}")
        handle = open(path, "r+b")
        try:
            stat = os.fstat(handle.fileno())
        except OSError:
            handle.close()
            raise
        if (stat.st_dev, stat.st_ino) != entry[1]:
            handle.close()
            raise ValueError(
                f"{what} không còn là file do lần migrate này tạo: {path}")
        return handle

    def open_for_rewrite(self, path: Path, what: str = "đầu ra"):
        """Như :meth:`open_bound` nhưng ``seek(0)+truncate(0)`` ngay — cho
        bước ghi mới hoàn toàn không cần đọc nội dung hiện tại."""
        handle = self.open_bound(path, what)
        handle.seek(0)
        handle.truncate(0)
        return handle


def _plan_migration(src_dir: Path, out_dir: Path) -> list[tuple[Path, Path, str]]:
    """Kiểm chứng nguồn/đích và trả plan ``(src, out_path, rel_posix)``.

    Chặn TRƯỚC mọi ghi: nguồn ≡ đích (kể cả qua symlink/junction), đích nằm
    trong nguồn hoặc ngược lại, đích trùng một file nguồn, đích đã tồn tại,
    hai nguồn cùng stem .doc/.docx đổ về một file đích, MỌI đầu ra (file
    migrate, manifest) sau khi resolve phải nằm trong
    root đích — thư mục con của đích là junction trỏ ra ngoài thì realpath
    thoát scope -> từ chối, và manifest đã có sẵn cũng từ chối ghi đè.
    Raise lỗi trước khi tạo thư mục hay ghi byte nào — nguồn và đích giữ
    nguyên bytes.
    """
    src_key = _norm_key(src_dir).rstrip("\\/")
    out_key = _norm_key(out_dir).rstrip("\\/")
    if src_key == out_key:
        raise ValueError(
            f"thư mục đích trùng thư mục nguồn: {src_dir}")
    if _contained_key(out_key, src_key) or _contained_key(src_key, out_key):
        raise ValueError(
            f"thư mục đích chồng lấn thư mục nguồn: {out_dir} vs {src_dir}")

    kept, _excluded = scan_source_templates(src_dir)
    src_keys = {_norm_key(path) for path in kept}
    plan: list[tuple[Path, Path, str]] = []
    seen_out: dict[str, str] = {}
    write_targets: list[tuple[Path, str]] = [
        (out_dir / "migration_manifest.json", "manifest")]
    for src in kept:
        rel = src.relative_to(src_dir)
        base_name = rel.with_suffix(".docx").name
        out_path = out_dir / rel.parent / base_name
        out_key_file = _norm_key(out_path)

        if out_key_file in src_keys:
            raise ValueError(
                f"đích trùng file nguồn: {out_path}")
        if out_path.exists() or out_path.is_symlink():
            raise FileExistsError(
                f"file đích đã tồn tại, từ chối ghi đè: {out_path}")
        if out_key_file in seen_out:
            raise ValueError(
                f"hai nguồn đổ về cùng đích (trùng stem .doc/.docx): "
                f"{seen_out[out_key_file]} và {rel.as_posix()} -> {out_path.name}")
        seen_out[out_key_file] = rel.as_posix()
        write_targets.append((out_path, rel.as_posix()))
        plan.append((src, out_path, rel.as_posix()))

    # Mọi đường ghi phải resolve nằm trong root đích (junction ở thư mục con
    # của đích trỏ ra ngoài -> realpath thoát scope -> từ chối toàn plan).
    for path, what in write_targets:
        if not _contained_key(_norm_key(path), out_key):
            raise ValueError(
                f"đầu ra resolve ra ngoài thư mục đích: {what} -> {path}")

    manifest_path = out_dir / "migration_manifest.json"
    if manifest_path.exists() or manifest_path.is_symlink():
        raise FileExistsError(
            f"manifest đã tồn tại, từ chối ghi đè: {manifest_path}")
    return plan


def migrate_templates(
    src_dir: Path,
    out_dir: Path,
    *,
    alias_map: dict[str, str] | None = None,
    registry: Iterable[str] = (),
    no_source: Iterable[str] = (),
    convert: Any = None,
    apply_renames: bool = True,
) -> dict[str, Any]:
    """Chuyển toàn bộ mẫu trong ``src_dir`` sang ``out_dir`` và trả manifest.

    Không bao giờ ghi đè file nguồn lẫn file đích đã có; ``_plan_migration``
    chặn mọi cấu hình nguy hiểm TRƯỚC khi ghi. Manifest ghi số lần xuất hiện
    thật của từng token và sha256 nguồn trước/sau để chứng minh.
    """
    src_dir, out_dir = Path(src_dir), Path(out_dir)
    plan = _plan_migration(src_dir, out_dir)  # mọi kiểm chứng trước mọi ghi
    _kept, excluded = scan_source_templates(src_dir)
    for name in excluded:
        if Path(name).suffix.lower() == ".docm":
            warnings.warn(
                f"Bỏ qua {name}: chưa hỗ trợ DOCM; chỉ nhận DOCX và DOC.",
                UserWarning, stacklevel=2)
    out_dir.mkdir(parents=True, exist_ok=True)
    converter = convert or convert_doc_to_docx
    guard = _WriteGuard(out_dir)
    # Vùng staging convert nằm dưới root đích nhưng NGOÀI danh sách mẫu:
    # tên dot-dir + dot-file `.conv.docx` nên scan_template_dir không nhặt
    # (review NAIA-12: `.conv.docx` sót cạnh output từng lọt vào scan).
    scratch_dir = out_dir / f".naia12-scratch-{uuid.uuid4().hex[:12]}"

    files: list[FileMigration] = []
    for src, out_path, rel_posix in plan:
        # Phòng thủ sâu: re-check containment TẠI THỜI ĐIỂM GHI — junction
        # được tạo giữa plan và write vẫn bị chặn trước khi mở file.
        guard.check(out_path, f"đầu ra {rel_posix}")
        before = sha256_file(src)
        converted = src.suffix.lower() == ".doc"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if converted:
            # COM/converter ghi theo path bên ngoài run — không fstat được
            # handle tạo từ xa. Run TỰ TẠO staging rỗng 'xb' + đọc danh
            # tính NTFS (volume, index) trên fd tạo ngay lúc còn mở:
            # converter ghi IN-PLACE lên file này thì danh tính đọc lại
            # khớp = bằng chứng ownership; converter tạo inode mới (SaveAs2)
            # thì phải trả receipt {"sha256", "identity"} đọc trên handle
            # trong chính tiến trình converter. Danh tính dùng cùng biểu
            # diễn với producer (dwVolumeSerialNumber + file index —
            # ``_file_identity``), KHÔNG phải st_dev của CRT (review
            # NAIA-12). Không chứng minh được -> từ chối, giữ staging,
            # KHÔNG copy/xoá file đang ngồi ở path.
            # Staging nằm trong `.naia12-scratch-*/` ở root đích — dot-dir
            # chứa dot-file nên scan_template_dir không bao giờ nhặt nhầm
            # làm mẫu (staging trước đây nằm cạnh output vẫn là .docx hợp
            # lệ -> lọt vào scan/batch nếu còn sót).
            scratch_dir.mkdir(parents=True, exist_ok=True)
            tmp_conv = scratch_dir / (f".{uuid.uuid4().hex}.conv.docx")
            guard.check(tmp_conv, f"staging convert {rel_posix}")
            with open(tmp_conv, "xb") as staging_handle:
                create_identity = _file_identity(staging_handle)
            if convert is None:
                # Default converter phải kiểm danh tính staging ngay trước
                # khi dispatch Word — staging bị thay -> từ chối.
                receipt = convert_doc_to_docx(
                    src, tmp_conv, staging_identity=create_identity)
            else:
                receipt = converter(src, tmp_conv)
            try:
                with open(tmp_conv, "rb") as conv_handle:
                    conv_identity = _file_identity(conv_handle)
                    payload = conv_handle.read()
            except OSError as exc:
                raise WordUnavailableError(
                    f"converter không tạo được output cho {rel_posix}: "
                    f"{exc}") from exc
            payload_sha256 = hashlib.sha256(payload).hexdigest()
            if isinstance(receipt, dict):
                # Contract chặt nhất: hash + danh tính producer trả về phải
                # khớp đúng file đang đọc — hash đúng mà danh tính lệch
                # (producer hash file khác / file bị thay) vẫn từ chối.
                reported = receipt.get("identity")
                try:
                    reported_identity = (
                        int(reported[0]), int(reported[1]))
                except (TypeError, ValueError, IndexError):
                    reported_identity = None
                verified = (
                    payload_sha256
                        == str(receipt.get("sha256") or "").strip().lower()
                    and reported_identity == conv_identity)
            elif isinstance(receipt, str) and receipt.strip():
                # Receipt chỉ-hash: chỉ chứng minh được khi file còn đúng
                # inode run tạo (ghi in-place); SaveAs2 tạo inode mới thì
                # receipt này không ràng buộc được file -> từ chối (review
                # NAIA-12: receipt hash theo path sau Close từng chứng
                # nhận file cạnh tranh).
                verified = (
                    payload_sha256 == receipt.strip().lower()
                    and conv_identity == create_identity)
            else:
                # Không receipt: chỉ chấp khi file là chính staging run
                # tạo, được ghi in-place — danh tính không đổi chứng minh
                # không có file ngoài nào bị đè.
                verified = conv_identity == create_identity
            if not verified:
                raise ValueError(
                    f"không chứng minh được file do converter tạo cho "
                    f"{rel_posix} — file tại {tmp_conv.name} giữ nguyên, "
                    f"không copy/xoá")
            with open(out_path, "xb") as handle:
                handle.write(payload)
                guard.capture_handle(out_path, handle)
            # KHÔNG dọn staging qua path: Windows không có unlink-theo-fd,
            # stat->unlink luôn còn khe để file cạnh tranh swap vào bị xoá
            # nhầm (review NAIA-12). Staging nằm trong `.naia12-scratch-*`
            # ngoài vùng scan nên giữ lại vô hại — scratch dir chỉ rmdir
            # khi rỗng sau cùng.
        else:
            # 'xb' = tạo-mới độc quyền: file đã tồn tại -> lỗi, không ghi đè.
            with open(out_path, "xb") as handle:
                handle.write(src.read_bytes())
                guard.capture_handle(out_path, handle)
        guard.register(out_path)

        # Occurrence nguồn (để kiểm bảo toàn) — đọc trên file ĐÍCH vừa copy
        # byte-exact của nguồn; xác minh lại danh tính sau khi đọc vì path
        # có thể bị đổi sang junction/file khác giữa chừng (review NAIA-12).
        guard.check(out_path, f"đầu ra {rel_posix} trước đọc token")
        present = _read_tokens(out_path)
        guard.check(out_path, f"đầu ra {rel_posix} sau đọc token")
        tokens = diff_tokens(
            present, alias_map=alias_map, registry=registry,
            no_source=no_source, verified_codes=verified_fixed_codes(src.name),
        )
        record = FileMigration(
            source_name=rel_posix,
            output_name=(Path(rel_posix).parent / out_path.name).as_posix(),
            source_sha256=before,
            converted_from_doc=converted,
            tokens=tokens,
        )
        if apply_renames:
            renames = {
                token.old: token.new
                for token in tokens
                if token.status == "renamed" and token.new
            }
            # Owner đã gỡ 4 token khỏi bộ mẫu -> thực sự xoá khỏi file đích, không
            # chỉ ghi chú (nếu không, export sẽ chết ở chỗ kiểm placeholder sót).
            drops = {
                token.old: _DROP_LOOKUP[_token_key(token.old)]
                for token in tokens
                if token.status == "dropped" and _token_key(token.old) in _DROP_LOOKUP
            }
            # Đọc + mọi biến đổi (rename/drop/context) + ghi lại qua MỘT fd
            # ``r+b`` ràng buộc inode run đã đăng ký: KHÔNG còn bước publish
            # ``tmp.replace(path)`` theo path — file cạnh tranh swap vào
            # đích giữa chừng không bị đè vì fd đi theo inode của run, và
            # cũng không được đọc làm input (review NAIA-12: đích bị swap
            # sau check/trước replace từng bị ghi đè sentinel).
            with guard.open_bound(
                    out_path, f"rewrite {rel_posix}") as handle:
                doc = Document(handle)
                changed = False
                if renames:
                    applied = {
                        old: replace_in_doc(doc, {old: new})
                        for old, new in renames.items()
                    }
                    changed = changed or any(applied.values())
                    for token in tokens:
                        if token.old in applied:
                            token.applied = applied[token.old]
                    # Alias nối tiếp (A->B->C): producer áp các rename theo
                    # THỨ TỰ phase trên cùng một tài liệu, nên output của
                    # phase trước (B) lọt vào phase sau (B->C) khi B cũng
                    # là token nguồn. ``new`` của record phải là ĐÍCH CUỐI
                    # sau mọi phase — đó là token thực sự đứng trong file
                    # đích — chứ không phải alias trực tiếp (review
                    # NAIA-12: record [A]->[B] trong khi file ra [C] làm
                    # replay oracle từ chối oan vì budget [B] đã cạn).
                    phases = [
                        (_token_key(old), new)
                        for old, new in renames.items()]
                    for token in tokens:
                        if token.status != "renamed" or not token.new:
                            continue
                        value = token.old
                        for key, new in phases:
                            if _token_key(value) == key:
                                value = new
                        token.new = value
                    record.notes.append(
                        f"đổi tên {len(renames)} token theo catalog §8 "
                        f"({sum(applied.values())} lần thay)")
                if drops:
                    counts, removed_lines = drop_tokens_in_doc(doc, drops)
                    changed = changed or any(counts.values())
                    for token in tokens:
                        if token.old in counts:
                            token.applied = counts[token.old]
                    record.removed_lines = removed_lines
                    total = sum(counts.values())
                    record.notes.append(
                        f"gỡ {total} token Owner loại bỏ"
                        + (f", xoá {removed_lines} dòng thừa" if removed_lines else "")
                    )
                # Context fix Owner (review NAIA-12): nhãn loại đất in cứng thành
                # placeholder động, token đất của mẫu DK18-N chỉ đúng tài sản N,
                # liệt kê "CODE: [CODE] m2" thành [Mục đích sử dụng 1]. Token đã
                # phân loại được gán status "context_fix" thay vì "kept" để
                # manifest ghi đúng thay đổi cuối cùng; các fix LITERAL tách ra
                # ``literal_fixes``, không cộng vào occurrence placeholder.
                context_fixes, context_warnings = _apply_context_fixes(
                    doc, src.stem)
                changed = changed or bool(context_fixes)
                if changed:
                    handle.seek(0)
                    handle.truncate(0)
                    doc.save(handle)
            # fd rewrite đã đóng: file tại path có thể vừa bị swap sang file
            # cạnh tranh NGAY SAU close — xác minh lại danh tính TRƯỚC khi
            # đọc occurrence / append record / ghi manifest; KHÔNG được
            # ``register`` lại từ path (review NAIA-12: swap sau rewrite
            # từng được manifest chứng nhận applied=1).
            guard.check(out_path, f"đầu ra {rel_posix} sau rewrite")
            for warn in context_warnings:
                record.notes.append(
                    f"ngữ cảnh chưa hỗ trợ, giữ nguyên: {warn}")
            # Ghi nhận hành động context theo normalized key trước; status/
            # applied của từng RECORD nguồn được phân bổ lại ở bước đối
            # chiếu occurrence còn lại bên dưới (không gộp vào một record).
            action_by_key: dict[str, list[dict[str, str]]] = {}
            for fix in context_fixes:
                action = {"new": fix["new"], "note": fix["note"]}
                if fix["kind"] == "token":
                    action_by_key.setdefault(
                        _normalize(fix["old"]), []).append(action)
                for removed_old, removed_count in fix["removed_tokens"].items():
                    action_by_key.setdefault(
                        _normalize(removed_old), []).append(action)
                    # Phòng thủ lineage: spelling gỡ khỏi liệt kê phải có
                    # record nguồn (diff_tokens đã tạo record cho mọi
                    # spelling nguồn — nhánh này không nên xảy ra).
                    if not any(_normalize(t.old) == _normalize(removed_old)
                               for t in tokens):
                        tokens.append(TokenMigration(
                            removed_old, fix["new"], removed_count,
                            "context_fix", fix["note"],
                            applied=removed_count))
                if fix["kind"] == "literal":
                    record.literal_fixes.append({
                        "old": fix["old"], "new": fix["new"],
                        "applied": fix["applied"],
                        "removed_tokens": fix["removed_tokens"],
                        "note": fix["note"]})
            if context_fixes:
                record.notes.append(
                    f"sửa {len(context_fixes)} điểm ngữ cảnh "
                    f"({sum(f['applied'] for f in context_fixes)} thay): "
                    + "; ".join(f"{f['old']} -> {f['new']}"
                                for f in context_fixes[:6]))
            # Phân bổ về TỪNG occurrence nguồn: đếm spelling nguồn CÒN LẠI
            # trong file đích -> applied = count - surviving. Engine khớp
            # token theo dạng chuẩn hoá nên một lần gọi thay mọi spelling
            # cùng key; chỉ đối chiếu spelling nguồn mới biết occurrence
            # nào thực sự đã đổi (review NAIA-12: [ĐỊA CHỈ ĐẤT]+[Địa chỉ
            # đất] cùng key từng gộp applied=2 vào record đầu trong khi
            # record sau báo kept dù occurrence của nó cũng bị thay).
            # Đếm spelling nguồn còn lại trên doc vừa ghi qua bound fd —
            # nội dung doc == nội dung file vừa save nên đếm in-memory tương
            # đương đọc lại file, mà không mở thêm khe path-lookup.
            remaining_by_old: dict[str, int] = {}
            for token_text in collect_placeholder_occurrences(doc):
                remaining_by_old[token_text] = (
                    remaining_by_old.get(token_text, 0) + 1)
            for token in tokens:
                surviving = remaining_by_old.get(token.old, 0)
                fixed = max(0, min(token.count, token.count - surviving))
                if fixed:
                    for action in action_by_key.get(
                            _normalize(token.old), []):
                        if token.status == "context_fix":
                            if token.new != action["new"]:
                                token.note = (
                                    f"{token.note}; một phần -> "
                                    f"{action['new']}")
                        else:
                            token.new = action["new"]
                            token.status = "context_fix"
                            token.note = action["note"]
                token.applied = fixed
            # Kiểm bảo toàn nguồn: tổng ``count`` của mọi record phải bằng
            # đúng số occurrence placeholder thật đã quét ở nguồn — một
            # record lineage sai (thêm token không có ở nguồn) phải làm
            # migrate fail chứ không ra manifest lệch (review NAIA-12).
            if sum(t.count for t in tokens) != len(present):
                raise RuntimeError(
                    f"kiểm bảo toàn thất bại: manifest count="
                    f"{sum(t.count for t in tokens)} khác {len(present)} "
                    f"occurrence nguồn ở {rel_posix}")
            record.applied = True

        after = sha256_file(src)
        if after != before:
            raise RuntimeError(f"file nguồn bị thay đổi trong lúc migrate: {rel_posix}")
        # Danh tính đích phải còn đúng file run NGAY TRƯỚC khi ghi nhận
        # record vào manifest — đầu ra bị swap giữa chừng không được phép
        # thành bằng chứng manifest (review NAIA-12).
        guard.check(out_path, f"đầu ra {rel_posix} trước manifest")
        files.append(record)

    # occurrence/token/applied chỉ đếm PLACEHOLDER THẬT có trong nguồn —
    # các sự kiện sửa chữ in cứng (nhãn/liệt kê literal) ghi riêng ở
    # ``literal_events``, không được cộng vào (review NAIA-12: tổng từng
    # phình 2142 thay vì 2128 placeholder nguồn do đếm cả literal).
    occurrences = {
        "occurrences": sum(t.count for f in files for t in f.tokens),
        "tokens": sum(len(f.tokens) for f in files),
        "applied": sum(t.applied for f in files for t in f.tokens),
        "literal_events": sum(len(f.literal_fixes) for f in files),
    }
    manifest = {
        "schema": "naia12.template-migration.v2",
        "source_dir": str(src_dir),
        "output_dir": str(out_dir),
        "excluded_files": excluded,
        "file_count": len(files),
        "totals": occurrences,
        "files": [item.to_dict() for item in files],
    }
    # Quét lần cuối: mọi đầu ra phải còn đúng danh tính file run trước khi
    # manifest chứng nhận chúng — file bị swap sau rewrite của NÓ thì đã
    # bị chặn trong vòng lặp; đây là phòng thủ cho swap ở file ĐÃ xong.
    for _src_done, out_done, rel_done in plan:
        guard.check(out_done, f"đầu ra {rel_done} trước manifest")
    # 'xb' — plan đã chặn manifest có sẵn; giữ lớp phòng thủ cuối trước race
    # (junction/link đổi giữa chừng không được kéo write ra ngoài đích).
    manifest_path = out_dir / "migration_manifest.json"
    guard.check(manifest_path, "manifest")
    with open(manifest_path, "xb") as handle:
        handle.write(
            json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))
        guard.capture_handle(manifest_path, handle)
    guard.register(manifest_path)
    # Scratch chỉ dọn được khi RỖNG: staging còn lại (convert fail giữa
    # chừng) giữ nguyên để audit — không bao giờ unlink theo path.
    try:
        scratch_dir.rmdir()
    except OSError:
        pass
    return manifest


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Migrate mẫu Word thừa kế")
    parser.add_argument("src_dir")
    parser.add_argument("out_dir")
    parser.add_argument("--registry-json", help="file JSON chứa danh sách token đã có registry")
    parser.add_argument("--no-apply", action="store_true", help="chỉ kiểm kê, không đổi tên")
    args = parser.parse_args(argv)

    registry: list[str] = []
    if args.registry_json:
        registry = json.loads(Path(args.registry_json).read_text(encoding="utf-8"))
    manifest = migrate_templates(
        Path(args.src_dir),
        Path(args.out_dir),
        registry=registry,
        no_source=NO_SOURCE_PLACEHOLDERS,
        apply_renames=not args.no_apply,
    )
    summary = {
        item["output_name"]: item["status_counts"] for item in manifest["files"]
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
