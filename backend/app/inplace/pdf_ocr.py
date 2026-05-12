"""OCR pre-processing for scanned/image-only PDFs.

When a PDF has no extractable text (or extremely sparse text), the bionic
transformation has nothing to style. Rather than failing silently, this
module rasterizes every text-less page, runs Tesseract OCR, and adds the
recognized words as an *invisible text layer* (`render_mode=3` in PDF
parlance) anchored to the recognized bounding boxes.

After this pre-processing pass:
- The PDF still looks identical to a human (the OCR text is invisible
  rendering — only used for selection / accessibility / `get_text` extraction).
- `pdf_inplace.export_inplace` can now find words to style bold.
- Copy/paste in any PDF reader pulls the OCR'd text.

Tesseract must be installed on the host (`apt install tesseract-ocr`). If
absent, `pytesseract.image_to_data` raises and the caller falls back to the
non-OCR path with a warning.

The OCR layer is added in-place — images and vector content of every page
are untouched. The user's original file on disk is never modified.
"""
from __future__ import annotations

import io

import fitz  # PyMuPDF

# Pages with fewer than this many text characters are considered "scanned"
# and eligible for OCR. Set conservatively low because in-place text PDFs
# usually have hundreds of characters per page.
_TEXT_THRESHOLD = 20

# Higher DPI → better OCR accuracy but slower. 300 is the standard "OCR-quality"
# raster setting; below 200 accuracy drops sharply on small fonts.
_RASTER_DPI = 300


def page_needs_ocr(page: fitz.Page) -> bool:
    """True if the page has effectively no text layer."""
    txt = page.get_text("text").strip()
    return len(txt) < _TEXT_THRESHOLD


def ocr_pdf(data: bytes, lang: str = "eng+fra") -> bytes:
    """Return new PDF bytes with an invisible OCR text layer on every scanned page.

    Pages that already have text are left untouched. Raises if Tesseract isn't
    available or the PDF can't be opened.
    """
    import pytesseract  # local import — heavy optional dep
    from PIL import Image

    doc = fitz.open(stream=data, filetype="pdf")
    any_modified = False

    for page in doc:
        if not page_needs_ocr(page):
            continue

        # Render the page to a high-DPI PNG that Tesseract can process.
        zoom = _RASTER_DPI / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        try:
            data_dict = pytesseract.image_to_data(
                img,
                lang=lang,
                output_type=pytesseract.Output.DICT,
            )
        except pytesseract.TesseractNotFoundError as exc:
            raise RuntimeError(
                "Tesseract OCR is required for scanned PDFs but is not installed. "
                "Install via `apt install tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng`."
            ) from exc

        n_words = len(data_dict.get("text", []))
        for i in range(n_words):
            word = (data_dict["text"][i] or "").strip()
            conf_str = str(data_dict.get("conf", [-1])[i])
            try:
                conf = float(conf_str)
            except ValueError:
                conf = -1.0
            if not word or conf < 0:
                continue

            # Map pixel coordinates back to PDF points (1pt == 1/72 inch).
            x = data_dict["left"][i] / zoom
            y = data_dict["top"][i] / zoom
            h = data_dict["height"][i] / zoom

            # render_mode=3 ⇒ "invisible text". Word is selectable but does
            # not appear visually. Anchor at the baseline (bottom-left).
            try:
                page.insert_text(
                    (x, y + h * 0.85),
                    word,
                    fontsize=max(4.0, h * 0.9),
                    fontname="helv",
                    color=(0, 0, 0),
                    render_mode=3,
                    overlay=True,
                )
                any_modified = True
            except Exception:
                # Skip a word that PyMuPDF can't render (unicode oddities, etc).
                continue

    if not any_modified:
        # Even though we didn't touch any page, return a clean re-save so
        # callers get a consistent bytestream.
        out = io.BytesIO()
        doc.save(out)
        doc.close()
        return out.getvalue()

    out = io.BytesIO()
    doc.save(out, garbage=3, deflate=True)
    doc.close()
    return out.getvalue()


def needs_ocr(data: bytes) -> bool:
    """Cheap up-front check: does ANY page in the PDF lack a usable text layer?"""
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        for page in doc:
            if page_needs_ocr(page):
                return True
        return False
    finally:
        doc.close()
