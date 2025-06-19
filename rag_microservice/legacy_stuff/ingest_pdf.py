import asyncio
from pathlib import Path
from pdf_ingest import load_pdf_chunks
from embeddings import embed_texts
from db import create_table, insert_chunks, get_connection

PDF_FILENAME = "short_pdf_CV.pdf"  # Change as needed
TRUNCATE_FIRST = True  # Set to True to clean the table before ingesting

def print_banner(msg: str):
    print(f"\n{'='*10} {msg} {'='*10}\n")

async def truncate_table():
    conn = await get_connection()
    try:
        await conn.execute("TRUNCATE TABLE rag_chunks;")
        print("Table 'rag_chunks' truncated.")
    finally:
        await conn.close()

async def main():
    print_banner("Creating table if not exists")
    await create_table()
    if TRUNCATE_FIRST:
        print_banner("Truncating table")
        await truncate_table()
    pdf_path = Path(__file__).parent / "documents" / PDF_FILENAME
    document_name = pdf_path.name
    print_banner(f"Loading and chunking {document_name}")
    chunks = load_pdf_chunks(pdf_path)
    texts = [chunk["text"] for chunk in chunks if chunk["text"]]
    print(f"Embedding {len(texts)} chunks...")
    embeddings = embed_texts(texts)
    enriched_chunks = []
    for chunk, emb in zip(chunks, embeddings):
        if chunk["text"]:
            enriched_chunks.append({
                "page": chunk["page"],
                "text": chunk["text"],
                "embedding": emb,
            })
    print_banner(f"Inserting {len(enriched_chunks)} chunks into the database")
    await insert_chunks(enriched_chunks, document_name=document_name)
    print_banner("Done!")

if __name__ == "__main__":
    asyncio.run(main()) 