"""Markdown parser using markdown-it-py."""
from __future__ import annotations

from markdown_it import MarkdownIt

from ..models import Block


def parse(data: bytes) -> tuple[list[Block], list[str]]:
    warnings: list[str] = []
    text = data.decode("utf-8", errors="replace")
    md = MarkdownIt("commonmark", {"html": False})
    tokens = md.parse(text)
    blocks: list[Block] = []

    i = 0
    list_stack: list[bool] = []  # ordered or not
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "heading_open":
            level = int(tok.tag.replace("h", ""))
            inline = tokens[i + 1]
            blocks.append(Block(type="heading", text=inline.content.strip(), level=level))
            i += 3
            continue
        if tok.type == "paragraph_open":
            inline = tokens[i + 1]
            txt = inline.content.strip()
            if txt:
                in_list = bool(list_stack)
                if in_list:
                    blocks.append(Block(type="list_item", text=txt, ordered=list_stack[-1]))
                else:
                    blocks.append(Block(type="paragraph", text=txt))
            i += 3
            continue
        if tok.type == "bullet_list_open":
            list_stack.append(False)
        elif tok.type == "ordered_list_open":
            list_stack.append(True)
        elif tok.type in ("bullet_list_close", "ordered_list_close") and list_stack:
            list_stack.pop()
        elif tok.type == "blockquote_open":
            inline_idx = _find_inline(tokens, i)
            if inline_idx is not None:
                blocks.append(Block(type="blockquote", text=tokens[inline_idx].content.strip()))
        elif tok.type == "fence" or tok.type == "code_block":
            blocks.append(Block(type="code", text=tok.content.rstrip("\n"), language=tok.info or None))
        elif tok.type == "hr":
            blocks.append(Block(type="spacer"))
        i += 1

    return blocks, warnings


def _find_inline(tokens, start_idx: int) -> int | None:
    for j in range(start_idx, min(start_idx + 5, len(tokens))):
        if tokens[j].type == "inline":
            return j
    return None
