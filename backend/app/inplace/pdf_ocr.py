"""OCR pre-processing for scanned/image-only PDFs.

When a PDF has no extractable text (or extremely sparse text), the bionic
transformation has nothing to style. Rather than failing silently, this
module rasterizes every text-less page, runs OCR, and adds an invisible
text layer so the bionic pass can find words to style and the user can
select / copy / search the recognized text.

Engine selection (decided in `RESEARCH_OCR.md`):

1. **Primary — OCRmyPDF**: industry-standard PDF OCR pipeline that wraps
   Tesseract with deskew, denoise, oversample, page-orientation detection
   and emits a clean, line-coherent invisible text layer. We use its
   Python API in-process (no subprocess). Quality on real scans is
   substantially higher than rolling our own Tesseract loop because of
   the preprocessing steps and because ocrmypdf writes per-line text
   spans (not per-word), which keeps lines intact when the downstream
   bionic pass redacts the prefix of each word.

2. **Fallback — manual Tesseract pipeline**: kept for environments where
   ocrmypdf or its system deps (Ghostscript, unpaper, pngquant) are not
   installed. It is honest about its limitation — each word is inserted
   individually, so post-bionic text extraction can look fragmented.

If both fail, the caller catches the exception and falls back to the
non-OCR path so the user still gets a valid PDF (just without bionic
styling on the scanned pages).

The OCR layer is added in-place — images and vector content of every
page are untouched. The user's original file on disk is never modified.
"""
from __future__ import annotations

import io
import logging

import fitz  # PyMuPDF

log = logging.getLogger(__name__)

# Pages with fewer than this many text characters are considered "scanned"
# and eligible for OCR. Set conservatively low because in-place text PDFs
# usually have hundreds of characters per page.
_TEXT_THRESHOLD = 20

# Higher DPI → better OCR accuracy but slower. 300 is the standard
# "OCR-quality" raster setting; below 200 accuracy drops sharply on small
# fonts. Used only by the manual fallback pipeline; ocrmypdf manages its
# own DPI via --image-dpi/--oversample.
_RASTER_DPI = 300


def page_needs_ocr(page: fitz.Page) -> bool:
    """True if the page has effectively no text layer."""
    txt = page.get_text("text").strip()
    return len(txt) < _TEXT_THRESHOLD


def ocr_pdf(data: bytes, lang: str = "eng+fra") -> bytes:
    """Return new PDF bytes with an invisible OCR text layer on every scanned page.

    Pages that already have text are left untouched. Tries OCRmyPDF first; falls
    back to a manual Tesseract pipeline if ocrmypdf or its system dependencies
    are missing.
    """
    # Cheap detection — skip OCR entirely if every page already has text.
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        has_scanned = any(page_needs_ocr(p) for p in doc)
    finally:
        doc.close()
    if not has_scanned:
        return data

    # Try the ocrmypdf pipeline first.
    try:
        return _ocr_with_ocrmypdf(data, lang)
    except _OcrmypdfUnavailable as exc:
        log.info("ocrmypdf unavailable (%s) — falling back to manual Tesseract", exc)
    except Exception as exc:  # noqa: BLE001 — log and try the fallback
        log.warning("ocrmypdf raised (%s) — falling back to manual Tesseract", exc)

    return _ocr_with_tesseract(data, lang)


class _OcrmypdfUnavailable(Exception):
    """Raised when ocrmypdf or one of its system deps is not installed."""


def _ocr_with_ocrmypdf(data: bytes, lang: str) -> bytes:
    """Primary OCR path: OCRmyPDF in-process.

    Quality features enabled:
    - `deskew`: rotate page so text baselines are horizontal (improves OCR)
    - `clean_final`: remove speckle noise (improves OCR but kept off by
      default because it requires `unpaper`; we let ocrmypdf detect)
    - `force_ocr=False`: skip pages that already have text
    - `skip_text=True`: never re-OCR pages that already have a text layer
    - `optimize=0`: don't re-encode images — preserves visual fidelity
    """
    try:
        import ocrmypdf  # type: ignore[import-not-found]
    except ImportError as exc:
        raise _OcrmypdfUnavailable("ocrmypdf not installed") from exc

    # ocrmypdf takes ISO 639-2 codes like "eng+fra" — same convention as
    # Tesseract — so we pass our `lang` straight through.
    src = io.BytesIO(data)
    out = io.BytesIO()
    try:
        ocrmypdf.ocr(
            src,
            out,
            language=lang,
            deskew=True,
            skip_text=True,  # don't re-OCR pages that already have text
            progress_bar=False,
            output_type="pdf",  # keep as plain PDF; no PDF/A re-encoding
            optimize=0,  # no JPEG re-compression of embedded images
            quiet=True,
        )
    except ocrmypdf.MissingDependencyError as exc:
        raise _OcrmypdfUnavailable(f"missing system dep: {exc}") from exc
    except ocrmypdf.PriorOcrFoundError:
        # Should not happen with skip_text=True, but be defensive.
        return data
    except ocrmypdf.BadArgsError as exc:
        raise _OcrmypdfUnavailable(f"bad args: {exc}") from exc

    return out.getvalue()


def _ocr_with_tesseract(data: bytes, lang: str) -> bytes:
    """Fallback OCR path: rasterize each scanned page and call pytesseract directly.

    Documented limitation: each word is inserted as a separate text-show
    operation, so post-bionic text extraction may look fragmented because
    PyMuPDF groups characters by Y-bucket. Use ocrmypdf when possible.
    """
    import pytesseract  # local import — heavy optional dep
    from PIL import Image

    doc = fitz.open(stream=data, filetype="pdf")
    try:
        any_modified = False

        for page in doc:
            if not page_needs_ocr(page):
                continue

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

                x = data_dict["left"][i] / zoom
                y = data_dict["top"][i] / zoom
                h = data_dict["height"][i] / zoom

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
                    continue

        out = io.BytesIO()
        if any_modified:
            doc.save(out, garbage=3, deflate=True)
        else:
            doc.save(out)
        return out.getvalue()
    finally:
        doc.close()


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
