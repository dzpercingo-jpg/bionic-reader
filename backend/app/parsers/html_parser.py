"""HTML parser using BeautifulSoup."""
from __future__ import annotations

from bs4 import BeautifulSoup

from ..models import Block


def parse(data: bytes) -> tuple[list[Block], list[str]]:
    warnings: list[str] = []
    text = data.decode("utf-8", errors="replace")
    soup = BeautifulSoup(text, "lxml")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside"]):
        tag.decompose()

    blocks: list[Block] = []
    body = soup.body or soup
    _walk(body, blocks)
    if not blocks:
        body_text = soup.get_text("\n", strip=True)
        if body_text:
            for paragraph in body_text.split("\n"):
                paragraph = paragraph.strip()
                if paragraph:
                    blocks.append(Block(type="paragraph", text=paragraph))
    return blocks, warnings


def _walk(node, blocks: list[Block]) -> None:
    for el in node.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre"]):
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
