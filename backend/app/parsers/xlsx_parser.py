"""XLSX parser — flattens worksheets into DocumentModel blocks for in-app
reading. Read-only; never modifies the source workbook.

For fidelity-preserving EXPORT use `app/inplace/xlsx_inplace.py`.
"""
from __future__ import annotations

import io

from openpyxl import load_workbook
from openpyxl.cell.rich_text import CellRichText

from ..models import Block


def parse(data: bytes) -> tuple[list[Block], list[str]]:
    warnings: list[str] = []
    blocks: list[Block] = []
    try:
        wb = load_workbook(io.BytesIO(data), data_only=False, rich_text=True)
    except Exception as exc:
        warnings.append(f"Failed to open XLSX: {exc}")
        return blocks, warnings

    for ws in wb.worksheets:
        blocks.append(Block(type="heading", text=f"Feuille : {ws.title}", level=2))
        rows_emitted = 0
        for row in ws.iter_rows():
            cells: list[str] = []
            for cell in row:
                val = cell.value
                if val is None:
                    cells.append("")
                elif isinstance(val, CellRichText):
                    cells.append(str(val))
                else:
                    cells.append(str(val))
            row_text = " | ".join(c for c in cells)
            if row_text.strip():
                blocks.append(Block(type="table_row", text=row_text.strip()))
                rows_emitted += 1
            if rows_emitted > 500:
                warnings.append(f"Feuille « {ws.title} » tronquée à 500 lignes pour la lecture.")
                break
        blocks.append(Block(type="spacer"))

    return blocks, warnings
