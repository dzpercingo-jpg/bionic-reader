"""Plain text parser with charset detection."""
from __future__ import annotations

import chardet

from ..models import Block


def parse(data: bytes) -> tuple[list[Block], list[str]]:
    warnings: list[str] = []
    detection = chardet.detect(data) if data else {"encoding": "utf-8", "confidence": 1.0}
    encoding = detection.get("encoding") or "utf-8"
    confidence = detection.get("confidence") or 0.0
    if confidence < 0.5:
        warnings.append(f"Low charset detection confidence ({confidence:.2f}); used {encoding}.")
    try:
        text = data.decode(encoding, errors="replace")
    except (LookupError, UnicodeDecodeError):
        text = data.decode("utf-8", errors="replace")
        warnings.append("Failed to decode with detected charset; used UTF-8 as fallback.")

    blocks: list[Block] = []
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip("\r\n")
        if not paragraph:
            blocks.append(Block(type="spacer"))
            continue
        blocks.append(Block(type="paragraph", text=paragraph.strip()))
    return blocks, warnings
