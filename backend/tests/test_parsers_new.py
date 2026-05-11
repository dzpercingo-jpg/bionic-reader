"""Smoke tests for the new PPTX and XLSX parsers."""
from __future__ import annotations

from pathlib import Path

from app.parsers import parse_bytes

FIXTURES = Path(__file__).parent / "fixtures"


def test_pptx_parser_flattens_to_blocks() -> None:
    src = FIXTURES / "with_image_and_table.pptx"
    doc = parse_bytes(src.name, src.read_bytes())
    assert doc.format == "pptx"
    assert doc.word_count > 0
    types = [b.type for b in doc.blocks]
    assert "heading" in types
    assert "paragraph" in types or "table_row" in types


def test_xlsx_parser_flattens_to_blocks() -> None:
    src = FIXTURES / "with_formula_and_image.xlsx"
    doc = parse_bytes(src.name, src.read_bytes())
    assert doc.format == "xlsx"
    assert doc.word_count > 0
    types = [b.type for b in doc.blocks]
    assert "heading" in types
    assert "table_row" in types
    # The formula B4 = =SUM(B2:B3) should appear in some row
    plain = "\n".join(b.text for b in doc.blocks)
    assert "=SUM" in plain or "Total" in plain
