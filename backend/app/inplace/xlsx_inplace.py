"""XLSX in-place bionic transformation.

Walks every cell of every worksheet. For cells containing plain string
values, replaces the value with a `CellRichText` composed of bionic
prefix-bold + suffix-normal `TextBlock` segments. The cell's existing
font (name, size, color) is preserved on every chunk via `InlineFont`.

What is *never* touched:
- Formula cells (any cell whose value starts with `=`)
- Numeric, date, boolean cells
- Charts, images, conditional formatting, named ranges
- Sheet order, hidden rows/columns, freeze panes
- Cell borders, fill, alignment

Requires openpyxl >= 3.1.
"""
from __future__ import annotations

import io
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont

from ..models import BionicSettings
from ..transformer import WORD_RE, _prefix_length


def export_inplace(
    data: bytes,
    settings: BionicSettings,
    filename: str = "workbook.xlsx",
) -> tuple[bytes, str, str]:
    wb = load_workbook(io.BytesIO(data), rich_text=True)
    if settings.enabled:
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for cell in row:
                    _process_cell(cell, settings)
    buf = io.BytesIO()
    wb.save(buf)
    stem = Path(filename).stem or "workbook"
    return (
        buf.getvalue(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        f"{stem}.bionic.xlsx",
    )


def _process_cell(cell, settings: BionicSettings) -> None:
    val = cell.value
    if val is None:
        return
    # Already rich text? Skip — we don't yet handle re-styling rich-text.
    if isinstance(val, CellRichText):
        return
    if not isinstance(val, str):
        return
    # Don't touch formulas.
    if val.startswith("="):
        return
    # Don't touch hyperlinks / very short cells (avoid useless work).
    if len(val.strip()) < 4:
        return

    chunks = _compute_chunks(val, settings)
    if len(chunks) <= 1 or all(not is_prefix for _, is_prefix in chunks):
        return

    font = cell.font
    base_color = None
    if font and font.color and getattr(font.color, "rgb", None):
        rgb = font.color.rgb
        if isinstance(rgb, str) and len(rgb) >= 6:
            base_color = rgb[-6:]

    base_kwargs = dict(
        rFont=font.name if font else None,
        sz=int(font.size) if font and font.size else 11,
    )
    if base_color:
        base_kwargs["color"] = base_color
    base_font = InlineFont(**base_kwargs)
    bold_font = InlineFont(b=True, **base_kwargs)

    parts: list = []
    for text, is_prefix in chunks:
        if not text:
            continue
        parts.append(TextBlock(bold_font if is_prefix else base_font, text))
    cell.value = CellRichText(parts)


def _compute_chunks(text: str, settings: BionicSettings) -> list[tuple[str, bool]]:
    chunks: list[tuple[str, bool]] = []
    last_end = 0
    for match in WORD_RE.finditer(text):
        start, end = match.span()
        if start > last_end:
            chunks.append((text[last_end:start], False))
        word = match.group(0)
        plen = _prefix_length(word, settings)
        if plen > 0:
            chunks.append((word[:plen], True))
            if plen < len(word):
                chunks.append((word[plen:], False))
        else:
            chunks.append((word, False))
        last_end = end
    if last_end < len(text):
        chunks.append((text[last_end:], False))
    return chunks
