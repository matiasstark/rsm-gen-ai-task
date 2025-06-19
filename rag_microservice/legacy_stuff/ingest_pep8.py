import asyncio
from rag_microservice.legacy_stuff.web_scraper import extract_sections_from_html
from rag_microservice.embeddings import embed_texts
from rag_microservice.db import create_table, insert_chunks, get_connection

PEP8_URL = "https://peps.python.org/pep-0008/"
DOCUMENT_NAME = "PEP_8_Style_Guide"
MAX_CHUNK_LENGTH = 2000

async def truncate_table():
    conn = await get_connection()
    try:
        await conn.execute("TRUNCATE TABLE rag_chunks;")
        print("Table 'rag_chunks' truncated.")
    finally:
        await conn.close()

async def main():
    print("Creating table if not exists...")
    await create_table()
    
    print("Truncating table...")
    await truncate_table()
    
    print(f"Extracting sections from {PEP8_URL}...")
    chunks = extract_sections_from_html(PEP8_URL, max_chunk_length=MAX_CHUNK_LENGTH)
    print(f"Extracted {len(chunks)} chunks")
    
    if not chunks:
        print("No chunks extracted. Exiting.")
        return
    
    # Prepare texts for embedding
    texts = [chunk["text"] for chunk in chunks]
    print("Embedding chunks...")
    embeddings = embed_texts(texts)
    
    # Prepare enriched chunks for database
    enriched_chunks = []
    for chunk, emb in zip(chunks, embeddings):
        enriched_chunks.append({
            "page": chunk["chunk_id"],  # Use chunk_id as page number
            "text": f"Section: {chunk['section']}\n\n{chunk['text']}",
            "embedding": emb,
        })
    
    print(f"Inserting {len(enriched_chunks)} chunks into database...")
    await insert_chunks(enriched_chunks, document_name=DOCUMENT_NAME)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main()) 