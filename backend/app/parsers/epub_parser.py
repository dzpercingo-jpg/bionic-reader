"""EPUB parser using ebooklib + BeautifulSoup."""
from __future__ import annotations

import io

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from ..models import Block


def parse(data: bytes) -> tuple[list[Block], list[str]]:
    warnings: list[str] = []
    blocks: list[Block] = []
    try:
        book = epub.read_epub(io.BytesIO(data))
    except Exception as exc:
        warnings.append(f"Failed to read EPUB: {exc}")
        return blocks, warnings

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        try:
            soup = BeautifulSoup(item.get_content(), "lxml")
        except Exception:
            continue
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        for el in soup.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre"]
        ):
            text = el.get_text(" ", strip=True)
            if not text:
                continue
            name = el.name
            if name and name.startswith("h"):
                try:
                    level = int(name[1])
                except ValueError:
                    level = 1
                blocks.append(Block(type="heading", text=text, level=level))
            elif name == "li":
                blocks.append(Block(type="list_item", text=text, ordered=False))
            elif name == "blockquote":
                blocks.append(Block(type="blockquote", text=text))
            elif name == "pre":
                blocks.append(Block(type="code", text=text))
            else:
                blocks.append(Block(type="paragraph", text=text))
        blocks.append(Block(type="spacer"))
    return blocks, warnings
