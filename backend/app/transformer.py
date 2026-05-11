"""Bionic reading transformation engine.

This module is the single source of truth for the bionic algorithm,
mirrored exactly by the frontend so that interactive previews match
exported files.

v2 extensions (driven by COUNCIL.md):
- Optimal Viewing Position (OVP) eye-anchor dot
- Phrase chunking (thin spacers between word groups)
- POS coloring for logical connectors
"""
from __future__ import annotations

import re

from .models import BionicSettings

WORD_RE = re.compile(r"(\w+)", re.UNICODE)

# French + English logical connectors that, when subtly colored,
# expose the *structure* of the argument at a glance.
CONNECTORS = {
    "mais", "donc", "car", "or", "ni", "puisque", "parce", "pourtant",
    "cependant", "néanmoins", "toutefois", "ainsi", "alors", "ensuite",
    "enfin", "premièrement", "deuxièmement", "finalement", "autrement",
    "sinon", "malgré", "bien", "tandis", "tant", "lorsque", "quand",
    "comme", "si", "puis", "aussi", "effet", "fait", "résumé",
    "conclusion", "exemple", "instance", "because", "however", "therefore",
    "thus", "hence", "moreover", "furthermore", "nevertheless", "although",
    "whereas", "while",
}


def _prefix_length(word: str, settings: BionicSettings) -> int:
    """Return how many leading characters to emphasize for `word`."""
    n = len(word)
    if n < settings.min_word_length:
        return 0
    if n == 1:
        return 0 if settings.skip_short_words else 1

    if settings.saccade_adaptive:
        if n <= 3:
            ratio = 0.5
        elif n <= 5:
            ratio = 0.5
        elif n <= 8:
            ratio = 0.45
        elif n <= 12:
            ratio = 0.4
        else:
            ratio = 0.35
        ratio = (ratio + settings.fixation_ratio) / 2
    else:
        ratio = settings.fixation_ratio

    prefix = max(1, round(n * ratio))
    return min(prefix, n - 1) if n > 1 else prefix


def _ovp_index(n: int) -> int:
    """OVP letter index (0-based) per O'Regan 1987 / Brysbaert 1996."""
    if n <= 2:
        return 0
    if n <= 4:
        return 1
    if n <= 6:
        return 2
    if n <= 9:
        return 3
    return round(n / 3)


def transform_word_html(word: str, settings: BionicSettings) -> str:
    """Wrap `word` with HTML reflecting the active techniques."""
    prefix_len = _prefix_length(word, settings)

    if prefix_len == 0:
        inner = _maybe_color_vowels(word, settings)
    else:
        prefix = word[:prefix_len]
        suffix = word[prefix_len:]
        style_parts: list[str] = []
        if settings.use_color_instead_of_bold:
            style_parts.append(f"color:{settings.prefix_color}")
        style_parts.append("font-weight:700")
        style = ";".join(style_parts)

        prefix_rendered = _maybe_color_vowels(prefix, settings)
        suffix_rendered = _maybe_color_vowels(suffix, settings)
        inner = f'<b class="br-prefix" style="{style}">{prefix_rendered}</b>{suffix_rendered}'

    inner = _maybe_wrap_eye_anchor(inner, word, settings)
    inner = _maybe_color_connector(inner, word, settings)
    return inner


def _maybe_color_vowels(text: str, settings: BionicSettings) -> str:
    if not settings.color_vowels:
        return text
    out: list[str] = []
    for ch in text:
        if ch.lower() in "aeiouyàâäéèêëîïôöùûüÿœæ":
            out.append(f'<span style="color:{settings.vowel_color}">{ch}</span>')
        else:
            out.append(ch)
    return "".join(out)


def _maybe_wrap_eye_anchor(html: str, word: str, settings: BionicSettings) -> str:
    if not settings.eye_anchor or len(word) < 3:
        return html
    ovp = _ovp_index(len(word))
    pct = ((ovp + 0.5) / len(word)) * 100
    style = (
        f"background-image:radial-gradient(circle at {pct:.1f}% 105%, "
        f"{settings.eye_anchor_color} 1px, transparent 2.5px);"
        "background-repeat:no-repeat;background-size:100% 4px;background-position:bottom"
    )
    return f'<span class="br-anchored" style="{style}">{html}</span>'


