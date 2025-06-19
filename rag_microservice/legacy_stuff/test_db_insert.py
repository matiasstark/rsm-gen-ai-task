import asyncio
from pathlib import Path
from rag_microservice.pdf_ingest import load_pdf_chunks
from rag_microservice.embeddings import embed_texts
from rag_microservice.db import insert_chunks

async def main():
    pdf_path = Path(__file__).parent / "documents" / "short_pdf_CV.pdf"
    document_name = pdf_path.name
    chunks = load_pdf_chunks(pdf_path)
    texts = [chunk["text"] for chunk in chunks if chunk["text"]]
    print(f"Embedding {len(texts)} chunks from {document_name}...")
    embeddings = embed_texts(texts)
    # Attach embeddings to chunks
    enriched_chunks = []
    for chunk, emb in zip(chunks, embeddings):
        if chunk["text"]:
            enriched_chunks.append({
                "page": chunk["page"],
                "text": chunk["text"],
                "embedding": emb,
            })
    print(f"Inserting {len(enriched_chunks)} chunks into the database...")
    await insert_chunks(enriched_chunks, document_name=document_name)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main()) 