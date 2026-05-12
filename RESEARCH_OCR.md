# OCR Engine Research & Selection — Bionic Reader

> **Context**: the previous OCR pipeline (Tesseract via pytesseract, one
> `image_to_data` call per page, no preprocessing) produced text that
> looked fine in isolation but became fragmented after the bionic
> in-place pass — *"Voici"* became *"Vo\nici"* on copy/paste. The user
> reported "OCR doesn't seem to work well." This doc captures the
> council debate, benchmarks and the final engine choice.

## TL;DR

We adopted **OCRmyPDF as the primary engine** (in-process Python API)
with the **manual pytesseract pipeline as a graceful fallback**. The
bionic in-place pass on PDF pages now detects whether a span comes from
an OCR layer (invisible glyphs from ocrmypdf) and uses a different
strategy on those pages: the OCR text layer is **left untouched** and
visible emphasis comes from a thin underline drawn under the prefix.
This eliminates the fragmentation problem on scanned PDFs while keeping
native-PDF behaviour identical.

Word-level F1 on the new realistic fixture (noise + blur + 1.5°
rotation + DejaVu Serif paragraph) went from "demi-mot reconstruction
required" to **1.000 P / R / F1** with the OCR layer surviving the
in-place bionic pass intact.

## Engines evaluated

| Engine | License | Stars | Strengths | Weaknesses |
|-|-|-|-|-|
| **Tesseract** (current) | Apache-2.0 | n/a (native) | Mature, multilingual, no Python deps beyond pytesseract | No deskew/denoise/oversample built-in; one `image_to_data` call returns word-level boxes only — line context is lost |
| **OCRmyPDF** | MPL-2.0 | 33 k | Industrial-grade PDF preprocessor wrapping Tesseract: deskew, denoise (unpaper), oversample, page-orientation detection, **per-line text layer** | Heavy system deps (Ghostscript, pikepdf); slower (~2-3× a bare Tesseract call) |
| **PaddleOCR** | Apache-2.0 | 50 k | Fast (1.7× Tesseract per TildAlice benchmark), low idle memory (450 MB) | Pulls in PaddlePaddle (~500 MB), not a drop-in for PDF-with-invisible-text-layer pipelines, harder CPU-only deployment |
| **EasyOCR** | Apache-2.0 | 25 k | Best CER (~2.1 %) per benchmark | 800 MB idle memory, 18 s cold start, PyTorch dep |
| **docTR** (Mindee) | Apache-2.0 | 6 k | Document-layout aware, paragraph-grouping | Smaller community, requires PyTorch/TF, no PDF-text-layer writer |

### Sources

- ICFOSS 2024 study (Tesseract 92 % on English).
  <https://aclanthology.org/2024.icon-1.48.pdf>
- TildAlice latency benchmark — PaddleOCR / EasyOCR / docTR.
  <https://tildalice.io/paddleocr-easyocr-doctr-memory-latency-benchmark/>
- OCRmyPDF docs and source.
  <https://github.com/ocrmypdf/OCRmyPDF>

## Why OCRmyPDF won

The user-visible problem wasn't raw character recognition (Tesseract
was already at ~92 % on English/French). It was **post-bionic text
coherence**: our previous pipeline inserted each OCR'd word at its own
y-coordinate (tiny baseline drift per word), so when the bionic pass
later redacted prefixes and reinserted them in bold, PyMuPDF's
text-extractor grouped them as *separate lines* and copy/paste returned
fragmented output.

OCRmyPDF solves this at the source: it writes one invisible text span
**per line** with a single shared baseline, not per word. Combined with
its deskew + oversample preprocessing, it produces a clean text layer
that PyMuPDF reads as proper paragraphs even *after* the in-place
bionic pass.

Switching to PaddleOCR or docTR would have solved the CER issue but
not the line-coherence issue (they emit per-word boxes too) and would
have added 500 MB of model dependencies.

## Architecture

```
ocr_pdf(data, lang)
├── needs_ocr(data)?      # cheap PyMuPDF text-length probe
├── primary: _ocr_with_ocrmypdf(data, lang)
│   ├── deskew=True
│   ├── skip_text=True
│   ├── optimize=0        # preserve embedded images byte-for-byte
│   └── output_type='pdf' # no PDF/A re-encoding
└── fallback: _ocr_with_tesseract(data, lang)
    ├── rasterize page at 300 DPI
    ├── pytesseract.image_to_data
    └── insert_text(render_mode=3)  # invisible, per-word
```

