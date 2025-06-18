from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
from pathlib import Path

from rag_microservice.pdf_ingest import load_pdf_chunks
from rag_microservice.embeddings import embed_texts
from rag_microservice.db import create_table, insert_chunks, similarity_search, get_connection

app = FastAPI()

PDF_FILENAME = "short_pdf_CV.pdf"  # Default PDF for demo

class QueryRequest(BaseModel):
    question: str

class SourceChunk(BaseModel):
    page: int
    text: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]

@app.get("/health")
def health():
    return {"status": "ok"}

async def truncate_table():
    conn = await get_connection()
    try:
        await conn.execute("TRUNCATE TABLE rag_chunks;")
    finally:
        await conn.close()

@app.post("/ingest")
async def ingest():
    await create_table()
    await truncate_table()
    pdf_path = Path(__file__).parent / "documents" / PDF_FILENAME
    document_name = pdf_path.name
    chunks = load_pdf_chunks(pdf_path)
    texts = [chunk["text"] for chunk in chunks if chunk["text"]]
    embeddings = embed_texts(texts)
    enriched_chunks = []
    for chunk, emb in zip(chunks, embeddings):
        if chunk["text"]:
            enriched_chunks.append({
                "page": chunk["page"],
                "text": chunk["text"],
                "embedding": emb,
            })
    await insert_chunks(enriched_chunks, document_name=document_name)
    return {"status": "ingested", "chunks": len(enriched_chunks)}

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    document_name = PDF_FILENAME
    query_embedding = embed_texts([request.question])[0]
    results = await similarity_search(query_embedding, document_name=document_name, top_k=5)
    if not results:
        raise HTTPException(status_code=404, detail="No relevant chunks found.")
    # For demo, just concatenate the top chunks as the answer
    answer = "\n".join([r["text"] for r in results])
    sources = [SourceChunk(page=r["page"], text=r["text"]) for r in results]
    return QueryResponse(answer=answer, sources=sources) 