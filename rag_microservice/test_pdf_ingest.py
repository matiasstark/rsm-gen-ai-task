from pathlib import Path
from rag_microservice.pdf_ingest import load_pdf_chunks

if __name__ == "__main__":
    pdf_path = Path(__file__).parent / "documents" / "short_pdf_CV.pdf"
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
    else:
        chunks = load_pdf_chunks(pdf_path)
        print(f"Loaded {len(chunks)} chunks from {pdf_path.name}")
        for chunk in chunks:
            print(f"Page {chunk['page']} (first 100 chars): {chunk['text'][:100]!r}") 