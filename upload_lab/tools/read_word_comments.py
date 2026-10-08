"""Doc comment trong file Word (.docx) lam dap an mau.

Cach dung:
    python tools/read_word_comments.py "file-co-comment.docx"
    -> in ra tung comment: nguoi viet, doan van ban bi boi, noi dung comment.

Gioi han: chi doc comment trong than van ban (ke ca bang); khong doc
comment trong header/footer. File .doc cu khong co comment XML.
"""
from __future__ import annotations

import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _text_of(element: ET.Element) -> str:
    parts = []
    for node in element.iter():
        if node.tag == "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t":
            parts.append(node.text or "")
    return unicodedata.normalize("NFC", "".join(parts))


def read_word_comments(path: str | Path) -> list[dict]:
    """Tra ve list {id, author, date, quoted_text, comment} theo thu tu id."""
    path = Path(path)
    with zipfile.ZipFile(path) as package:
        try:
            comments_xml = package.read("word/comments.xml")
        except KeyError:
            return []
        document_xml = package.read("word/document.xml")

    comments_root = ET.fromstring(comments_xml)
    comments: dict[str, dict] = {}
    for comment in comments_root.findall("w:comment", NS):
        cid = str(comment.get(f"{{{NS['w']}}}id", ""))
        comments[cid] = {
            "id": cid,
            "author": comment.get(f"{{{NS['w']}}}author", ""),
            "date": comment.get(f"{{{NS['w']}}}date", ""),
            "comment": _text_of(comment).strip(),
            "quoted_text": "",
        }

    doc_root = ET.fromstring(document_xml)
    active: list[str] = []
    quoted: dict[str, list[str]] = {cid: [] for cid in comments}

    for node in doc_root.iter():
        tag = node.tag
        if tag == f"{{{NS['w']}}}commentRangeStart":
            cid = str(node.get(f"{{{NS['w']}}}id", ""))
            if cid in comments and cid not in active:
                active.append(cid)
        elif tag == f"{{{NS['w']}}}commentRangeEnd":
            cid = str(node.get(f"{{{NS['w']}}}id", ""))
            if cid in active:
                active.remove(cid)
        elif tag == f"{{{NS['w']}}}t":
            text = node.text or ""
            for cid in active:
                quoted[cid].append(text)

    result = []
    for cid, info in comments.items():
        info["quoted_text"] = unicodedata.normalize("NFC", "".join(quoted[cid])).strip()
        result.append(info)
    return result


def main() -> int:
    if len(sys.argv) < 2:
        print('Cach dung: python tools/read_word_comments.py "file-co-comment.docx"')
        return 1
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Khong tim thay file: {path}")
        return 1
    items = read_word_comments(path)
    if not items:
        print("File nay khong co comment nao.")
        return 0
    for item in items:
        print(f"--- comment {item['id']} (tac gia: {item['author'] or '?'}) ---")
        print(f"Boi vao: {item['quoted_text'] or '(khong ro doan)'}")
        print(f"Noi dung: {item['comment']}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
