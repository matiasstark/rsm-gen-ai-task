from typing import List, Dict
from pathlib import Path
from pypdf import PdfReader


def load_pdf_chunks(pdf_path: Path) -> List[Dict[str, str]]:
    """
    Load a PDF and split it into per-page chunks.
    Returns a list of dicts: {"page": int, "text": str}
    """
    reader = PdfReader(str(pdf_path))
    chunks = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        chunks.append({"page": i, "text": text.strip()})
    return chunks 