"""Split a parsed PDF into section-aware chunks (keeping page numbers)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from core import config
from core.pdf_parser import ParsedPDF

PAGES_PER_FALLBACK_SECTION = 3  # used when the PDF has no detectable headings
MAX_TITLE_CHARS = 100


@dataclass
class Chunk:
    index: int
    text: str
    page: int      # page where the chunk starts
    section: str

    @property
    def for_embedding(self) -> str:
        """Text that is turned into a vector (the section title helps retrieval)."""
        return f"{self.section}\n{self.text}" if self.section else self.text


def build_chunks(
    parsed: ParsedPDF,
    max_chars: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    max_chars = max_chars or config.CHUNK_MAX_CHARS
    overlap = config.CHUNK_OVERLAP_CHARS if overlap is None else overlap
    chunks: list[Chunk] = []
    for title, items in _group_sections(parsed):
        # Never let overlap or a chunk cross a physical PDF page.
        from itertools import groupby
        for page, group in groupby(items, key=lambda item: item[0]):
            for _, text in _chunk_section(list(group), max_chars, overlap):
                chunks.append(Chunk(len(chunks), text, page, title))
    return chunks


def _group_sections(parsed: ParsedPDF) -> list[tuple[str, list[tuple[int, str]]]]:
    blocks = parsed.blocks

    if not any(b.is_heading for b in blocks):
        groups: dict[str, list[tuple[int, str]]] = {}
        step = PAGES_PER_FALLBACK_SECTION
        for b in blocks:
            start = ((b.page - 1) // step) * step + 1
            end = min(start + step - 1, max(parsed.n_pages, b.page))
            title = f"Page {start}" if start == end else f"Pages {start}-{end}"
            groups.setdefault(title, []).append((b.page, b.text))
        return list(groups.items())

    sections: list[tuple[str, list[tuple[int, str]]]] = []
    title = "Introduction"
    items: list[tuple[int, str]] = []
    title_is_default = True
    for b in blocks:
        if b.is_heading:
            if not items:
                # first heading, or a sub-heading right after a heading: merge into the title
                title = b.text if title_is_default else f"{title} {b.text}"
                title = title[:MAX_TITLE_CHARS]
                title_is_default = False
            else:
                sections.append((title, items))
                title, items, title_is_default = b.text[:MAX_TITLE_CHARS], [], False
        else:
            items.append((b.page, b.text))
    if items:
        sections.append((title, items))
    return sections


def _chunk_section(
    items: list[tuple[int, str]], max_chars: int, overlap: int
) -> list[tuple[int, str]]:
    piece_limit = max(200, max_chars - overlap)
    out: list[tuple[int, str]] = []
    buffer: list[tuple[int, str]] = []
    buffer_len = 0
    fresh = 0  # number of new (non-carried-over) pieces in the buffer

    def flush() -> None:
        nonlocal buffer, buffer_len, fresh
        if fresh:
            out.append((buffer[0][0], "\n".join(text for _, text in buffer)))
        carry = buffer[-1] if buffer and len(buffer[-1][1]) <= overlap else None
        buffer = [carry] if carry else []
        buffer_len = len(carry[1]) + 1 if carry else 0
        fresh = 0

    for page, text in items:
        for piece in _split_long(text, piece_limit):
            if fresh and buffer_len + len(piece) + 1 > max_chars:
                flush()
            buffer.append((page, piece))
            buffer_len += len(piece) + 1
            fresh += 1
    if fresh:
        flush()
    return out


def _split_long(text: str, limit: int) -> list[str]:
    """Split a long paragraph at sentence ends, then at spaces, then anywhere."""
    if len(text) <= limit:
        return [text]
    sentences = re.split(r"(?<=[.!?。])\s+", text)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        while len(sentence) > limit:  # very long sentence, or Thai text without spaces
            if current:
                pieces.append(current)
                current = ""
            cut = sentence.rfind(" ", 0, limit)
            if cut < limit * 0.5:
                cut = limit
            pieces.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if current and len(current) + 1 + len(sentence) > limit:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return [p for p in pieces if p]