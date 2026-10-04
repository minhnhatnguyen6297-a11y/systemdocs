"""Ordered body reader and exact code-point spans; never rebuild paragraphs."""
from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from zipfile import ZipFile

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PART = "word/document.xml"


@dataclass
class DocxSource:
    sha256: str
    text: str
    segments: list[dict]
    warnings: list[str]

    def replacement_reason(self, span):
        refs = self.refs(span)
        if not refs or any(not ref['supported'] for ref in refs):
            return 'Vị trí đi qua vùng Word chưa hỗ trợ sửa'
        styles = {seg.get('style', '') for seg in self.segments
                  if max(span[0], seg['start']) < min(span[1], seg['end'])}
        if len(styles) > 1:
            return 'Vị trí có nhiều kiểu chữ; chưa hỗ trợ thay mà giữ đúng định dạng'
        return None

    def refs(self, span: list[int]) -> list[dict]:
        start, end = span
        result = []
        for seg in self.segments:
            lo, hi = max(start, seg["start"]), min(end, seg["end"])
            if lo < hi:
                result.append({"part": PART, "path": seg["path"],
                               "node_span": [lo - seg["start"], hi - seg["start"]],
                               "supported": seg["supported"]})
        return result


def read_docx(content: bytes) -> DocxSource:
    with ZipFile(io.BytesIO(content)) as package:
        if sum(info.file_size for info in package.infolist()) > 100 * 1024 * 1024:
            raise ValueError("DOCX giải nén vượt giới hạn 100 MB")
        root = etree.fromstring(package.read(PART), etree.XMLParser(resolve_entities=False))
        other_text = [n for n in package.namelist()
                      if n.startswith(("word/header", "word/footer")) and n.endswith(".xml")]
    body = root.find(W + "body")
    if body is None:
        raise ValueError("DOCX thiếu phần nội dung")
    chunks, segments, warnings = [], [], []
    pos = 0
    field_depth = 0

    def emit(value, path, supported, style=''):
        nonlocal pos
        if value:
            segments.append({"start": pos, "end": pos + len(value),
                             "path": path, "supported": supported, "style": style})
            chunks.append(value)
            pos += len(value)

    def walk(node, path, safe=True):
        nonlocal field_depth
        tag = node.tag
        if tag == W + "fldChar":
            kind = node.get(W + "fldCharType")
            if kind == "begin":
                field_depth += 1
            elif kind == "end":
                field_depth = max(0, field_depth - 1)
            return
        if tag == W + "p" and node.find(".//" + W + "fldChar") is not None:
            safe = False
        allowed = {W + s for s in ("body", "p", "r", "tbl", "tr", "tc")}
        if tag == W + "t":
            props = node.getparent().find(W + 'rPr')
            emit(node.text or "", path, safe and field_depth == 0, etree.tostring(props).decode() if props is not None else '')
            return
        if tag in (W + "tab", W + "br", W + "cr"):
            emit("\t" if tag == W + "tab" else "\n", path, False)
            return
        if tag in (W + "pPr", W + "rPr", W + "tblPr", W + "tcPr", W + "trPr", W + "sectPr"):
            return
        child_safe = safe and tag in allowed
        if not child_safe and any(n.tag == W + "t" for n in node.iter()):
            warning = "Vùng chưa hỗ trợ sửa: " + etree.QName(node).localname
            if warning not in warnings:
                warnings.append(warning)
        # Physical XML cells avoid repeating merged cells; recursion preserves nested tables.
        for i, child in enumerate(node):
            walk(child, path + [i], child_safe)
        if tag == W + "p":
            emit("\n", path, False)

    walk(body, [])
    if other_text:
        warnings.append("Chỉ đọc thân văn bản và bảng; đầu/chân trang được giữ nguyên")
    if root.find(".//" + W + "instrText") is not None or root.find(".//" + W + "fldChar") is not None:
        warnings.append("Mã trường Word được giữ nguyên, chưa hỗ trợ gắn vị trí")
    return DocxSource(hashlib.sha256(content).hexdigest(), "".join(chunks), segments, warnings)


def replace_spans(content: bytes, source: DocxSource, replacements: list[tuple[list[int], str]]) -> bytes:
    """Edit only supported w:t slices; all other package entries keep their bytes."""
    if hashlib.sha256(content).hexdigest() != source.sha256:
        raise ValueError("Nguồn Word đã đổi; cần kiểm tra lại vị trí")
    previous_end = -1
    edits = {}
    for span, value in sorted(replacements, key=lambda item: item[0]):
        start, end = span
        if start < previous_end or start < 0 or end <= start or end > len(source.text):
            raise ValueError("Vị trí chồng nhau hoặc không hợp lệ")
        previous_end = end
        refs = source.refs(span)
        reason = source.replacement_reason(span)
        if reason:
            raise ValueError(reason)
        for i, ref in enumerate(refs):
            edits.setdefault(tuple(ref["path"]), []).append((ref["node_span"], str(value) if i == 0 else ""))
    output = io.BytesIO()
    with ZipFile(io.BytesIO(content)) as original, ZipFile(output, "w") as derivative:
        root = etree.fromstring(original.read(PART), etree.XMLParser(resolve_entities=False))
        body = root.find(W + "body")
        for path, slices in edits.items():
            node = body
            for index in path:
                node = node[index]
            if node.tag != W + "t":
                raise ValueError("Bản đồ vị trí không còn khớp")
            text = node.text or ""
            for (start, end), value in sorted(slices, reverse=True):
                text = text[:start] + value + text[end:]
            node.text = text
            node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        for info in original.infolist():
            derivative.writestr(info, etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
                                if info.filename == PART and edits else original.read(info.filename))
    return output.getvalue()
