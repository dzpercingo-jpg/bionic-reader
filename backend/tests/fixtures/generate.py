"""Regenerate the test fixtures used by the in-place exporter test suite.

These fixtures embed a 1x1 red PNG, a 3x3 table, a formula (for XLSX), and
mixed-formatting text in different file formats. Each fixture targets a
real-world scenario:

- DOCX with image, table, and mixed bold/italic/red runs
- PPTX with title, body text, image, and a table
- XLSX with a formula cell, plain text cells, and an embedded image
- PDF with title, paragraph, an image, and a table-shaped vector drawing

Run from `backend/`:

    python tests/fixtures/generate.py
"""
from __future__ import annotations

import base64
from pathlib import Path

HERE = Path(__file__).parent


def write_red_png() -> Path:
    # 1×1 red PNG, generated once and committed.
    path = HERE / "red.png"
    if path.exists():
        return path
    b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNg+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    path.write_bytes(base64.b64decode(b64))
    return path


def write_docx(image_path: Path) -> None:
    from docx import Document
    from docx.shared import Inches, RGBColor

    doc = Document()
    doc.add_heading("Document with images and table", level=1)
    p = doc.add_paragraph("Voici ")
    r = p.add_run("du texte en gras")
    r.bold = True
    p.add_run(" et ")
    r = p.add_run("italique rouge")
    r.italic = True
    r.font.color.rgb = RGBColor(0xC0, 0x10, 0x10)
    p.add_run(" pour tester la préservation.")

    doc.add_picture(str(image_path), width=Inches(1))

    table = doc.add_table(rows=3, cols=3)
    table.style = "Table Grid"
    headers = ["Concept", "Description", "Source"]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for r in cell.paragraphs[0].runs:
            r.bold = True
    table.rows[1].cells[0].text = "Attention"
    table.rows[1].cells[1].text = "Capacité à se concentrer"
    table.rows[1].cells[2].text = "Posner 1980"
    table.rows[2].cells[0].text = "Bionique"
    table.rows[2].cells[1].text = "Préfixes en gras"
    table.rows[2].cells[2].text = "Casutt 2018"

    doc.save(str(HERE / "with_image_and_table.docx"))


def write_pptx(image_path: Path) -> None:
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # title-only
    slide.shapes.title.text = "Présentation avec image et tableau"

    tb = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(5), Inches(1.5))
    tf = tb.text_frame
    tf.text = "Première ligne de texte"
    tf.add_paragraph().text = "Deuxième ligne avec mots plus longs"

    slide.shapes.add_picture(str(image_path), Inches(6), Inches(1.5), Inches(1), Inches(1))

    rows, cols = 3, 3
    table_shape = slide.shapes.add_table(rows, cols, Inches(0.5), Inches(4), Inches(8), Inches(2))
    table = table_shape.table
    headers = ["Concept", "Description", "Source"]
    for i, h in enumerate(headers):
        table.cell(0, i).text = h
    table.cell(1, 0).text = "Attention"
    table.cell(1, 1).text = "Capacité de concentration"
    table.cell(1, 2).text = "Posner 1980"
    table.cell(2, 0).text = "Bionique"
    table.cell(2, 1).text = "Préfixes en gras"
    table.cell(2, 2).text = "Casutt 2018"

    prs.save(str(HERE / "with_image_and_table.pptx"))


def write_xlsx(image_path: Path) -> None:
    from openpyxl import Workbook
    from openpyxl.drawing.image import Image

    wb = Workbook()
    ws = wb.active
    ws.title = "Data"
    ws["A1"] = "Concept"
    ws["B1"] = "Score"
    ws["C1"] = "Description longue à styler en bionique"
    ws["A2"] = "Attention"
    ws["B2"] = 80
    ws["C2"] = "Capacité de concentration soutenue dans le temps"
    ws["A3"] = "Bionique"
    ws["B3"] = 65
    ws["C3"] = "Préfixes en gras pour guider la fixation oculaire"
    ws["A4"] = "Total"
    ws["B4"] = "=SUM(B2:B3)"

    img = Image(str(image_path))
    img.width = 60
    img.height = 60
    ws.add_image(img, "E1")

    wb.save(str(HERE / "with_formula_and_image.xlsx"))


