import asyncio
from rag_microservice.unified_scraper import UnifiedWebScraper, save_chunks_to_file
from rag_microservice.embeddings import embed_texts
from rag_microservice.db import create_table, insert_chunks, get_connection

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
    
    # Initialize scraper
    scraper = UnifiedWebScraper(max_chunk_length=1500, overlap_length=100)
    
    all_chunks = []
    
    # Scrape Think Python
    print("\n" + "="*50)
    print("SCRAPING THINK PYTHON BOOK")
    print("="*50)
    think_python_chunks = scraper.scrape_think_python()
    print(f"Extracted {len(think_python_chunks)} chunks from Think Python")
    all_chunks.extend(think_python_chunks)
    
    # Scrape PEP 8
    print("\n" + "="*50)
    print("SCRAPING PEP 8 STYLE GUIDE")
    print("="*50)
    pep8_chunks = scraper.scrape_pep8()
    print(f"Extracted {len(pep8_chunks)} chunks from PEP 8")
    all_chunks.extend(pep8_chunks)
    
    if not all_chunks:
        print("No chunks extracted. Exiting.")
        return
    
    # Save chunks to file for inspection
    print(f"\nSaving {len(all_chunks)} chunks to file for inspection...")
    save_chunks_to_file(all_chunks, "all_chunks.txt")
    
    # Prepare texts for embedding (the text already includes section context)
    texts = [chunk["text"] for chunk in all_chunks]
    print(f"Embedding {len(texts)} chunks...")
    embeddings = embed_texts(texts)
    
    # Prepare enriched chunks for database
    enriched_chunks = []
    for chunk, emb in zip(all_chunks, embeddings):
        # The text already includes section context from the scraper
        enriched_chunks.append({
            "page": chunk["chunk_id"],
            "text": chunk["text"],  # Already includes section context
            "embedding": emb,
            "source_type": chunk["source_type"],
            "chapter_num": chunk["chapter_num"],
            "section_name": chunk["section"],
            "url": chunk["url"],
            "is_overlap": chunk.get("is_overlap", False),
        })
    
    print(f"Inserting {len(enriched_chunks)} chunks into database...")
    await insert_chunks(enriched_chunks, document_name="Python_Documentation")
    print("Done!")
    
    # Print summary
    think_python_count = len([c for c in all_chunks if c["source_type"] == "think_python"])
    pep8_count = len([c for c in all_chunks if c["source_type"] == "pep8"])
    print(f"\nSummary:")
    print(f"- Think Python: {think_python_count} chunks")
    print(f"- PEP 8: {pep8_count} chunks")
    print(f"- Total: {len(all_chunks)} chunks")

if __name__ == "__main__":
    asyncio.run(main()) 