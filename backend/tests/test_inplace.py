"""Fidelity tests for in-place exporters.

For each format, verifies that:
1. The source file on disk is byte-unchanged after export.
2. Images, tables, formulas, page count, and structural data survive.
3. Bionic styling is actually applied (bold markup count > 0).
"""
from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

import pytest

from app.inplace.docx_inplace import export_inplace as docx_inplace
from app.inplace.pdf_inplace import export_inplace as pdf_inplace
from app.inplace.pptx_inplace import export_inplace as pptx_inplace
from app.inplace.xlsx_inplace import export_inplace as xlsx_inplace
from app.models import BionicSettings

FIXTURES = Path(__file__).parent / "fixtures"


def _sha(path_or_bytes) -> str:
    data = path_or_bytes if isinstance(path_or_bytes, bytes) else Path(path_or_bytes).read_bytes()
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def settings() -> BionicSettings:
    return BionicSettings(enabled=True, fixation_ratio=0.5, min_word_length=4)


# ---------- DOCX ----------


def test_docx_inplace_preserves_image_and_table(settings: BionicSettings) -> None:
    src_path = FIXTURES / "with_image_and_table.docx"
    data = src_path.read_bytes()
    src_sha = _sha(data)

    out_bytes, mime, name = docx_inplace(data, settings, src_path.name)

    # 1. source untouched on disk
    assert _sha(src_path) == src_sha
    assert name.endswith(".bionic.docx")
    assert mime.endswith("wordprocessingml.document")

    # 2. structure preserved
    src_zip = zipfile.ZipFile(io.BytesIO(data))
    out_zip = zipfile.ZipFile(io.BytesIO(out_bytes))
    src_media = {n for n in src_zip.namelist() if n.startswith("word/media/")}
    out_media = {n for n in out_zip.namelist() if n.startswith("word/media/")}
    assert src_media == out_media
    for n in src_media:
        # 3. image bytes byte-identical
        assert src_zip.read(n) == out_zip.read(n), f"image modified: {n}"

    out_xml = out_zip.read("word/document.xml").decode("utf-8")
    # 4. bionic styling actually applied
    assert out_xml.count("<w:b/>") >= 20

    # 5. table content survives (search after stripping tags)
    import re
    plain = re.sub(r"<[^>]+>", "", out_xml)
    for keyword in ["Concept", "Description", "Attention", "Posner 1980", "Casutt 2018"]:
        assert keyword in plain, f"lost: {keyword}"


def test_docx_inplace_preserves_original_italic(settings: BionicSettings) -> None:
    """The fixture contains an italic+red run that must survive."""
    src_path = FIXTURES / "with_image_and_table.docx"
    out_bytes, _, _ = docx_inplace(src_path.read_bytes(), settings, src_path.name)
    out_xml = zipfile.ZipFile(io.BytesIO(out_bytes)).read("word/document.xml").decode("utf-8")
    assert "<w:i/>" in out_xml, "original italic lost"


# ---------- PPTX ----------


def test_pptx_inplace_preserves_image_and_table(settings: BionicSettings) -> None:
    src_path = FIXTURES / "with_image_and_table.pptx"
    data = src_path.read_bytes()
    src_sha = _sha(data)

    out_bytes, mime, name = pptx_inplace(data, settings, src_path.name)

    assert _sha(src_path) == src_sha
    assert name.endswith(".bionic.pptx")
    assert mime.endswith("presentationml.presentation")

    src_zip = zipfile.ZipFile(io.BytesIO(data))
    out_zip = zipfile.ZipFile(io.BytesIO(out_bytes))
    src_media = {n for n in src_zip.namelist() if n.startswith("ppt/media/")}
    out_media = {n for n in out_zip.namelist() if n.startswith("ppt/media/")}
    assert src_media == out_media
    for n in src_media:
        assert src_zip.read(n) == out_zip.read(n), f"image modified: {n}"

    total_bold = 0
    for n in out_zip.namelist():
        if n.startswith("ppt/slides/slide") and n.endswith(".xml"):
            total_bold += out_zip.read(n).decode("utf-8").count('b="1"')
    assert total_bold >= 10

    # Re-open with python-pptx to ensure file is valid
    from pptx import Presentation
    prs = Presentation(io.BytesIO(out_bytes))
    assert len(prs.slides) == 1


# ---------- XLSX ----------


