"""Pydantic models shared across the API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

BlockType = Literal[
    "heading",
    "paragraph",
    "list_item",
    "blockquote",
    "code",
    "image_caption",
    "table_row",
    "spacer",
]


class Block(BaseModel):
    """A semantic chunk of a document."""

    type: BlockType
    text: str = ""
    level: int | None = Field(default=None, description="Heading level 1..6 or list nesting level.")
    ordered: bool | None = Field(default=None, description="True for ordered list, False for unordered.")
    language: str | None = Field(default=None, description="Programming language for code blocks.")


class DocumentModel(BaseModel):
    """A normalized representation of any uploaded document."""

    id: str
    filename: str
    format: str
    word_count: int
    char_count: int
    blocks: list[Block]
    warnings: list[str] = Field(default_factory=list)


class BionicSettings(BaseModel):
    """All knobs supported by the bionic transformation engine."""

    enabled: bool = True
    fixation_ratio: float = Field(default=0.5, ge=0.2, le=0.8)
    min_word_length: int = Field(default=2, ge=1, le=10)
    skip_short_words: bool = True
    use_color_instead_of_bold: bool = False
    prefix_color: str = "#111111"
    color_vowels: bool = False
    vowel_color: str = "#dc2626"
    saccade_adaptive: bool = True


class ExportRequest(BaseModel):
    """Payload for /api/export."""

    document: DocumentModel
    settings: BionicSettings
    format: Literal["html", "pdf", "docx", "txt"] = "html"
    title: str | None = None
