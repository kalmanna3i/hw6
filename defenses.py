"""Code-layer defenses: drop text a person would not see, before the model reads it."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

from pypdf import PdfReader

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(the\s+)?handbook",
    r"you\s+are\s+now",
    r"system\s*prompt",
    r"send_email\s*\(",
    r"approve_payment\s*\(",
    r"do\s+not\s+follow\s+the\s+handbook",
]

_DROP_TAGS = {"script", "style", "noscript", "template", "svg", "iframe", "object"}
_VOID_TAGS = {"meta", "link", "br", "hr", "img", "input", "source", "wbr"}
_CLASS_RULE = re.compile(r"\.([A-Za-z0-9_-]+)\s*\{([^}]*)\}", re.I)
_STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.I | re.S)


def style_hides(style: str) -> bool:
    """True when CSS would hide the text from a person looking at the page."""
    s = re.sub(r"\s+", "", style.lower())
    if any(
        token in s
        for token in (
            "display:none",
            "visibility:hidden",
            "opacity:0;",
            "opacity:0.0",
            "color:white",
            "color:#fff;",
            "color:#ffffff",
            "color:rgb(255,255,255)",
            "text-indent:-",
            "left:-",
            "top:-",
            "clip:rect(0",
        )
    ):
        return True
    if s.endswith("opacity:0"):
        return True
    match = re.search(r"font-size:([0-9.]+)(px|pt|em|%)?", s)
    if match and float(match.group(1)) < 2:
        return True
    return False


def _hiding_classes(html: str) -> set[str]:
    bad: set[str] = set()
    for block in _STYLE_BLOCK.findall(html):
        for name, body in _CLASS_RULE.findall(block):
            if style_hides(body):
                bad.add(name)
    return bad


class _VisibleText(HTMLParser):
    def __init__(self, hidden_classes: set[str]):
        super().__init__(convert_charrefs=True)
        self.hidden_classes = hidden_classes
        self.drop_depth = 0
        self.parts: list[str] = []

    def _classes(self, attrs: list[tuple[str, str | None]]) -> set[str]:
        for key, value in attrs:
            if key == "class" and value:
                return set(value.split())
        return set()

    def _start(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.drop_depth:
            if tag not in _VOID_TAGS:
                self.drop_depth += 1
            return
        attr = {key: (value or "") for key, value in attrs}
        hide = (
            tag in _DROP_TAGS
            or "hidden" in attr
            or attr.get("aria-hidden", "").lower() == "true"
            or style_hides(attr.get("style", ""))
            or bool(self._classes(attrs) & self.hidden_classes)
        )
        if hide and tag not in _VOID_TAGS:
            self.drop_depth = 1
            return
        if tag in _VOID_TAGS or hide:
            return
        if tag in {"p", "div", "tr", "li", "h1", "h2", "br", "table"}:
            self.parts.append("\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if self.drop_depth and tag not in _VOID_TAGS:
            self.drop_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.drop_depth:
            self.parts.append(data)

    def handle_comment(self, data: str) -> None:
        return


def strip_hidden_html(text: str) -> tuple[str, list[str]]:
    """Keep the words a browser would show. Drop comments, scripts, and hidden nodes."""
    hits: list[str] = []
    if "<!--" in text:
        hits.append("html_comment")
    lower = text.lower()
    for label, needle in (
        ("script", "<script"),
        ("template", "<template"),
        ("svg", "<svg"),
        ("display_none", "display:none"),
        ("display_none", "display: none"),
        ("font_size_0", "font-size:0"),
        ("font_size_0", "font-size: 0"),
        ("white_text", "color:#fff"),
        ("white_text", "color: #fff"),
        ("white_text", "color:#ffffff"),
    ):
        if needle in lower and label not in hits:
            hits.append(label)
    parser = _VisibleText(_hiding_classes(text))
    parser.feed(text)
    parser.close()
    cleaned = re.sub(r"[ \t]+\n", "\n", "".join(parser.parts))
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned, hits


def _pdf_unescape(raw: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(raw):
        if raw[i] == "\\" and i + 1 < len(raw):
            nxt = raw[i + 1]
            mapping = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f"}
            if nxt in mapping:
                out.append(mapping[nxt])
                i += 2
                continue
            if nxt.isdigit():
                octal = nxt
                i += 2
                while i < len(raw) and raw[i].isdigit() and len(octal) < 3:
                    octal += raw[i]
                    i += 1
                out.append(chr(int(octal, 8)))
                continue
            out.append(nxt)
            i += 2
            continue
        out.append(raw[i])
        i += 1
    return "".join(out)


_PDF_TOKEN = re.compile(
    r"(?P<rg>[0-9.]+ [0-9.]+ [0-9.]+ rg)"
    r"|(?P<x>[-\d.]+) (?P<y>[-\d.]+) Tm"
    r"|\((?P<s>(?:\\.|[^\\)])*)\)\s*Tj",
)


def extract_pdf_text(path: Path, *, drop_hidden: bool) -> tuple[str, list[str]]:
    """Read PDF text. With defenses, skip off-page text and white-on-white text."""
    reader = PdfReader(str(path))
    hits: list[str] = []
    if not drop_hidden:
        return "\n".join((page.extract_text() or "") for page in reader.pages), hits

    pages: list[str] = []
    for page in reader.pages:
        box = page.mediabox
        left, bottom, right, top = (float(box[i]) for i in range(4))
        contents = page.get_contents()
        if contents is None:
            pages.append(page.extract_text() or "")
            continue
        data = contents.get_data().decode("latin1", errors="replace")
        color = (0.0, 0.0, 0.0)
        x = y = 0.0
        kept: list[str] = []
        for match in _PDF_TOKEN.finditer(data):
            if match.group("rg"):
                parts = match.group("rg").split()
                color = (float(parts[0]), float(parts[1]), float(parts[2]))
                continue
            if match.group("x") is not None and match.group("s") is None:
                x = float(match.group("x"))
                y = float(match.group("y"))
                continue
            if match.group("s") is None:
                continue
            text = _pdf_unescape(match.group("s"))
            off_page = x < left - 1 or x > right + 1 or y < bottom - 1 or y > top + 1
            white = all(channel >= 0.92 for channel in color)
            if off_page or white:
                hits.append("off_page_text" if off_page else "white_text")
                continue
            kept.append(text)
        pages.append("\n".join(kept))
    # unique hit labels, preserve order
    seen: list[str] = []
    for hit in hits:
        if hit not in seen:
            seen.append(hit)
    return "\n".join(pages), seen


def redact_injection_phrases(text: str) -> tuple[str, list[str]]:
    hits: list[str] = []
    cleaned = text
    for pat in INJECTION_PATTERNS:
        if re.search(pat, cleaned, flags=re.IGNORECASE):
            hits.append(pat)
            cleaned = re.sub(pat, "[REDACTED_INJECTION]", cleaned, flags=re.IGNORECASE)
    return cleaned, hits


def sanitize_document_text(text: str) -> tuple[str, list[str]]:
    """Structural cleanup, then a short phrase pass for classic injection lines."""
    hits: list[str] = []
    cleaned = text
    if "<html" in text.lower() or "<table" in text.lower() or "<p" in text.lower():
        cleaned, html_hits = strip_hidden_html(text)
        hits.extend(html_hits)
    cleaned, phrase_hits = redact_injection_phrases(cleaned)
    hits.extend(phrase_hits)
    return cleaned, hits
