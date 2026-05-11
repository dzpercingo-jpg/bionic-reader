# Test fixtures

Fidelity fixtures used by `tests/test_inplace.py` and `tests/test_api_inplace.py`.

Each file contains a *mix of content types* (text, embedded image, table or
formula) so the in-place exporters can be verified to preserve non-text
elements byte-for-byte.

| File | Format | Contents |
|------|--------|----------|
| `red.png` | PNG | 1x1 red pixel — reused as the embedded image in every fixture |
| `with_image_and_table.docx` | DOCX | Heading + paragraph (mixed bold/italic/red) + embedded image + 3x3 table |
| `with_image_and_table.pptx` | PPTX | Title + body + image + 3x3 table |
| `with_formula_and_image.xlsx` | XLSX | 3 columns × 3 rows + `=SUM(B2:B3)` formula + embedded image |
| `with_image_and_table.pdf` | PDF | Heading + paragraph + embedded image + table-shaped vector drawing |

The fixtures are committed as binary so the tests are hermetic. To regenerate
them, run `python tests/fixtures/generate.py` (see that script).
