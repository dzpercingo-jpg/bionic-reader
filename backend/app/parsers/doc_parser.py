"""Legacy `.doc` (Word 97–2003 binary) parser.

`python-docx` only handles modern Open XML `.docx`. To read a legacy binary
`.doc` file we convert it to `.docx` first using LibreOffice in headless mode
(`soffice --convert-to docx`) and then delegate to the existing DOCX parser.
The conversion happens entirely in memory + a per-call tempdir; the user's
file on disk is never modified.

If `libreoffice`/`soffice` is missing from PATH, the parser returns no blocks
and a clear warning instead of crashing, so the API can still respond 200 and
the UI can render an explanatory message.
"""
from __future__ import annotations

from ..inplace.doc_inplace import convert_doc_to_docx
from ..models import Block
from .docx_parser import parse as parse_docx


def parse(data: bytes) -> tuple[list[Block], list[str]]:
    warnings: list[str] = []
    try:
        docx_bytes = convert_doc_to_docx(data)
    except RuntimeError as exc:
        warnings.append(str(exc))
        return [], warnings
    except Exception as exc:  # pragma: no cover — defensive
        warnings.append(f"Failed to convert legacy .doc to .docx: {exc}")
        return [], warnings
    blocks, more_warnings = parse_docx(docx_bytes)
    warnings.extend(more_warnings)
    return blocks, warnings
