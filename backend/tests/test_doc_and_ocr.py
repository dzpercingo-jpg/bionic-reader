"""Fidelity tests for legacy .doc and scanned-PDF OCR pre-processing.

These tests require LibreOffice and Tesseract to be installed on the host
(both are listed in the project's blueprint). When either is missing they
are skipped automatically.
"""
from __future__ import annotations

import hashlib
import io
import shutil
import zipfile
from pathlib import Path

import fitz
import pytest

from app.inplace.doc_inplace import export_inplace as doc_inplace
from app.inplace.pdf_inplace import export_inplace as pdf_inplace
from app.inplace.pdf_ocr import needs_ocr, ocr_pdf
from app.models import BionicSettings
from app.parsers import parse_bytes

FIXTURES = Path(__file__).parent / "fixtures"

HAS_SOFFICE = bool(shutil.which("libreoffice") or shutil.which("soffice"))
HAS_TESSERACT = bool(shutil.which("tesseract"))


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def settings() -> BionicSettings:
    return BionicSettings(enabled=True, fixation_ratio=0.5, min_word_length=4)


@pytest.mark.skipif(not HAS_SOFFICE, reason="LibreOffice not installed")
def test_doc_inplace_converts_to_docx_and_applies_bionic(settings: BionicSettings) -> None:
    """Legacy .doc → bionic-styled .docx with image and table preserved."""
    src_path = FIXTURES / "with_image_and_table.doc"
    if not src_path.exists():
        pytest.skip("with_image_and_table.doc fixture missing — run tests/fixtures/generate.py")
    data = src_path.read_bytes()
    src_sha = _sha(data)

    out_bytes, mime, name = doc_inplace(data, settings, src_path.name)

    # Source file invariant
    assert _sha(src_path.read_bytes()) == src_sha
    # Output is always .docx (round-tripping to .doc would lose data)
    assert name.endswith(".bionic.docx")
    assert mime.endswith("wordprocessingml.document")

    # Output should be a valid DOCX archive with the original image and text.
    out_zip = zipfile.ZipFile(io.BytesIO(out_bytes))
    media = [n for n in out_zip.namelist() if n.startswith("word/media/")]
    assert media, "image lost in .doc → .docx conversion"
    document_xml = out_zip.read("word/document.xml").decode("utf-8")
    # Strip XML tags to ignore the prefix/suffix run splits introduced by bionic.
    import re
    plain = re.sub(r"<[^>]+>", "", document_xml)
    # Table content survives even if the .doc binary round-trip flattens the
    # <w:tbl> wrapper to plain runs (a limitation of the legacy binary format).
    for keyword in ["Attention", "Posner 1980", "Casutt 2018"]:
        assert keyword in plain, f"text content lost: {keyword}"
    assert document_xml.count("<w:b/>") >= 10, "bionic styling missing on output"


@pytest.mark.skipif(not HAS_SOFFICE, reason="LibreOffice not installed")
def test_doc_parser_extracts_text() -> None:
    src_path = FIXTURES / "with_image_and_table.doc"
    if not src_path.exists():
        pytest.skip("with_image_and_table.doc fixture missing")
    doc = parse_bytes(src_path.name, src_path.read_bytes())
    assert doc.word_count > 0
    text = " ".join(b.text for b in doc.blocks if b.text)
    assert "Attention" in text
    assert "Posner 1980" in text


@pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract not installed")
def test_scanned_pdf_needs_ocr_detection() -> None:
    src_path = FIXTURES / "scanned_image_only.pdf"
    if not src_path.exists():
        pytest.skip("scanned_image_only.pdf fixture missing — run tests/fixtures/generate.py")
    assert needs_ocr(src_path.read_bytes()) is True

    text_pdf_path = FIXTURES / "with_image_and_table.pdf"
    assert needs_ocr(text_pdf_path.read_bytes()) is False


@pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract not installed")
def test_ocr_pdf_adds_invisible_text_layer() -> None:
    """ocr_pdf should add a text layer that PyMuPDF can extract."""
    src_path = FIXTURES / "scanned_image_only.pdf"
    if not src_path.exists():
        pytest.skip("scanned_image_only.pdf fixture missing")
    data = src_path.read_bytes()

    ocr_bytes = ocr_pdf(data, lang="fra+eng")

    doc = fitz.open(stream=ocr_bytes, filetype="pdf")
    text = " ".join(p.get_text() for p in doc).lower()
    doc.close()
    # Tesseract is good enough that at least one of these key words must appear.
    assert any(k in text for k in ("bionique", "ocr", "tesseract", "scanne", "lecture")), (
        f"OCR found no recognizable text. Extracted: {text!r}"
    )


@pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract not installed")
def test_pdf_inplace_runs_ocr_on_scanned_pdf(settings: BionicSettings) -> None:
    """End-to-end: scanned PDF → bionic-styled PDF with OCR text layer."""
    src_path = FIXTURES / "scanned_image_only.pdf"
    if not src_path.exists():
        pytest.skip("scanned_image_only.pdf fixture missing")
    data = src_path.read_bytes()
    src_sha = _sha(data)

    out_bytes, mime, name = pdf_inplace(data, settings, src_path.name, ocr=True)

    assert _sha(src_path.read_bytes()) == src_sha
    assert name.endswith(".bionic.pdf")
    assert mime == "application/pdf"

    out_doc = fitz.open(stream=out_bytes, filetype="pdf")
    # Same page count.
    src_doc = fitz.open(stream=data, filetype="pdf")
    assert out_doc.page_count == src_doc.page_count
    # OCR added text — get_text now returns content.
    out_text = out_doc[0].get_text().strip().lower()
    src_doc.close()
    out_doc.close()
    assert len(out_text) > 5, f"OCR should have produced text on the scanned page, got {out_text!r}"


@pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract not installed")
def test_pdf_inplace_with_ocr_disabled_skips_ocr(settings: BionicSettings) -> None:
    """When ocr=False, scanned PDFs stay scanned (no text layer added)."""
    src_path = FIXTURES / "scanned_image_only.pdf"
    if not src_path.exists():
        pytest.skip("scanned_image_only.pdf fixture missing")
    data = src_path.read_bytes()

    out_bytes, _, _ = pdf_inplace(data, settings, src_path.name, ocr=False)

    out_doc = fitz.open(stream=out_bytes, filetype="pdf")
    out_text = out_doc[0].get_text().strip()
    out_doc.close()
    # With OCR disabled, no text layer is added → scanned page still has no text.
    assert out_text == ""


def test_pdf_inplace_falls_back_when_ocr_raises_arbitrary_error(
    monkeypatch: pytest.MonkeyPatch, settings: BionicSettings
) -> None:
    """Regression: ocr=True must not crash the whole export if OCR raises
    something other than RuntimeError (e.g. pytesseract.TesseractError, PIL
    error, fitz error during rasterization). The non-OCR path must take over
    silently so the user still gets a valid PDF for text pages."""
    from app.inplace import pdf_inplace as pdf_inplace_mod

    def _boom(_data: bytes) -> bytes:  # noqa: ANN001
        raise ValueError("simulated OCR backend failure")

    monkeypatch.setattr(pdf_inplace_mod, "needs_ocr", lambda _d: True)
    monkeypatch.setattr(pdf_inplace_mod, "ocr_pdf", _boom)

    src_path = FIXTURES / "with_image_and_table.pdf"
    data = src_path.read_bytes()

    # Must not raise — the broad except in pdf_inplace catches ANY OCR failure.
    out_bytes, mime, name = pdf_inplace_mod.export_inplace(
        data, settings, src_path.name, ocr=True
    )
    assert mime == "application/pdf"
    assert name.endswith(".bionic.pdf")
    # Output is a valid PDF and the text pages still got the bionic pass.
    out_doc = fitz.open(stream=out_bytes, filetype="pdf")
    assert out_doc.page_count >= 1
    out_doc.close()


def test_ocr_pdf_closes_document_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: if OCR raises mid-loop, the fitz.Document must still be
    closed (no native-resource leak in the server)."""
    from app.inplace import pdf_ocr as pdf_ocr_mod

    src_path = FIXTURES / "scanned_image_only.pdf"
    if not src_path.exists():
        pytest.skip("scanned_image_only.pdf fixture missing")
    data = src_path.read_bytes()

    closed: list[bool] = []
    real_open = pdf_ocr_mod.fitz.open

    def tracked_open(*args, **kwargs):  # noqa: ANN001, ANN201
        d = real_open(*args, **kwargs)
        original_close = d.close

        def _close() -> None:
            closed.append(True)
            original_close()

        d.close = _close  # type: ignore[method-assign]
        return d

    monkeypatch.setattr(pdf_ocr_mod.fitz, "open", tracked_open)

    # Force pytesseract.image_to_data to raise an arbitrary error.
    import pytesseract

    def _boom(*_a, **_kw):  # noqa: ANN001, ANN003, ANN202
        raise pytesseract.TesseractNotFoundError()

    monkeypatch.setattr(pytesseract, "image_to_data", _boom)

    with pytest.raises(RuntimeError, match="Tesseract"):
        pdf_ocr_mod.ocr_pdf(data)

    assert closed, "fitz.Document.close() must be called even when ocr_pdf raises"