def _maybe_color_connector(html: str, word: str, settings: BionicSettings) -> str:
    if not settings.pos_coloring:
        return html
    if word.lower() in CONNECTORS:
        return (
            f'<span class="br-connector" '
            f'style="color:{settings.pos_color};font-weight:500">{html}</span>'
        )
    return html


def transform_text_html(text: str, settings: BionicSettings) -> str:
    """Apply bionic transformation to a free-form text string, returning HTML."""
    if not settings.enabled and not settings.eye_anchor and not settings.pos_coloring:
        if settings.phrase_chunking:
            # Pure spacing technique, no bionic — still apply chunks.
            return _chunked_plain(text, settings.phrase_chunk_size)
        return _escape_html(text)

    if settings.phrase_chunking and settings.phrase_chunk_size > 0:
        # Group at the word level BEFORE transforming, to never break HTML nesting.
        chunks: list[list[tuple[str, str]]] = []  # list of [(word_or_sep, kind)]
        current_chunk: list[tuple[str, str]] = []
        words_in_chunk = 0
        last_end = 0
        for match in WORD_RE.finditer(text):
            start, end = match.span()
            if start > last_end:
                current_chunk.append((text[last_end:start], "sep"))
            current_chunk.append((match.group(0), "word"))
            words_in_chunk += 1
            last_end = end
            if words_in_chunk >= settings.phrase_chunk_size:
                chunks.append(current_chunk)
                current_chunk = []
                words_in_chunk = 0
        if last_end < len(text):
            current_chunk.append((text[last_end:], "sep"))
        if current_chunk:
            chunks.append(current_chunk)

        rendered_chunks: list[str] = []
        for chunk in chunks:
            buf: list[str] = []
            for token, kind in chunk:
                if kind == "word":
                    if settings.enabled:
                        buf.append(transform_word_html(token, settings))
                    else:
                        inner = _escape_html(token)
                        inner = _maybe_wrap_eye_anchor(inner, token, settings)
                        inner = _maybe_color_connector(inner, token, settings)
                        buf.append(inner)
                else:
                    buf.append(_escape_html(token))
            rendered_chunks.append(f'<span class="br-phrase">{"".join(buf)}</span>')
        return '<span class="br-phrase-gap"> </span>'.join(rendered_chunks)

    out_parts: list[str] = []
    last_end = 0
    for match in WORD_RE.finditer(text):
        start, end = match.span()
        if start > last_end:
            out_parts.append(_escape_html(text[last_end:start]))
        word = match.group(0)
        if settings.enabled:
            out_parts.append(transform_word_html(word, settings))
        else:
            inner = _escape_html(word)
            inner = _maybe_wrap_eye_anchor(inner, word, settings)
            inner = _maybe_color_connector(inner, word, settings)
            out_parts.append(inner)
        last_end = end
    if last_end < len(text):
        out_parts.append(_escape_html(text[last_end:]))
    return "".join(out_parts)


def _chunked_plain(text: str, chunk_size: int) -> str:
    """Chunk plain (non-bionic) text into N-word groups separated by spacers."""
    if chunk_size <= 0:
        return _escape_html(text)
    parts: list[str] = []
    buf: list[str] = []
    words = 0
    last_end = 0
    for match in WORD_RE.finditer(text):
        start, end = match.span()
        if start > last_end:
            buf.append(_escape_html(text[last_end:start]))
        buf.append(_escape_html(match.group(0)))
        words += 1
        last_end = end
        if words >= chunk_size:
            parts.append(f'<span class="br-phrase">{"".join(buf)}</span>')
            buf = []
            words = 0
    if last_end < len(text):
        buf.append(_escape_html(text[last_end:]))
    if buf:
        parts.append(f'<span class="br-phrase">{"".join(buf)}</span>')
    return '<span class="br-phrase-gap"> </span>'.join(parts)


def _escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


__all__ = [
    "BionicSettings",
    "transform_text_html",
    "transform_word_html",
]
