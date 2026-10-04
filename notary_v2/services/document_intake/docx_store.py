"""Immutable backend sources addressed by opaque UUID, never client paths."""
import hashlib
import json
import uuid
import os
import tempfile
import shutil
from pathlib import Path
from .models import MAX_FILE_BYTES


class DocxStore:
    def __init__(self, root):
        self.root = Path(root)

    def save(self, content, suggestions, filename='Hợp đồng Word'):
        self.root.mkdir(parents=True, exist_ok=True)
        source_id = str(uuid.uuid4())
        destination = self.root / source_id
        folder = Path(tempfile.mkdtemp(prefix='.source-', dir=self.root))
        digest = hashlib.sha256(content).hexdigest()
        label = ''.join(c for c in str(filename).replace('\\', '/').split('/')[-1] if c.isprintable())[:180] or 'Hợp đồng Word'
        for suggestion in suggestions:
            for field in suggestion["fields"].values():
                for ref in field["source_refs"]:
                    ref["source_id"] = source_id
                    ref['source_label'] = label
        try:
            (folder / "original.docx").write_bytes(content)
            extraction = json.dumps({"sha256": digest, "text_map_version": 1, 'label': label,
                "suggestions": suggestions}, ensure_ascii=False).encode("utf-8")
            (folder / "extraction.json").write_bytes(extraction)
            (folder / "extraction.sha256").write_text(hashlib.sha256(extraction).hexdigest(), encoding="ascii")
            folder.rename(destination)
        except BaseException:
            shutil.rmtree(folder, ignore_errors=True)
            raise
        return source_id

    def load(self, source_id, sha256=None):
        try:
            if str(uuid.UUID(source_id)) != source_id:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Mã nguồn Word không hợp lệ") from None
        folder = self.root / source_id
        original = folder / "original.docx"
        if original.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("Nguồn Word vượt giới hạn")
        content = original.read_bytes()
        try:
            extraction = (folder / "extraction.json").read_bytes()
            checksum = (folder / "extraction.sha256").read_text(encoding="ascii")
            if len(checksum) != 64 or any(c not in '0123456789abcdef' for c in checksum) or hashlib.sha256(extraction).hexdigest() != checksum:
                raise ValueError()
            package = json.loads(extraction)
            if not isinstance(package, dict):
                raise ValueError()
        except (OSError, UnicodeError, ValueError):
            raise ValueError("Bằng chứng Word thiếu hoặc sai dấu kiểm; hãy nhập và kiểm tra lại") from None
        digest = hashlib.sha256(content).hexdigest()
        if digest != package["sha256"] or (sha256 is not None and digest != sha256) or package.get("text_map_version") != 1:
            raise ValueError("Nguồn Word đã đổi; hãy nhập và kiểm tra lại")
        return content, package

    def save_template(self, source_id, content):
        self.load(source_id)
        digest = hashlib.sha256(content).hexdigest()
        folder = self.root / source_id / "templates"
        folder.mkdir(exist_ok=True)
        path = folder / (digest + ".docx")
        temp = None
        try:
            with tempfile.NamedTemporaryFile(prefix='.template-', dir=folder, delete=False) as handle:
                temp = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temp, path)  # Atomic publication, never replace an existing immutable file.
            except FileExistsError:
                if path.read_bytes() != content:
                    raise ValueError("Mẫu lưu bị đổi nội dung") from None
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
        return digest

    def load_template(self, source_id, digest):
        self.load(source_id)
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError("Hash mẫu Word không hợp lệ")
        content = (self.root / source_id / "templates" / (digest + ".docx")).read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError("Mẫu đã bị đổi nội dung; cần kiểm tra lại")
        return content