def test_xlsx_inplace_preserves_formulas_and_image(settings: BionicSettings) -> None:
    src_path = FIXTURES / "with_formula_and_image.xlsx"
    data = src_path.read_bytes()
    src_sha = _sha(data)

    out_bytes, mime, name = xlsx_inplace(data, settings, src_path.name)

    assert _sha(src_path) == src_sha
    assert name.endswith(".bionic.xlsx")
    assert mime.endswith("spreadsheetml.sheet")

    src_zip = zipfile.ZipFile(io.BytesIO(data))
    out_zip = zipfile.ZipFile(io.BytesIO(out_bytes))
    src_media = {n for n in src_zip.namelist() if n.startswith("xl/media/")}
    out_media = {n for n in out_zip.namelist() if n.startswith("xl/media/")}
    assert src_media == out_media
    for n in src_media:
        assert src_zip.read(n) == out_zip.read(n), f"image modified: {n}"

    # Formula cell must remain a formula (not rich-text).
    from openpyxl import load_workbook
    from openpyxl.cell.rich_text import CellRichText
    wb = load_workbook(io.BytesIO(out_bytes), rich_text=True)
    ws = wb.active
    b4 = ws["B4"].value
    assert isinstance(b4, str) and b4.startswith("="), f"formula corrupted: {b4!r}"
    c2 = ws["C2"].value
    assert isinstance(c2, CellRichText), "Long string cell should be rich-text now"


# ---------- PDF ----------


def test_pdf_inplace_preserves_image_and_page_count(settings: BionicSettings) -> None:
    import fitz
    src_path = FIXTURES / "with_image_and_table.pdf"
    data = src_path.read_bytes()
    src_sha = _sha(data)

    out_bytes, mime, name = pdf_inplace(data, settings, src_path.name)

    assert _sha(src_path) == src_sha
    assert name.endswith(".bionic.pdf")
    assert mime == "application/pdf"

    src_doc = fitz.open(stream=data, filetype="pdf")
    out_doc = fitz.open(stream=out_bytes, filetype="pdf")

    assert src_doc.page_count == out_doc.page_count
    for i in range(src_doc.page_count):
        assert src_doc[i].rect == out_doc[i].rect

    # Image byte-equality
    for i in range(src_doc.page_count):
        src_imgs = src_doc[i].get_images(full=True)
        out_imgs = out_doc[i].get_images(full=True)
        assert len(out_imgs) >= len(src_imgs)
        for src_img in src_imgs:
            src_pix = fitz.Pixmap(src_doc, src_img[0])
            src_sha_img = hashlib.sha256(src_pix.tobytes("png")).hexdigest()
            found = False
            for out_img in out_imgs:
                out_pix = fitz.Pixmap(out_doc, out_img[0])
                if hashlib.sha256(out_pix.tobytes("png")).hexdigest() == src_sha_img:
                    found = True
                    break
            assert found, "an image was modified by the PDF in-place exporter"

    # Words preserved (possibly split into prefix+suffix)
    src_words = {w[4] for w in src_doc[0].get_text("words")}
    out_words = {w[4] for w in out_doc[0].get_text("words")}
    out_text = " ".join(w[4] for w in out_doc[0].get_text("words"))
    for sw in src_words:
        if len(sw) < 3:
            continue
        if sw in out_text:
            continue
        # Check reconstruction by split
        found = any(sw[:i] in out_words and sw[i:] in out_words for i in range(1, len(sw)))
        assert found, f"word missing: {sw!r}"


def test_pdf_inplace_disabled_settings_makes_no_change(settings: BionicSettings) -> None:
    """When bionic is disabled, the output should be a valid PDF (page count/images preserved)."""
    import fitz
    src_path = FIXTURES / "with_image_and_table.pdf"
    data = src_path.read_bytes()
    disabled = BionicSettings(enabled=False)
    out_bytes, _, _ = pdf_inplace(data, disabled, src_path.name)

    src_doc = fitz.open(stream=data, filetype="pdf")
    out_doc = fitz.open(stream=out_bytes, filetype="pdf")
    assert src_doc.page_count == out_doc.page_count
    # With disabled prefix length is 0, so no redaction at all — text should be identical
    src_text = src_doc[0].get_text()
    out_text = out_doc[0].get_text()
    assert out_text.strip() == src_text.strip(), "Disabled bionic should not alter the PDF text"
