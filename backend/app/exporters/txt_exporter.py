"""Plain text exporter — losslessly outputs the source text without bionic formatting.

Useful for users who just want a clean copy of the extracted text.
"""
from __future__ import annotations

from ..models import BionicSettings, DocumentModel


def export(doc: DocumentModel, settings: BionicSettings, title: str | None = None) -> tuple[bytes, str, str]:
    lines: list[str] = []
    if title:
        lines.append(title)
        lines.append("=" * min(len(title), 60))
        lines.append("")
    for block in doc.blocks:
        if block.type == "heading":
            lines.append("")
            lines.append(block.text)
            lines.append("-" * min(len(block.text), 60))
        elif block.type == "list_item":
            bullet = "1." if block.ordered else "-"
            lines.append(f"{bullet} {block.text}")
        elif block.type == "blockquote":
            for sub in block.text.split("\n"):
                lines.append(f"> {sub}")
        elif block.type == "code":
            lines.append("```")
            lines.append(block.text)
            lines.append("```")
        elif block.type == "spacer":
            lines.append("")
        else:
            lines.append(block.text)
    body = "\n".join(lines)
    from pathlib import Path

    stem = Path(doc.filename).stem or "document"
    return body.encode("utf-8"), "text/plain", f"{stem}.bionic.txt"