def write_pdf(image_path: Path) -> None:
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 portrait
    page.insert_text((50, 70), "Document PDF avec image et tableau",
                     fontname="hebo", fontsize=20)
    page.insert_text(
        (50, 130),
        "Ceci est un paragraphe contenant suffisamment de mots pour vérifier que la technique\n"
        "bionique fonctionne correctement avec préservation des images et de la structure générale\n"
        "du document PDF original.",
        fontname="helv",
        fontsize=12,
    )
    page.insert_image(fitz.Rect(400, 300, 500, 400), filename=str(image_path))

    # Simple drawn table (vector rectangles).
    y = 500
    for col_x in [50, 200, 350, 500]:
        page.draw_line((col_x, y), (col_x, y + 60), width=0.7)
    for row_y in [y, y + 30, y + 60]:
        page.draw_line((50, row_y), (500, row_y), width=0.7)
    page.insert_text((60, y + 18), "Concept", fontname="hebo", fontsize=11)
    page.insert_text((210, y + 18), "Score", fontname="hebo", fontsize=11)
    page.insert_text((360, y + 18), "Source", fontname="hebo", fontsize=11)
    page.insert_text((60, y + 48), "Attention", fontsize=10)
    page.insert_text((210, y + 48), "80", fontsize=10)
    page.insert_text((360, y + 48), "Posner 1980", fontsize=10)
    # second data row
    page.draw_line((50, y + 90), (500, y + 90), width=0.7)
    for col_x in [50, 200, 350, 500]:
        page.draw_line((col_x, y + 60), (col_x, y + 90), width=0.7)
    page.insert_text((60, y + 78), "Bionique", fontsize=10)
    page.insert_text((210, y + 78), "65", fontsize=10)
    page.insert_text((360, y + 78), "Casutt 2018", fontsize=10)

    doc.save(str(HERE / "with_image_and_table.pdf"))


def write_doc_via_libreoffice() -> None:
    """Convert with_image_and_table.docx -> with_image_and_table.doc via libreoffice.

    Used by the legacy-format in-place exporter tests. Skipped silently if
    LibreOffice is not installed on the host.
    """
    import shutil
    import subprocess
    import tempfile

    soffice = shutil.which("libreoffice") or shutil.which("soffice")
    if not soffice:
        print("LibreOffice not installed — skipping .doc fixture")
        return
    src = HERE / "with_image_and_table.docx"
    with tempfile.TemporaryDirectory() as td:
        out = subprocess.run(
            [
                soffice,
                "--headless",
                f"-env:UserInstallation=file://{td}/profile",
                "--convert-to",
                "doc",
                "--outdir",
                td,
                str(src),
            ],
            capture_output=True,
            timeout=60,
            check=False,
        )
        if out.returncode != 0:
            print("LibreOffice failed:", out.stderr.decode(errors="ignore"))
            return
        produced = Path(td) / "with_image_and_table.doc"
        if produced.exists():
            (HERE / "with_image_and_table.doc").write_bytes(produced.read_bytes())


def write_scanned_pdf() -> None:
    """Render a few sentences as a JPEG and embed in a no-text PDF.

    Used to verify the OCR pre-processing step adds an invisible text layer
    so the in-place exporter can apply bionic styling to scanned PDFs.
    """
    import io as _io

    import fitz
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (1200, 600), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except Exception:
        font = ImageFont.load_default()
    lines = [
        "Voici un texte scanne pour OCR.",
        "Lecture bionique facile a comprendre.",
        "Avec OCR Tesseract integre dans Bionic Reader.",
    ]
    y = 80
    for line in lines:
        draw.text((60, y), line, fill="black", font=font)
        y += 100
    buf = _io.BytesIO()
    img.save(buf, "JPEG", quality=80)
    doc = fitz.open()
    page = doc.new_page(width=595, height=298)
    page.insert_image(page.rect, stream=buf.getvalue())
    doc.save(str(HERE / "scanned_image_only.pdf"), garbage=4, deflate=True)


def main() -> None:
    image = write_red_png()
    write_docx(image)
    write_pptx(image)
    write_xlsx(image)
    write_pdf(image)
    write_doc_via_libreoffice()
    write_scanned_pdf()
    print("All fixtures regenerated under", HERE)


if __name__ == "__main__":
    main()
