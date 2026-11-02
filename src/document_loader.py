"""Module 1 - Document loader.

Extracts text page by page from PDFs and keeps document/page metadata
so every chunk can later be cited back to its source.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path

import pymupdf as fitz

MAX_FILE_MB = 50
MIN_CHARS_PER_PAGE = 30  # below this a page probably needs OCR


@dataclass
class Page:
    doc_id: str
    filename: str
    page: int          # 1-based, matches the page number a human sees
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def make_doc_id(path: Path) -> str:
    """Stable ID from file contents, so renaming a file keeps citations valid."""
    digest = hashlib.sha1(path.read_bytes()).hexdigest()[:10]
    return f"{path.stem[:30]}_{digest}"


def load_pdf(path: str | Path) -> tuple[list[Page], list[str]]:
    """Return (pages, warnings) for a single PDF.

    Raises ValueError for files that are not usable PDFs.
    """
    path = Path(path)
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"{path.name}: not a PDF")
    if not path.exists() or path.stat().st_size == 0:
        raise ValueError(f"{path.name}: file is missing or empty")
    if path.stat().st_size > MAX_FILE_MB * 1024 * 1024:
        raise ValueError(f"{path.name}: larger than {MAX_FILE_MB} MB")

    try:
        doc = fitz.open(path)
    except Exception as exc:  # corrupt file
        raise ValueError(f"{path.name}: could not open PDF ({exc})") from exc

    doc_id = make_doc_id(path)
    pages: list[Page] = []
    warnings: list[str] = []
    with doc:
        for i, pdf_page in enumerate(doc, start=1):
            text = pdf_page.get_text("text")
            if len(text.strip()) < MIN_CHARS_PER_PAGE:
                warnings.append(f"{path.name} p.{i}: little/no text (scanned? needs OCR)")
                continue
            pages.append(Page(doc_id=doc_id, filename=path.name, page=i, text=text))

    if not pages:
        raise ValueError(f"{path.name}: no extractable text on any page")
    return pages, warnings


def load_folder(folder: str | Path) -> tuple[list[Page], list[str]]:
    """Load every PDF in a folder. Bad files become warnings, not crashes."""
    all_pages: list[Page] = []
    warnings: list[str] = []
    for pdf in sorted(Path(folder).glob("*.pdf")):
        try:
            pages, warns = load_pdf(pdf)
            all_pages.extend(pages)
            warnings.extend(warns)
        except ValueError as exc:
            warnings.append(str(exc))
    return all_pages, warnings
