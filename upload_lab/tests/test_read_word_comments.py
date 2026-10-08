from __future__ import annotations

import unittest
import zipfile
from pathlib import Path

from tools.read_word_comments import read_word_comments

NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.open-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
</Relationships>"""

DOCUMENT = f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="{NS}"><w:body>
<w:p><w:r><w:t>Bà Nguyễn Thị A Sinh ngày: 01/01/1960;</w:t></w:r></w:p>
<w:p><w:commentRangeStart w:id="0"/><w:r><w:t>Ông Trần Văn X chết ngày 29/05/2022.</w:t></w:r><w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p>
<w:p><w:tbl><w:tr><w:tc><w:p><w:commentRangeStart w:id="1"/><w:r><w:t>Thửa 65</w:t></w:r><w:commentRangeEnd w:id="1"/></w:p></w:tc></w:tr></w:tbl></w:p>
</w:body></w:document>"""

COMMENTS = f"""<?xml version="1.0" encoding="UTF-8"?>
<w:comments xmlns:w="{NS}">
<w:comment w:id="0" w:author="Chu" w:date="2026-10-06"><w:p><w:r><w:t>ngay chet</w:t></w:r></w:p></w:comment>
<w:comment w:id="1" w:author="Chu" w:date="2026-10-06"><w:p><w:r><w:t>thua dat so 65</w:t></w:r></w:p></w:comment>
</w:comments>"""


def make_commented_docx(path: Path) -> Path:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", CONTENT_TYPES)
        package.writestr("_rels/.rels", RELS)
        package.writestr("word/document.xml", DOCUMENT)
        package.writestr("word/_rels/document.xml.rels", DOC_RELS)
        package.writestr("word/comments.xml", COMMENTS)
    return path


class ReadWordCommentsTests(unittest.TestCase):
    def test_reads_quoted_text_inside_tables_and_paragraphs(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = make_commented_docx(Path(tmp) / "mau.docx")
            items = read_word_comments(path)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["comment"], "ngay chet")
        self.assertIn("chết ngày 29/05/2022", items[0]["quoted_text"])
        self.assertEqual(items[1]["comment"], "thua dat so 65")
        self.assertEqual(items[1]["quoted_text"], "Thửa 65")

    def test_file_without_comments_returns_empty(self):
        import tempfile

        from docx import Document

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trang.docx"
            Document().save(str(path))
            self.assertEqual(read_word_comments(path), [])


if __name__ == "__main__":
    unittest.main()
