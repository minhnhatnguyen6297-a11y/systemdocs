"""Immutable backend sources addressed by opaque UUID, never client paths."""
import hashlib
import json
import uuid
from pathlib import Path
from .models import MAX_FILE_BYTES


class DocxStore:
    def __init__(self, root):
        self.root = Path(root)

    def save(self, content, suggestions):
        self.root.mkdir(parents=True, exist_ok=True)
        source_id = str(uuid.uuid4())
        folder = self.root / source_id
        folder.mkdir()
        digest = hashlib.sha256(content).hexdigest()
        for suggestion in suggestions:
            for field in suggestion["fields"].values():
                for ref in field["source_refs"]:
                    ref["source_id"] = source_id
        try:
            (folder / "original.docx").write_bytes(content)
            (folder / "extraction.json").write_text(json.dumps({"sha256": digest, "text_map_version": 1,
                "suggestions": suggestions}, ensure_ascii=False), encoding="utf-8")
        except BaseException:
            for name in ("original.docx", "extraction.json"):
                (folder / name).unlink(missing_ok=True)
            folder.rmdir()
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
        package = json.loads((folder / "extraction.json").read_text(encoding="utf-8"))
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
        try:
            with path.open("xb") as handle:
                handle.write(content)
        except FileExistsError:
            if path.read_bytes() != content:
                raise ValueError("Mẫu lưu bị đổi nội dung") from None
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        return digest

    def load_template(self, source_id, digest):
        self.load(source_id)
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError("Hash mẫu Word không hợp lệ")
        content = (self.root / source_id / "templates" / (digest + ".docx")).read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError("Mẫu đã bị đổi nội dung; cần kiểm tra lại")
        return content
