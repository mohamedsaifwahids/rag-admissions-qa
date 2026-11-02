"""Module 2 - Preprocessing and chunking.

Splits each page into overlapping word windows. Chunks never cross a page
boundary, so every chunk has exactly one page number to cite.
Chunk size/overlap are parameters so Experiment A (250/500/800) is a
one-line change.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict

from .document_loader import Page


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    filename: str
    page: int
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def normalize(text: str) -> str:
    """Tidy whitespace but keep paragraph breaks."""
    text = text.replace("­", "")              # soft hyphens
    text = re.sub(r"-\n(\w)", r"\1", text)          # re-join hyphenated line breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)    # single newline -> space
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def chunk_pages(pages: list[Page], chunk_size: int = 250, overlap: int = 50) -> list[Chunk]:
    """Word-based sliding window. chunk_size and overlap are in words
    (roughly 0.75 words per token, so 250 words ~ 330 tokens)."""
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    step = chunk_size - overlap
    chunks: list[Chunk] = []
    for p in pages:
        words = normalize(p.text).split()
        if not words:
            continue
        n = 0
        for start in range(0, len(words), step):
            window = words[start:start + chunk_size]
            chunks.append(Chunk(
                chunk_id=f"{p.doc_id}_p{p.page}_c{n}",
                doc_id=p.doc_id,
                filename=p.filename,
                page=p.page,
                text=" ".join(window),
            ))
            n += 1
            if start + chunk_size >= len(words):
                break
    return chunks
