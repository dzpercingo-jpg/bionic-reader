"""PDF in-place bionic transformation via PyMuPDF.

Strategy (preserves images, vectors, signatures, annotations, page count,
metadata):

1. For every text page, walk `get_text("rawdict")` to get each character's
   bbox + font + size + color (`rawdict` exposes per-char data which
   `dict` does not).
2. For each word, compute the bionic prefix length and gather the bboxes
   of the *prefix characters*.
3. Add a redaction annotation on the union of those prefix bboxes.
4. Apply redactions with `images=PDF_REDACT_IMAGE_NONE` — this means images
   and vector graphics are left **completely intact** even if a redaction
   rectangle happens to touch them. Only the matching text in the
   content stream is removed.
5. Re-insert the prefix text at the same position using a Base-14 bold
   font (Helvetica-Bold by default, Times-Bold / Courier-Bold heuristics
   based on the original font name).

Why not just draw an overlay on top? Because PDF readers extract text by
content-stream order, and overlay text would cause selection / accessibility
duplicates ("ABCABC...") and copy/paste artifacts. Redaction + re-insertion
keeps each character once in the content stream — copy/paste still works,
search still works, screen readers still read the page correctly.

Limitations (documented for the user):
- Custom embedded fonts cannot be replicated exactly. We fall back to a
  Base-14 bold font (always present in every PDF reader). For most
  documents the visual difference is minor; mathematical / symbol heavy
  documents may show fallback boxes.
- Right-to-left scripts (Arabic, Hebrew) are not supported.
- Scanned PDFs (image-only, no text layer) cannot be bionic-ified
  in-place without OCR — a separate OCR pre-processing step is required
  (see `pdf_ocr_inplace`).
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from ..models import BionicSettings
from ..transformer import WORD_RE, _prefix_length
from .pdf_ocr import needs_ocr, ocr_pdf

# PyMuPDF char_flags bit 0 indicates "text is rendered with fill". OCR layers
# from ocrmypdf are inserted with render_mode 3 (invisible), so this bit is
# clear. Native PDF text has it set.
_CHAR_FLAG_FILL = 0x01


@dataclass(frozen=True)
class Overlay:
    """One bionic prefix — the original bbox to redact, plus the exact
    baseline origin and render mode used to reinsert the bold text."""
    rect: fitz.Rect
    text: str
    fsize: float
    color: tuple[float, float, float]
    font_hint: str
    origin_x: float
    origin_y: float
    is_ocr: bool  # True → the underlying span is an invisible OCR layer


def export_inplace(
    data: bytes,
    settings: BionicSettings,
    filename: str = "document.pdf",
    ocr: bool = True,
) -> tuple[bytes, str, str]:
    """Bionic-style a PDF in-place.

    If `ocr=True` (default) and the PDF has at least one page without a usable
    text layer (scanned), Tesseract OCR is run first to add an invisible text
    layer to those pages so the bionic styling has something to anchor to.
    Pages that already have selectable text are not OCR'd.
    """
    if ocr:
        try:
            if needs_ocr(data):
                data = ocr_pdf(data)
        except Exception:
            # OCR unavailable or failed (Tesseract missing, bad language pack,
            # PIL/fitz raster error, etc.) — fall back to the non-OCR path.
            # The caller will see a PDF with no bionic bold on scanned pages
            # but the file is still valid and other pages still get styled.
            pass

    doc = fitz.open(stream=data, filetype="pdf")
    if settings.enabled:
        for page in doc:
            _process_page(page, settings)

    buf = io.BytesIO()
    doc.save(buf, garbage=3, deflate=True, clean=False)
    doc.close()
    stem = Path(filename).stem or "document"
    return (
        buf.getvalue(),
        "application/pdf",
        f"{stem}.bionic.pdf",
    )


def _process_page(page: fitz.Page, settings: BionicSettings) -> None:
    raw = page.get_text("rawdict")
    overlays: list[Overlay] = []

    for block in raw.get("blocks", []):
        if block.get("type", 0) != 0:
            continue  # image / drawing
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                _collect_span_overlays(span, settings, overlays)

    if not overlays:
        return

    # Separate OCR'd overlays from native-text overlays. For native text we
    # do the classical redact+reinsert. For OCR'd pages (the user sees a
    # rendered image, the text layer is invisible) we leave the text layer
    # ALONE and add a subtle visible highlight under the prefix so the
    # bionic emphasis is visible without fragmenting the selectable text.
    native = [o for o in overlays if not o.is_ocr]
    ocr_layer = [o for o in overlays if o.is_ocr]

    # --- Native text path -----------------------------------------------
    if native:
        for o in native:
            page.add_redact_annot(o.rect)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        for o in native:
            bold_fontname = _pick_bold_font(o.font_hint)
            try:
                page.insert_text(
                    (o.origin_x, o.origin_y),
                    o.text,
                    fontname=bold_fontname,
                    fontsize=o.fsize,
                    color=o.color,
                    render_mode=0,
                    overlay=True,
                )
            except Exception:
                page.draw_line(
                    (o.rect.x0, o.rect.y1 + 0.5),
                    (o.rect.x1, o.rect.y1 + 0.5),
                    color=o.color,
                    width=0.8,
                )

    # --- OCR (scanned-page) path ---------------------------------------
    # Draw a thin gray underline beneath the prefix portion of each OCR'd
    # word. The rendered scan stays visually intact; the OCR text layer
    # is not redacted so `get_text()` keeps producing coherent line text
    # like ocrmypdf wrote it. The underline is what makes the bionic
    # emphasis visible to the user on top of the page image.
    for o in ocr_layer:
        try:
            y = o.rect.y1 + max(0.6, o.fsize * 0.06)
            page.draw_line(
                (o.rect.x0, y),
                (o.rect.x1, y),
                color=(0.10, 0.10, 0.10),
                width=max(0.8, o.fsize * 0.07),
            )
        except Exception:
            continue


def _collect_span_overlays(
    span: dict,
    settings: BionicSettings,
    out: list,
) -> None:
    chars = span.get("chars", [])
    if not chars:
        return
    font_name = span.get("font", "") or ""
    font_size = float(span.get("size", 11) or 11)
    color_int = int(span.get("color", 0))
    r = ((color_int >> 16) & 0xFF) / 255.0
    g = ((color_int >> 8) & 0xFF) / 255.0
    b = (color_int & 0xFF) / 255.0
    color = (r, g, b)

    # Detect invisible (OCR-generated) text. ocrmypdf writes glyph-stretched
    # invisible text where the FILL char_flag bit is unset (no fill paint).
    # On OCR pages we keep the text layer untouched and instead draw a
    # visible highlight, so the underlying selectable text stays coherent.
    char_flags = int(span.get("char_flags", 0))
    is_ocr = (char_flags & _CHAR_FLAG_FILL) == 0

    # Reconstruct the text string aligned with chars (one entry per char).
    text = "".join((c.get("c", "") or "") for c in chars)

    for match in WORD_RE.finditer(text):
        start, end = match.span()
        word = match.group(0)
        plen = _prefix_length(word, settings)
        if plen <= 0:
            continue
        prefix_chars = chars[start : start + plen]
        if not prefix_chars or len(prefix_chars) != plen:
            continue

        bboxes = [pc.get("bbox") for pc in prefix_chars if pc.get("bbox")]
        if not bboxes:
            continue
        x0 = min(bb[0] for bb in bboxes)
        y0 = min(bb[1] for bb in bboxes)
        x1 = max(bb[2] for bb in bboxes)
        y1 = max(bb[3] for bb in bboxes)
        rect = fitz.Rect(x0, y0, x1, y1)
        if rect.is_empty or rect.is_infinite:
            continue

        # Pull the EXACT baseline from the first prefix char's origin.
        # PyMuPDF stores `origin = (x, baseline_y)` per char in rawdict.
        first = prefix_chars[0]
        origin = first.get("origin") or (rect.x0, rect.y1 - max(0.5, font_size * 0.18))
        origin_x, origin_y = float(origin[0]), float(origin[1])

        out.append(Overlay(
            rect=rect,
            text=word[:plen],
            fsize=font_size,
            color=color,
            font_hint=font_name,
            origin_x=origin_x,
            origin_y=origin_y,
            is_ocr=is_ocr,
        ))


def _pick_bold_font(fontname: str) -> str:
    n = (fontname or "").lower()
    if any(t in n for t in ("times", "serif", "roman", "garamond", "georgia", "caslon", "minion")):
        return "tibo"  # Times-Bold
    if any(t in n for t in ("mono", "courier", "consolas", "menlo", "andale")):
        return "cobo"  # Courier-Bold
    return "hebo"  # Helvetica-Bold
