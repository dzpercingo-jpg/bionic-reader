"""DOCX parser using python-docx."""
from __future__ import annotations

import io

from docx import Document
from docx.text.paragraph import Paragraph

from ..models import Block


def parse(data: bytes) -> tuple[list[Block], list[str]]:
    warnings: list[str] = []
    blocks: list[Block] = []
    try:
        doc = Document(io.BytesIO(data))
    except Exception as exc:
        warnings.append(f"Failed to open DOCX: {exc}")
        return blocks, warnings

    for element in _iter_block_items(doc):
        if isinstance(element, Paragraph):
            blocks.extend(_paragraph_to_blocks(element))
        else:
            for row in element.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    blocks.append(Block(type="table_row", text=row_text))

    return blocks, warnings


def _iter_block_items(parent):
    """Yield paragraphs and tables in document order."""
    from docx.document import Document as _Document
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table

    parent_elm = parent.element.body if isinstance(parent, _Document) else parent._element
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def _paragraph_to_blocks(p: Paragraph) -> list[Block]:
    text = (p.text or "").strip()
    if not text:
        return [Block(type="spacer")]
    style = (p.style.name if p.style else "").lower()
    if style.startswith("heading"):
        try:
            level = int(style.replace("heading", "").strip() or "1")
        except ValueError:
            level = 1
        return [Block(type="heading", text=text, level=max(1, min(level, 6)))]
    if "list" in style or style.startswith("bullet"):
        return [Block(type="list_item", text=text, ordered=False)]
    if style.startswith("number"):
        return [Block(type="list_item", text=text, ordered=True)]
    if "quote" in style:
        return [Block(type="blockquote", text=text)]
    return [Block(type="paragraph", text=text)]
