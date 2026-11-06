"""Defense layers for the vendor desk agent."""

from __future__ import annotations

import re

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(the\s+)?handbook",
    r"you\s+are\s+now",
    r"system\s*prompt",
    r"send_email\s*\(",
    r"approve_payment\s*\(",
    r"transfer\s+funds",
    r"wire\s+transfer",
    r"override\s+decision",
    r"always\s+recommend",
    r"do\s+not\s+follow\s+the\s+handbook",
]


def sanitize_document_text(text: str) -> tuple[str, list[str]]:
    """Code-layer defense: neutralize common injection phrases before the model."""
    hits: list[str] = []
    cleaned = text
    for pat in INJECTION_PATTERNS:
        if re.search(pat, cleaned, flags=re.IGNORECASE):
            hits.append(pat)
            cleaned = re.sub(pat, "[REDACTED_INJECTION]", cleaned, flags=re.IGNORECASE)
    # Strip HTML comments often used to hide payloads
    if re.search(r"<!--.*?-->", cleaned, flags=re.DOTALL):
        hits.append("html_comment")
        cleaned = re.sub(r"<!--.*?-->", " ", cleaned, flags=re.DOTALL)
    # Strip CSS/display:none style hidden blocks (best-effort)
    if "display:none" in cleaned.lower() or "display: none" in cleaned.lower():
        hits.append("display_none")
        cleaned = re.sub(
            r"<[^>]+style=['\"][^'\"]*display\s*:\s*none[^'\"]*['\"][^>]*>.*?</[^>]+>",
            " ",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
    return cleaned, hits
