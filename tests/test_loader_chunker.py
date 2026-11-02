"""Covers guide tests T01 (valid PDF) and T02 (empty/corrupt PDF)."""
import pymupdf as fitz
import pytest

from src.document_loader import load_pdf, load_folder
from src.text_chunker import chunk_pages, normalize


def make_pdf(path, pages_text):
    doc = fitz.open()
    for t in pages_text:
        page = doc.new_page()
        page.insert_textbox(fitz.Rect(50, 50, 550, 800), t, fontsize=10)
    doc.save(path)


def test_valid_pdf_keeps_page_numbers(tmp_path):
    pdf = tmp_path / "policy.pdf"
    make_pdf(pdf, ["Applicants must hold " * 20, "Deadline is 30 June " * 20])
    pages, warnings = load_pdf(pdf)
    assert [p.page for p in pages] == [1, 2]
    assert "Deadline" in pages[1].text
    assert warnings == []


def test_blank_page_warns_not_crashes(tmp_path):
    pdf = tmp_path / "mixed.pdf"
    make_pdf(pdf, ["Real text here " * 20, ""])
    pages, warnings = load_pdf(pdf)
    assert len(pages) == 1 and len(warnings) == 1


def test_empty_and_corrupt_files_rejected(tmp_path):
    (tmp_path / "empty.pdf").write_bytes(b"")
    (tmp_path / "corrupt.pdf").write_bytes(b"not a pdf at all")
    with pytest.raises(ValueError):
        load_pdf(tmp_path / "empty.pdf")
    with pytest.raises(ValueError):
        load_pdf(tmp_path / "corrupt.pdf")
    pages, warnings = load_folder(tmp_path)  # folder load survives bad files
    assert pages == [] and len(warnings) == 2


def test_chunks_overlap_and_stay_on_page(tmp_path):
    pdf = tmp_path / "long.pdf"
    words = " ".join(f"w{i}" for i in range(600))
    make_pdf(pdf, [words])
    pages, _ = load_pdf(pdf)
    chunks = chunk_pages(pages, chunk_size=250, overlap=50)
    assert all(c.page == 1 for c in chunks)
    first, second = chunks[0].text.split(), chunks[1].text.split()
    assert first[-50:] == second[:50]          # overlap is exact
    assert len({c.chunk_id for c in chunks}) == len(chunks)  # IDs unique


def test_normalize_rejoins_hyphenation():
    assert normalize("admis-\nsion policy") == "admission policy"
