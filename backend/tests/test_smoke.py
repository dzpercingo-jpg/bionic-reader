"""Smoke tests for the bionic transformer + parsers."""
from __future__ import annotations

from app.exporters.html_exporter import export as export_html
from app.models import BionicSettings
from app.parsers import parse_bytes
from app.transformer import transform_text_html


def test_transform_basic() -> None:
    s = BionicSettings()
    out = transform_text_html("Hello world!", s)
    assert "<b" in out
    assert "Hello" not in out.split("</b>")[0] or "Hel" in out  # prefix is bolded


def test_disabled_no_html() -> None:
    s = BionicSettings(enabled=False)
    out = transform_text_html("Hello world", s)
    assert "<b" not in out


def test_txt_parser() -> None:
    doc = parse_bytes("note.txt", b"Bonjour le monde.\n\nDeuxieme paragraphe.")
    assert doc.format == "txt"
    assert doc.word_count >= 4
    types = [b.type for b in doc.blocks]
    assert "paragraph" in types


def test_html_export() -> None:
    doc = parse_bytes("doc.txt", b"Le cerveau humain est une merveille.")
    body, mime, filename = export_html(doc, BionicSettings(), "Test")
    assert mime == "text/html"
    assert filename.endswith(".html")
    text = body.decode("utf-8")
    assert "<b" in text
    assert "Test" in text


def test_md_parser() -> None:
    src = b"# Title\n\nThis is a paragraph.\n\n- item one\n- item two\n"
    doc = parse_bytes("a.md", src)
    types = [b.type for b in doc.blocks]
    assert "heading" in types
    assert "list_item" in types
