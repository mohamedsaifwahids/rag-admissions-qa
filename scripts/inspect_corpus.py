"""Run this after dropping PDFs into data/documents/.

    python -m scripts.inspect_corpus            # default 250/50
    python -m scripts.inspect_corpus 500 100    # try other sizes

Prints a corpus summary, any extraction warnings, and a few sample chunks,
and saves all chunks to indexes/chunks.jsonl so you can eyeball them.
"""
import json
import random
import sys
from collections import Counter
from pathlib import Path

from src.document_loader import load_folder
from src.text_chunker import chunk_pages

DOCS = Path("data/documents")
OUT = Path("indexes/chunks.jsonl")


def main() -> None:
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    overlap = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    pages, warnings = load_folder(DOCS)
    if not pages:
        print(f"No usable PDFs in {DOCS}/ - add some and re-run.")
        for w in warnings:
            print("  !", w)
        return

    chunks = chunk_pages(pages, chunk_size=size, overlap=overlap)

    print(f"\n=== Corpus: {DOCS} | chunk_size={size} overlap={overlap} ===")
    per_doc = Counter(p.filename for p in pages)
    chunks_per_doc = Counter(c.filename for c in chunks)
    for name in sorted(per_doc):
        print(f"  {name:<55} {per_doc[name]:>4} pages  {chunks_per_doc[name]:>5} chunks")
    print(f"  TOTAL: {len(per_doc)} docs, {len(pages)} pages, {len(chunks)} chunks")

    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings[:20]:
            print("  !", w)

    print("\n=== 3 random chunks (check the text looks clean) ===")
    for c in random.sample(chunks, min(3, len(chunks))):
        print(f"\n[{c.chunk_id}] {c.filename} p.{c.page}\n{c.text[:500]}...")

    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
    print(f"\nSaved {len(chunks)} chunks -> {OUT}")


if __name__ == "__main__":
    main()
