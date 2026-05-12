"""OCR quality benchmarks for the in-place scanned-PDF pipeline.

Measures word-level Precision / Recall / F1 against ground truth on a
realistic scanned fixture (noise + blur + rotation + DejaVu Serif).
Documents the post-bionic readability requirement: even after the
in-place bionic pass redacts/reinserts prefixes, the extractable text
must remain coherent (F1 ≥ 0.9 against ground truth).

These tests are skipped if Tesseract isn't on PATH.
"""
from __future__ import annotations

import re
import shutil
from collections import Counter
from pathlib import Path

import fitz
import pytest

from app.inplace.pdf_inplace import export_inplace as pdf_inplace
from app.inplace.pdf_ocr import _ocr_with_ocrmypdf, _ocr_with_tesseract, ocr_pdf
from app.models import BionicSettings

FIXTURES = Path(__file__).parent / "fixtures"
HAS_TESSERACT = bool(shutil.which("tesseract"))


def _words(s: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z']+", s)]


def _f1(predicted: str, truth: str) -> tuple[float, float, float]:
    pred_c = Counter(_words(predicted))
    truth_c = Counter(_words(truth))
    overlap = sum((pred_c & truth_c).values())
    precision = overlap / max(1, sum(pred_c.values()))
    recall = overlap / max(1, sum(truth_c.values()))
    f1 = 2 * precision * recall / max(1e-9, precision + recall)
    return precision, recall, f1


def _extract_text(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return " ".join(p.get_text() for p in doc)
    finally:
        doc.close()


@pytest.fixture
def realistic_scan() -> tuple[bytes, str]:
    pdf_path = FIXTURES / "scanned_realistic.pdf"
    gt_path = FIXTURES / "scanned_realistic.gt.txt"
    if not (pdf_path.exists() and gt_path.exists()):
        pytest.skip("scanned_realistic fixture missing — run tests/fixtures/generate.py")
    return pdf_path.read_bytes(), gt_path.read_text(encoding="utf-8")


@pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract not installed")
def test_ocr_pdf_realistic_fixture_word_f1(realistic_scan: tuple[bytes, str]) -> None:
    """OCR (whichever engine is selected) must recognise ≥90 % of words."""
    pdf, gt = realistic_scan
    out = ocr_pdf(pdf, lang="fra+eng")
    text = _extract_text(out)
    p, r, f1 = _f1(text, gt)
    assert f1 >= 0.90, (
        f"OCR word-F1 too low: P={p:.3f} R={r:.3f} F1={f1:.3f}\n--- got ---\n{text}"
    )


@pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract not installed")
def test_ocr_post_bionic_text_is_coherent(realistic_scan: tuple[bytes, str]) -> None:
    """After the in-place bionic pass on an OCR'd PDF, the extractable text
    must STILL be coherent — no prefix/suffix fragmentation that destroys
    word boundaries. This is the regression test for the previously-known
    'OCR doesn't seem to work' issue: the OCR layer was being redacted by
    the bionic pass, producing 'Vo\\nici' instead of 'Voici'."""
    pdf, gt = realistic_scan
    settings = BionicSettings(enabled=True, fixation_ratio=0.5, min_word_length=4)
    out, _, _ = pdf_inplace(pdf, settings, "scanned_realistic.pdf")
    text = _extract_text(out)
    p, r, f1 = _f1(text, gt)
    assert f1 >= 0.90, (
        f"post-bionic OCR text fragmented: P={p:.3f} R={r:.3f} F1={f1:.3f}\n"
        f"--- got ---\n{text}"
    )


@pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract not installed")
def test_ocrmypdf_vs_tesseract_baseline(realistic_scan: tuple[bytes, str]) -> None:
    """Document the quality delta between the primary (ocrmypdf) and the
    fallback (manual pytesseract) engines on the realistic fixture.

    Both must be ≥ 0.85 F1 in absolute terms; we don't enforce strict
    ordering because on very easy text both pipelines saturate.
    """
    pdf, gt = realistic_scan
    try:
        primary = _ocr_with_ocrmypdf(pdf, "fra+eng")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"ocrmypdf primary engine not usable: {exc}")
    fallback = _ocr_with_tesseract(pdf, "fra+eng")

    _, _, f1_primary = _f1(_extract_text(primary), gt)
    _, _, f1_fallback = _f1(_extract_text(fallback), gt)
    assert f1_primary >= 0.85, f"ocrmypdf F1 too low: {f1_primary:.3f}"
    assert f1_fallback >= 0.85, f"manual tesseract F1 too low: {f1_fallback:.3f}"
