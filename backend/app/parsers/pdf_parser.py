"""PDF parser using PyMuPDF.

We extract paragraphs in reading order and try to detect headings by font size.
"""
from __future__ import annotations

import io

import fitz  # PyMuPDF

from ..models import Block


def parse(data: bytes) -> tuple[list[Block], list[str]]:
    warnings: list[str] = []
    blocks: list[Block] = []
    try:
        doc = fitz.open(stream=io.BytesIO(data), filetype="pdf")
    except Exception as exc:
        warnings.append(f"Failed to open PDF: {exc}")
        return blocks, warnings

    sizes: list[float] = []
    for page in doc:
        page_dict = page.get_text("dict")
        for blk in page_dict.get("blocks", []):
            for line in blk.get("lines", []):
                for span in line.get("spans", []):
                    sizes.append(span.get("size", 0.0))

    body_size = _median(sizes) if sizes else 11.0

    for page_index, page in enumerate(doc):
        page_dict = page.get_text("dict")
        for blk in page_dict.get("blocks", []):
            if blk.get("type") != 0:
                continue
            paragraph_text_parts: list[str] = []
            paragraph_max_size = 0.0
            for line in blk.get("lines", []):
                line_text_parts: list[str] = []
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    if not span_text:
                        continue
                    line_text_parts.append(span_text)
                    paragraph_max_size = max(paragraph_max_size, span.get("size", 0.0))
                if line_text_parts:
                    paragraph_text_parts.append("".join(line_text_parts))
            paragraph = " ".join(p.strip() for p in paragraph_text_parts).strip()
            if not paragraph:
                continue

            if paragraph_max_size > body_size * 1.25 and len(paragraph) < 200:
                level = 1 if paragraph_max_size > body_size * 1.6 else 2
                blocks.append(Block(type="heading", text=paragraph, level=level))
            else:
                blocks.append(Block(type="paragraph", text=paragraph))
        blocks.append(Block(type="spacer"))
        if page_index >= 1000:
            warnings.append("Truncated to first 1000 pages.")
            break

    if not blocks:
        warnings.append("No extractable text — this may be a scanned/image-only PDF.")

    return blocks, warnings


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    mid = len(s) // 2
    if len(s) % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2
