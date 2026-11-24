"""Read a PDF with PyMuPDF and return text blocks with page numbers.

Headings are detected from font size and bold text, so the chunker can split
the PDF by section.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

MIN_TEXT_CHARS = 50


@dataclass
class Block:
    page: int  # 1-based page number
    text: str
    is_heading: bool = False


@dataclass
class ParsedPDF:
    n_pages: int
    blocks: list[Block] = field(default_factory=list)


def _open(source):
    try:
        import pymupdf
    except ImportError:  # very old PyMuPDF versions
        import fitz as pymupdf
    if isinstance(source, (bytes, bytearray)):
        return pymupdf.open(stream=bytes(source), filetype="pdf")
    return pymupdf.open(str(source))


def _join_lines(lines: list[str]) -> str:
    """Join the lines of one block into a single paragraph."""
    text = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not text:
            text = line
        elif text.endswith("-") and len(text) > 1 and line[:1].islower():
            text = text[:-1] + line  # "learn-" + "ing" -> "learning"
        else:
            text = text + " " + line
    return re.sub(r"\s+", " ", text).strip()


def _extract_raw(doc) -> list[tuple[int, str, float, float, int]]:
    """Return (page, text, avg_font_size, bold_ratio, n_lines) for every text block."""
    raw = []
    for page_number, page in enumerate(doc, start=1):
        for block in page.get_text("dict").get("blocks", []):
            if block.get("type") != 0:  # 0 = text, 1 = image
                continue
            lines: list[str] = []
            chars = 0
            size_total = 0.0
            bold_chars = 0
            for line in block.get("lines", []):
                parts = []
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    parts.append(text)
                    n = len(text.strip())
                    if n == 0:
                        continue
                    chars += n
                    size_total += float(span.get("size", 0)) * n
                    font = str(span.get("font", "")).lower()
                    if (int(span.get("flags", 0)) & 16) or "bold" in font:
                        bold_chars += n
                lines.append("".join(parts))
            text = _join_lines(lines)
            if not text or chars == 0:
                continue
            raw.append((page_number, text, size_total / chars, bold_chars / chars, len(lines)))
    return raw


def _normalise_key(text: str) -> str:
    return re.sub(r"\d+", "#", text.lower()).strip()


def _drop_page_furniture(raw, n_pages: int):
    """Remove page numbers and headers/footers that repeat on many pages."""
    raw = [r for r in raw if not re.fullmatch(r"[\d\s./\-]+", r[1])]
    if n_pages < 4:
        return raw
    pages_with: dict[str, set[int]] = defaultdict(set)
    for page, text, *_ in raw:
        pages_with[_normalise_key(text)].add(page)
    limit = max(3, int(n_pages * 0.5))
    repeated = {key for key, pages in pages_with.items() if len(pages) >= limit}
    return [r for r in raw if not (_normalise_key(r[1]) in repeated and len(r[1]) <= 80)]


def _flag_headings(raw) -> list[bool]:
    """Decide which blocks are headings."""
    if not raw:
        return []
    weights: Counter = Counter()
    for _, text, size, _, _ in raw:
        weights[round(size, 1)] += len(text)
    body_size = weights.most_common(1)[0][0]

    def by_size(item) -> bool:
        _, text, size, _, _ = item
        return len(text) <= 120 and size >= body_size * 1.15

    def by_size_or_bold(item) -> bool:
        _, text, _, bold, n_lines = item
        return by_size(item) or (bold >= 0.8 and n_lines <= 2 and len(text) <= 80)

    for rule in (by_size_or_bold, by_size):
        flags = [rule(item) for item in raw]
        if sum(flags) <= 0.5 * len(raw):  # if most blocks look like headings, the rule is wrong
            return flags
    return [False] * len(raw)


def parse_pdf(source: str | Path | bytes) -> ParsedPDF:
    """Parse a PDF (file path or raw bytes) into text blocks."""
    doc = _open(source)
    try:
        n_pages = doc.page_count
        raw = _extract_raw(doc)
    finally:
        doc.close()

    if sum(len(item[1]) for item in raw) < MIN_TEXT_CHARS:
        raise ValueError(
            "This PDF has no readable text (it may be scanned images). "
            "Please use a text-based PDF."
        )

    raw = _drop_page_furniture(raw, n_pages)
    flags = _flag_headings(raw)
    blocks = [Block(page=item[0], text=item[1], is_heading=flag) for item, flag in zip(raw, flags)]
    return ParsedPDF(n_pages=n_pages, blocks=blocks)