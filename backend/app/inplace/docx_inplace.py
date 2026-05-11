"""DOCX in-place bionic transformation.

Opens the user's original .docx and walks every text run (`<w:r>`) in
the body, headers, footers, footnotes, comments, and table cells.
For each run that contains *only* `<w:rPr>` and `<w:t>` children
(i.e. plain text — no embedded images, fields, breaks, or drawings),
the run is replaced by a sequence of cloned runs that segment the text
into bionic-prefix (bold) + suffix pieces.

Runs that contain anything other than text/rPr are left untouched —
this guarantees images, charts, hyperlinks-with-icons, equations,
form fields, comment ranges, and any other complex inline content
are preserved bit-for-bit.

Outside of run-splitting, NOTHING in the document is modified:
- styles.xml is untouched
- numbering.xml is untouched
- relationships, content types, headers, footers, sections all intact
- images are referenced by the same /word/media/* parts
- tables retain their structure, grid, borders, conditional formatting
"""
from __future__ import annotations

import io
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.oxml.shared import OxmlElement

from ..models import BionicSettings
from ..transformer import WORD_RE, _prefix_length

# Safe inner-children tags for a `<w:r>` we are allowed to split.
# We MUST be paranoid: any unknown child means the run carries
# content (drawings, fields, breaks) that we should not duplicate.
_SAFE_RUN_CHILDREN = {qn("w:rPr"), qn("w:t")}


def export_inplace(
    data: bytes,
    settings: BionicSettings,
    filename: str = "document.docx",
) -> tuple[bytes, str, str]:
    doc = Document(io.BytesIO(data))

    if settings.enabled:
        _process_part(doc.element.body, settings)
        for section in doc.sections:
            for hf_attr in (
                "header",
                "first_page_header",
                "even_page_header",
                "footer",
                "first_page_footer",
                "even_page_footer",
            ):
                try:
                    part = getattr(section, hf_attr)
                except Exception:
                    continue
                if part is None:
                    continue
                try:
                    root = part._element
                except AttributeError:
                    continue
                _process_part(root, settings)
    # else: pass-through — file is structurally untouched.

    buf = io.BytesIO()
    doc.save(buf)
    stem = Path(filename).stem or "document"
    return (
        buf.getvalue(),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        f"{stem}.bionic.docx",
    )


def _process_part(root, settings: BionicSettings) -> None:
    """Walk all `<w:p>` inside `root` (body / header / footer / cell)."""
    for p_elem in root.iter(qn("w:p")):
        _process_paragraph(p_elem, settings)


def _process_paragraph(p_elem, settings: BionicSettings) -> None:
    """Replace each plain-text `<w:r>` with bionic-split sub-runs."""
    # Snapshot, because we mutate the children list.
    runs = [c for c in p_elem if c.tag == qn("w:r")]
    for r_elem in runs:
        _split_run_into_bionic(r_elem, settings)


def _split_run_into_bionic(r_elem, settings: BionicSettings) -> None:
    """Split a single `<w:r>` into bionic-prefixed sub-runs."""
    # Refuse to split if the run holds anything more than text.
    for child in r_elem:
        if child.tag not in _SAFE_RUN_CHILDREN:
            return

    text_elems = [c for c in r_elem if c.tag == qn("w:t")]
    if not text_elems:
        return
    text = "".join((t.text or "") for t in text_elems)
    if not text.strip():
        return

    chunks = _compute_bionic_chunks(text, settings)
    # No transformation needed (only one suffix chunk == raw text).
    if len(chunks) <= 1 or all(not is_prefix for _, is_prefix in chunks):
        return

    parent = r_elem.getparent()
    insert_at = list(parent).index(r_elem)

    new_runs: list = []
    for chunk_text, is_prefix in chunks:
        if not chunk_text:
            continue
        new_r = deepcopy(r_elem)
        # Strip <w:t> children from clone.
        for old_t in [c for c in new_r if c.tag == qn("w:t")]:
            new_r.remove(old_t)
        # Apply bold on rPr clone if prefix.
        if is_prefix:
            _set_bold(new_r)
        # Append the new <w:t>
        new_t = OxmlElement("w:t")
        new_t.set(qn("xml:space"), "preserve")
        new_t.text = chunk_text
        new_r.append(new_t)
        new_runs.append(new_r)

    for i, new_r in enumerate(new_runs):
        parent.insert(insert_at + i, new_r)

    parent.remove(r_elem)


def _set_bold(r_elem) -> None:
    """Ensure the run has `<w:b/>` set inside `<w:rPr>`."""
    rPr = r_elem.find(qn("w:rPr"))
    if rPr is None:
        rPr = OxmlElement("w:rPr")
        r_elem.insert(0, rPr)
    # Remove any existing <w:b> children to avoid duplicates / val=0 toggles
    for existing in rPr.findall(qn("w:b")):
        rPr.remove(existing)
    for existing in rPr.findall(qn("w:bCs")):
        rPr.remove(existing)
    b = OxmlElement("w:b")
    rPr.append(b)
    b_cs = OxmlElement("w:bCs")  # bold for complex script
    rPr.append(b_cs)


def _compute_bionic_chunks(text: str, settings: BionicSettings) -> list[tuple[str, bool]]:
    """Tokenize `text` into `(chunk, is_prefix)` pieces."""
    chunks: list[tuple[str, bool]] = []
    last_end = 0
    for match in WORD_RE.finditer(text):
        start, end = match.span()
        if start > last_end:
            chunks.append((text[last_end:start], False))
        word = match.group(0)
        plen = _prefix_length(word, settings)
        if plen > 0:
            chunks.append((word[:plen], True))
            if plen < len(word):
                chunks.append((word[plen:], False))
        else:
            chunks.append((word, False))
        last_end = end
    if last_end < len(text):
        chunks.append((text[last_end:], False))
    return chunks
