from __future__ import annotations
import sys
from pathlib import Path
from typing import List, Dict

import fitz  # PyMuPDF
from ebooklib import epub
import ebooklib
from lxml import html


def extract_pdf(path: Path) -> List[Dict[str, str]]:
    doc = fitz.open(path)
    sections = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        sections.append({"title": f"Page {page_num + 1}", "text": text.strip()})
    return sections


def extract_epub(path: Path) -> List[Dict[str, str]]:
    book = epub.read_epub(str(path))
    sections = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        tree = html.fromstring(item.get_content())
        text = tree.text_content()
        title = item.get_name()
        sections.append({"title": title, "text": text.strip()})
    return sections


def write_sections(sections: List[Dict[str, str]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as f:
        for sec in sections:
            f.write(f"# {sec['title']}\n\n{sec['text']}\n\n")


def ingest_document(file_path: str) -> Path:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{path.stem}.md"

    if path.suffix.lower() == ".pdf":
        sections = extract_pdf(path)
    elif path.suffix.lower() == ".epub":
        sections = extract_epub(path)
    else:
        raise ValueError("Unsupported file type. Use PDF or EPUB.")

    write_sections(sections, output_path)
    return output_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python document_ingestor.py <file.pdf|file.epub>")
        sys.exit(1)
    result = ingest_document(sys.argv[1])
    print(f"Written output to {result}")