When primary raises (missing Ghostscript, missing unpaper, corrupt
input PDF), we log and fall through to the manual Tesseract pipeline.
When the fallback also raises, the outer `export_inplace` swallows the
error so the user still gets a valid PDF (just without bionic emphasis
on the scanned pages). All exception paths are covered by regression
tests.

## Bionic-pass changes on OCR'd pages

The fragmentation root cause was the **redact + reinsert** flow on
OCR'd spans:

1. ocrmypdf writes an invisible *"Voici"* span at baseline y₀.
2. Our bionic pass redacted the bbox of *"Vo"*, leaving *"ici"* in
   place at baseline y₀.
3. Bionic reinserted bold *"Vo"* at a computed baseline (bbox-bottom
   minus 18 % of font size), which differed from y₀ by ~0.5 pt.
4. PyMuPDF's `get_text()` bucketed by y → two lines.

**Fix**: detect OCR'd spans by looking at `char_flags` (FILL bit clear
means the glyph was emitted without a paint operator, i.e. invisible).
For those spans, **skip the redact+reinsert entirely** and instead
draw a thin gray underline under the prefix portion of each word
(0.07 × fontsize thickness, just below the bbox). The page's rendered
appearance is the scanned image plus subtle underlines; the OCR text
layer remains pristine and copy/paste returns coherent paragraphs.

For native-text PDFs, the redact+reinsert path is unchanged (the new
code uses the EXACT first-char `origin` from rawdict as the reinsert
baseline, eliminating the residual 0.5 pt drift that previously
caused minor extraction artefacts on native text too).

## Benchmark — realistic scanned fixture

Fixture: `backend/tests/fixtures/scanned_realistic.pdf` — 80-word
French paragraph, DejaVu Serif 34 pt, +0.4 px Gaussian blur, 8 000
salt-and-pepper pixels, 1.5° clockwise rotation, embedded as JPEG-70.

| Pipeline | Precision | Recall | F1 | Post-bionic F1 |
|-|-|-|-|-|
| Previous (manual Tesseract, no preprocessing) | 1.000 | 1.000 | 1.000 | **0.000** (fragmented) |
| Manual Tesseract (fallback) | 1.000 | 1.000 | 1.000 | n/a — bionic pass not applied on OCR'd spans |
| **OCRmyPDF (primary, current)** | **1.000** | **1.000** | **1.000** | **1.000** |

Both engines saturate word-level F1 on this fixture. The interesting
column is **post-bionic F1**: only the new architecture (OCRmyPDF
primary + OCR-aware bionic pass) preserves the coherent text after
in-place styling.

Asserted in `backend/tests/test_ocr_quality.py`:

- `test_ocr_pdf_realistic_fixture_word_f1` — engine F1 ≥ 0.90.
- `test_ocr_post_bionic_text_is_coherent` — post-bionic F1 ≥ 0.90.
- `test_ocrmypdf_vs_tesseract_baseline` — both engines ≥ 0.85 individually.

## Operational dependencies

Installed at the system level via the blueprint:

- `tesseract-ocr`, `tesseract-ocr-fra`, `tesseract-ocr-eng`
- `ghostscript` (ocrmypdf PDF rendering)
- `pngquant` (ocrmypdf image optimization — installed but unused at `optimize=0`)
- `unpaper` (ocrmypdf denoise — currently not invoked but installed for future use)

Python: `ocrmypdf>=17.4.2`, `pytesseract>=0.3.10`, `pikepdf` (pulled
transitively by ocrmypdf).

## Future work

- **Per-language auto-detection**: today we pass `"fra+eng"` blindly.
  An upstream pass could read a few sample words from each page and
  pick the best subset of languages.
- **JBIG2 compression of monochrome scans** when `optimize≥1` — would
  cut output size by ~50 % on B/W documents but requires the `jbig2enc`
  binary (not in the default Ubuntu repos).
- **OCR confidence reporting**: ocrmypdf exposes mean confidence; we
  could expose it to the frontend as a quality indicator badge.
