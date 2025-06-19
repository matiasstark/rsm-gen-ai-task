from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from rag_microservice.embeddings import embed_texts
from rag_microservice.db import create_table, insert_chunks, similarity_search, get_connection, delete_site_chunks, truncate_table, drop_table, count_chunks
from rag_microservice.unified_scraper import UnifiedWebScraper

app = FastAPI(
    title="RSM RAG Microservice",
    description="A Retrieval-Augmented Generation microservice for document ingestion and querying",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    question: str

class IngestRequest(BaseModel):
    site: str  # "pep8" or "think_python"

class ResetRequest(BaseModel):
    password: str

class SourceChunk(BaseModel):
    page: int
    text: str
    source_type: Optional[str] = None
    section_name: Optional[str] = None
    url: Optional[str] = None
    distance: Optional[float] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]


@app.get("/health", tags=["RSM main methods"])
def health():
    return {"status": "ok"}

@app.post("/reset", tags=["Helpers"])
async def reset_database(request: ResetRequest):
    """Reset the database by truncating the rag_chunks table. Requires password 'RSM'."""
    if request.password != "RSM":
        raise HTTPException(status_code=403, detail="Invalid password")
    
    await truncate_table()
    return {"status": "success", "message": "Database table truncated successfully"}

@app.get("/count", tags=["Helpers"])
async def get_chunk_count():
    """Get the total number of chunks in the database."""
    count = await count_chunks()
    return {"total_chunks": count}

@app.post("/ingest", tags=["RSM main methods"])
async def ingest(request: IngestRequest):
    await create_table()
    
    # Validate site parameter
    if request.site not in ["pep8", "think_python"]:
        raise HTTPException(status_code=400, detail="Site must be 'pep8' or 'think_python'")
    
    # Delete existing chunks for this site
    await delete_site_chunks(request.site)
    
    # Scrape the specified site
    scraper = UnifiedWebScraper()
    
    if request.site == "pep8":
        chunks = scraper.scrape_pep8()
    else:  # think_python
        chunks = scraper.scrape_think_python()
    
    if not chunks:
        raise HTTPException(status_code=500, detail=f"No chunks extracted from {request.site}")
    
    # Prepare chunks for database insertion
    texts = [chunk["text"] for chunk in chunks if chunk["text"]]
    embeddings = embed_texts(texts)
    
    enriched_chunks = []
    for chunk, emb in zip(chunks, embeddings):
        if chunk["text"]:
            enriched_chunks.append({
                "page": chunk.get("chunk_id", 1),  # Use chunk_id as page number
                "text": chunk["text"],
                "embedding": emb,
                "source_type": chunk["source_type"],
                "section_name": chunk.get("section_name", ""),  # Use section_name field from scraper
                "url": chunk.get("url", ""),
                "is_overlap": chunk.get("is_overlap", False)
            })
    
    await insert_chunks(enriched_chunks, document_name=request.site)
    
    return {
        "status": "ingested", 
        "message": f"for site: {request.site}, ingested {len(enriched_chunks)} chunks"
    }

@app.post("/query", response_model=QueryResponse, tags=["RSM main methods"])
async def query(request: QueryRequest):
    query_embedding = embed_texts([request.question])[0]
    results = await similarity_search(
        query_embedding, 
        top_k=5
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="No relevant chunks found.")
    
    # For demo, just concatenate the top chunks as the answer
    answer = "\n".join([r["text"] for r in results])
    
    # Create source chunks with all metadata
    sources = [
        SourceChunk(
            page=r["page"], 
            text=r["text"],
            source_type=r["source_type"],
            section_name=r["section_name"],
            url=r["url"],
            distance=r["distance"]
        ) 
        for r in results
    ]
    
    return QueryResponse(answer=answer, sources=sources) 