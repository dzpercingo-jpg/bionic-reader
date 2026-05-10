"""RTF parser using striprtf."""
from __future__ import annotations

from striprtf.striprtf import rtf_to_text

from ..models import Block


def parse(data: bytes) -> tuple[list[Block], list[str]]:
    warnings: list[str] = []
    text = rtf_to_text(data.decode("utf-8", errors="replace"), errors="ignore")
    blocks: list[Block] = []
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip("\r\n").strip()
        if not paragraph:
            blocks.append(Block(type="spacer"))
            continue
        blocks.append(Block(type="paragraph", text=paragraph))
    if not blocks:
        warnings.append("No text extracted from RTF.")
    return blocks, warnings
