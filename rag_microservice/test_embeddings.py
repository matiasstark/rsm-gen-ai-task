from pathlib import Path
from rag_microservice.pdf_ingest import load_pdf_chunks
from rag_microservice.embeddings import embed_texts

if __name__ == "__main__":
    pdf_path = Path(__file__).parent / "documents" / "short_pdf_CV.pdf"
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
    else:
        chunks = load_pdf_chunks(pdf_path)
        texts = [chunk["text"] for chunk in chunks if chunk["text"]]
        print(f"Embedding {len(texts)} chunks...")
        embeddings = embed_texts(texts)
        print(f"Embeddings shape: {len(embeddings)} x {len(embeddings[0]) if embeddings else 0}")
        print(f"First embedding (first 5 dims): {embeddings[0][:5] if embeddings else 'N/A'}") 