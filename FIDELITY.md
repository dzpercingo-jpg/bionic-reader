# Format fidelity — what survives the bionic transformation

The original "rebuild from parsed text" exporters (in `backend/app/exporters/`)
re-create the file from a flat block model; they lose images, tables, embedded
objects, and most non-text formatting. Those still exist as a fallback, but
the **primary path** is now `backend/app/inplace/*` which performs **run-level
edits on the user's original file**.

The user's source file is never modified — both paths read the bytes,
process them in memory, and stream out a new `.bionic.<ext>` file.

## What is preserved by the in-place exporters

### DOCX (`app/inplace/docx_inplace.py`)
| Element | Status |
|---|---|
| Embedded images (`word/media/*.png|jpg|...`) | **Byte-identical** |
| Tables (grid, borders, conditional formatting) | Preserved |
| Headers / footers (per section) | Preserved (and bionic-styled) |
| Paragraph styles (Heading 1, Quote, custom) | Preserved |
| Run properties (font, size, color, italic, underline, strikethrough) | **Cloned onto every split sub-run** |
| Hyperlinks, footnotes, comments | Preserved (untouched) |
| Inline drawings, charts, OLE objects | Preserved (runs containing them are *not* split) |
| Page setup, sections, margins | Preserved |

How: for every `<w:r>` (run) that contains only `<w:rPr>` + `<w:t>` (i.e. plain
text), we replace it with N cloned runs splitting the text into bionic
prefix + suffix and adding `<w:b/>` to the prefix's `<w:rPr>`. Any run with a
drawing, break, field, or unknown child is skipped untouched.

### PDF (`app/inplace/pdf_inplace.py`)
| Element | Status |
|---|---|
| Embedded images (raster + vector) | **Byte-identical** |
| Page count and dimensions | Identical |
| Metadata (title, author, creation date) | Preserved |
| Signatures, annotations | Preserved |
| Vector drawings (tables, shapes, signatures) | Preserved |
| Text content | Preserved (prefix letters are redacted and re-rendered in Helv-Bold / Times-Bold / Courier-Bold per font heuristic) |
| Fonts (custom embedded) | Re-rendered with closest Base-14 bold equivalent |

How: for every character in every text span, compute its OVP-based prefix
bbox. Redact the prefix bbox using `apply_redactions(images=PDF_REDACT_IMAGE_NONE)`
so vector drawings + images are **never** touched, then re-insert the prefix
text at the same position using a Base-14 bold font.

Known limitations:
- Custom embedded fonts cannot be replicated exactly. The fallback Helvetica /
  Times / Courier bold may look slightly different from the original.
- Right-to-left scripts (Arabic, Hebrew) are not supported.
- Scanned PDFs (image-only) need a separate OCR pass before this exporter
  can find any text to style.

### PPTX (`app/inplace/pptx_inplace.py`)
| Element | Status |
|---|---|
| Slide layouts, masters, themes | Preserved (untouched) |
| Shapes (text boxes, images, smart-art, charts) | Preserved |
| Animations, transitions | Preserved |
| Tables and their cell formatting | Preserved |
| Notes slides | Preserved (and bionic-styled) |
| Run properties (`<a:rPr>`) on every text run | Cloned to every split sub-run |

How: same run-splitting approach as DOCX, but on `<a:r>` (drawingML namespace).

### XLSX (`app/inplace/xlsx_inplace.py`)
| Element | Status |
|---|---|
| Formulas (any cell starting with `=`) | **Never touched** |
| Numeric, date, boolean cells | Never touched |
| Embedded images, charts | **Byte-identical** |
| Sheet order, hidden rows/columns, freeze panes | Preserved |
| Cell borders, fill, alignment | Preserved |
| Cell font (name, size, color) | Cloned to every text chunk |
| Plain string cells longer than 3 chars | Replaced with `CellRichText` of bionic chunks |

How: walk every cell of every worksheet; for `isinstance(val, str)` and
`not val.startswith("=")`, build a `CellRichText` made of `TextBlock(InlineFont(b=True), prefix)`
+ `TextBlock(InlineFont(b=False), suffix)` for each word, cloning the
existing font onto each chunk.

## Verification

Run `pytest backend/tests/test_inplace.py backend/tests/test_api_inplace.py -v`.
The suite verifies, for every format:

- The source file on disk is byte-unchanged before/after export (SHA-256 invariant)
- Embedded images in the output are byte-identical to the source's images
- Tables, formulas, and structural metadata survive
- The output can be re-opened by the format's native library without error
- Bionic styling actually got applied (count of `<w:b/>` / `b="1"` / `CellRichText` instances > 0)

## When the in-place path is NOT used

The flat-rebuild exporters (`html`, `docx`-rebuild, `txt`) remain available
because they are useful when:

- The user wants to *change* the format (DOCX → HTML, PDF → TXT, etc.)
- The user prefers a clean, opinionated layout over the original (e.g.
  for printing)
- The file is in an unsupported source format (`.epub`, `.rtf`, `.md`,
  `.html`) and there is no in-place strategy for it.
