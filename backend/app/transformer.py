"""Bionic reading transformation engine.

This module is the single source of truth for the bionic algorithm,
mirrored exactly by the frontend so that interactive previews match
exported files.
"""
from __future__ import annotations

import re

from .models import BionicSettings

WORD_RE = re.compile(r"(\w+)", re.UNICODE)


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


def transform_word_html(word: str, settings: BionicSettings) -> str:
    """Wrap `word` with HTML to render the bionic prefix."""
    prefix_len = _prefix_length(word, settings)
    if prefix_len == 0:
        return _maybe_color_vowels(word, settings)

    prefix = word[:prefix_len]
    suffix = word[prefix_len:]
    style_parts: list[str] = []
    if settings.use_color_instead_of_bold:
        style_parts.append(f"color:{settings.prefix_color}")
    style_parts.append("font-weight:700")
    style = ";".join(style_parts)

    prefix_rendered = _maybe_color_vowels(prefix, settings)
    suffix_rendered = _maybe_color_vowels(suffix, settings)
    return f'<b class="br-prefix" style="{style}">{prefix_rendered}</b>{suffix_rendered}'


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


def transform_text_html(text: str, settings: BionicSettings) -> str:
    """Apply bionic transformation to a free-form text string, returning HTML."""
    if not settings.enabled:
        return _escape_html(text)

    out_parts: list[str] = []
    last_end = 0
    for match in WORD_RE.finditer(text):
        start, end = match.span()
        if start > last_end:
            out_parts.append(_escape_html(text[last_end:start]))
        out_parts.append(transform_word_html(match.group(0), settings))
        last_end = end
    if last_end < len(text):
        out_parts.append(_escape_html(text[last_end:]))
    return "".join(out_parts)


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
