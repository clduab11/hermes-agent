"""Input validation and sanitisation helpers."""
from __future__ import annotations

import re
from typing import Any

__all__ = ["sanitize_text"]

_SCRIPT_RE = re.compile(r"<\/?script.*?>", re.IGNORECASE)


def sanitize_text(value: str) -> str:
    """Very small HTML/JS sanitiser used for defensive programming.

    This is not a replacement for a full sanitisation library but provides
    basic protection against embedded ``<script>`` tags and normalises
    whitespace. The function is intentionally conservative to avoid
    unexpected mutations of user provided content.
    """

    cleaned = _SCRIPT_RE.sub("", value)
    return re.sub(r"\s+", " ", cleaned).strip()
