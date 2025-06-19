from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import os

from rag_microservice.embeddings import embed_texts
from rag_microservice.db import create_table, insert_chunks, similarity_search, get_connection, delete_site_chunks, truncate_table, drop_table, count_chunks
from rag_microservice.unified_scraper import UnifiedWebScraper
from rag_microservice.llm_service import LLMService
from rag_microservice.observability import obs_manager, get_metrics, get_metrics_content_type
from openai import OpenAI

app = FastAPI(
    title="RSM RAG Microservice",
    description="A Retrieval-Augmented Generation microservice for document ingestion and querying",
    version="1.0.0"
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests with timing."""
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log the request
    obs_manager.log_request(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration=duration,
        user_agent=request.headers.get("user-agent", ""),
        client_ip=request.client.host if request.client else None
    )
    
    return response

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

@app.get("/metrics", tags=["Helpers"])
async def metrics():
    """Get Prometheus metrics."""
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )

@app.post("/ingest", tags=["RSM main methods"])
async def ingest(request: IngestRequest):
    start_time = time.time()
    
    # Create a Langfuse trace for this ingestion
    trace = obs_manager.create_langfuse_trace(
        name="rag-ingest",
        metadata={
            "site": request.site,
            "endpoint": "/ingest"
        }
    )
    
    try:
        await create_table()
        
        # Validate site parameter
        if request.site not in ["pep8", "think_python"]:
            raise HTTPException(status_code=400, detail="Site must be 'pep8' or 'think_python'")
        
        # Create span for site deletion
        delete_span = obs_manager.create_langfuse_span(trace, "delete-existing-chunks")
        
        # Delete existing chunks for this site
        await delete_site_chunks(request.site)
        
        if delete_span:
            delete_span.end(metadata={"site": request.site})
        
        # Create span for scraping
        scrape_span = obs_manager.create_langfuse_span(trace, "scrape-content")
        
        # Scrape the specified site
        scraper = UnifiedWebScraper()
        
        if request.site == "pep8":
            chunks = scraper.scrape_pep8()
        else:  # think_python
            chunks = scraper.scrape_think_python()
        
        if scrape_span:
            scrape_span.end(metadata={"num_chunks": len(chunks), "site": request.site})
        
        if not chunks:
            raise HTTPException(status_code=500, detail=f"No chunks extracted from {request.site}")
        
        # Create span for embedding
        embed_span = obs_manager.create_langfuse_span(trace, "create-embeddings")
        
        # Prepare chunks for database insertion
        texts = [chunk["text"] for chunk in chunks if chunk["text"]]
        embeddings = embed_texts(texts)
        
        if embed_span:
            embed_span.end(metadata={"num_texts": len(texts)})
        
        # Create span for database insertion
        db_span = obs_manager.create_langfuse_span(trace, "insert-chunks")
        
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
        
        if db_span:
            db_span.end(metadata={"num_chunks": len(enriched_chunks)})
        
        duration = time.time() - start_time
        
        # Log the ingestion operation
        obs_manager.log_ingestion_operation(
            source_type=request.site,
            duration=duration,
            num_chunks=len(enriched_chunks)
        )
        
        return {
            "status": "ingested", 
            "message": f"for site: {request.site}, ingested {len(enriched_chunks)} chunks"
        }
        
    except Exception as e:
        duration = time.time() - start_time
        obs_manager.log_error("ingest", e, site=request.site)
        
        # Log error in trace if available
        if trace:
            error_span = trace.span(name="error", level="ERROR")
            error_span.end(metadata={"error": str(e), "error_type": type(e).__name__})
        
        raise
    finally:
        # Flush traces to ensure they are sent to Langfuse
        if trace:
            obs_manager.flush_langfuse()

@app.post("/query", response_model=QueryResponse, tags=["RSM main methods"])
async def query(request: QueryRequest):
    # Create a Langfuse trace for this query
    trace = obs_manager.create_langfuse_trace(
        name="rag-query",
        metadata={
            "question": request.question,
            "endpoint": "/query"
        }
    )
    
    try:
        # Initialize LLM service
        llm_service = LLMService()
        
        # Create span for embedding
        embed_span = obs_manager.create_langfuse_span(trace, "embed-query")
        
        # Perform semantic search
        query_embedding = embed_texts([request.question])[0]
        
        if embed_span:
            embed_span.end(metadata={"num_texts": 1})
        
        # Create span for search
        search_span = obs_manager.create_langfuse_span(trace, "similarity-search")
        
        results = await similarity_search(
            query_embedding, 
            top_k=5
        )
        
        if search_span:
            search_span.end(metadata={"num_results": len(results), "top_k": 5})
        
        if not results:
            raise HTTPException(status_code=404, detail="No relevant chunks found.")
        
        # Create span for LLM generation
        llm_span = obs_manager.create_langfuse_span(trace, "llm-generation")
        
        # Generate response using LLM
        llm_response = llm_service.generate_response_with_sources(request.question, results)
        
        if llm_span:
            llm_span.end(metadata={
                "model": llm_service.model_name,
                "num_sources": llm_response["num_sources"]
            })
        
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
        
        return QueryResponse(
            answer=llm_response["answer"], 
            sources=sources
        )
        
    except Exception as e:
        # Log error in trace if available
        if trace:
            error_span = trace.span(name="error", level="ERROR")
            error_span.end(metadata={"error": str(e), "error_type": type(e).__name__})
        raise
    finally:
        # Flush traces to ensure they are sent to Langfuse
        if trace:
            obs_manager.flush_langfuse() 