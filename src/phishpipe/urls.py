"""Hide URLs behind placeholders and put them back.

A URL starts with http://, https:// or www. and ends at the next space.
Trailing punctuation is not part of the URL. Email addresses are not changed.
Every URL occurrence gets its own placeholder: {{URL_1}}, {{URL_2}}, ...
"""

from __future__ import annotations

import re

PLACEHOLDER_RE = re.compile(r"\{\{URL_(\d+)\}\}")
_URL_RE = re.compile(r"(?:https?://|(?<![\w.@/-])www\.)\S+", re.IGNORECASE)
_TRAILING = ".,;:!?)]}>'\""
_PREFIXES = ("http://", "https://", "www.")


class PlaceholderConflictError(ValueError):
    """The text already contains something that looks like a URL placeholder."""


def make_placeholder(number: int) -> str:
    return f"{{{{URL_{number}}}}}"


def mask_urls(text: str) -> tuple[str, list[str]]:
    """Return the text with placeholders and the list of original URLs (in order)."""
    if PLACEHOLDER_RE.search(text):
        raise PlaceholderConflictError("text already contains a URL placeholder")

    urls: list[str] = []
    parts: list[str] = []
    last = 0
    for match in _URL_RE.finditer(text):
        url = match.group().rstrip(_TRAILING)
        if url.lower() in _PREFIXES:  # nothing after the prefix, not a real URL
            continue
        end = match.start() + len(url)
        urls.append(url)
        parts.append(text[last : match.start()])
        parts.append(make_placeholder(len(urls)))
        last = end
    parts.append(text[last:])
    return "".join(parts), urls


def unmask_urls(text: str, urls: list[str]) -> str:
    """Put the original URLs back. Unknown placeholders are left as they are."""

    def replace(match: re.Match) -> str:
        index = int(match.group(1))
        if 1 <= index <= len(urls):
            return urls[index - 1]
        return match.group()

    return PLACEHOLDER_RE.sub(replace, text)
