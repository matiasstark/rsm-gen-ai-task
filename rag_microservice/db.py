import os
import asyncpg
from typing import Optional, List, Dict, Any

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))
DB_NAME = os.getenv("POSTGRES_DB", "ragdb")
DB_USER = os.getenv("POSTGRES_USER", "raguser")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "ragpass")

VECTOR_DIM = 384  # For all-MiniLM-L6-v2

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS rag_chunks (
    id SERIAL PRIMARY KEY,
    document_name TEXT NOT NULL,
    page INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR({VECTOR_DIM}),
    source_type TEXT,
    section_name TEXT,
    url TEXT,
    is_overlap BOOLEAN DEFAULT FALSE
);
"""

async def get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )

async def create_table():
    conn = await get_connection()
    try:
        await conn.execute(CREATE_TABLE_SQL)
    finally:
        await conn.close()

async def drop_table():
    """Drop the rag_chunks table if it exists."""
    conn = await get_connection()
    try:
        await conn.execute("DROP TABLE IF EXISTS rag_chunks;")
        print("Dropped rag_chunks table")
    finally:
        await conn.close()

async def reset_table():
    """Drop and recreate the rag_chunks table."""
    await drop_table()
    await create_table()
    print("Reset rag_chunks table successfully")

async def delete_site_chunks(site: str):
    """Delete chunks for a specific site from the database."""
    conn = await get_connection()
    try:
        await conn.execute("DELETE FROM rag_chunks WHERE source_type = $1", site)
        print(f"Deleted chunks for site: {site}")
    finally:
        await conn.close()

async def truncate_table():
    """Truncate all data from the rag_chunks table."""
    conn = await get_connection()
    try:
        await conn.execute("TRUNCATE TABLE rag_chunks;")
        print("Truncated rag_chunks table")
    finally:
        await conn.close()

async def count_chunks() -> int:
    """Count the total number of chunks in the rag_chunks table."""
    conn = await get_connection()
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM rag_chunks")
        return count
    finally:
        await conn.close()

async def insert_chunks(chunks: List[Dict[str, Any]], document_name: str) -> None:
    conn = await get_connection()
    try:
        await conn.executemany(
            """
            INSERT INTO rag_chunks (document_name, page, chunk_text, embedding, source_type, section_name, url, is_overlap)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            [
                (
                    document_name,
                    chunk["page"],
                    chunk["text"],
                    str(chunk["embedding"]),
                    chunk.get("source_type"),
                    chunk.get("section_name"),
                    chunk.get("url"),
                    chunk.get("is_overlap", False),
                )
                for chunk in chunks
            ]
        )
    finally:
        await conn.close()

async def similarity_search(query_embedding: List[float], document_name: str = None, source_type: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
    conn = await get_connection()
    try:
        # Build dynamic query based on filters
        query = f"""
            SELECT id, page, chunk_text, embedding, embedding <-> $1 AS distance, 
                   source_type, section_name, url
            FROM rag_chunks
            WHERE 1=1
        """
        params = [str(query_embedding)]
        param_count = 1
        
        if document_name:
            param_count += 1
            query += f" AND document_name = ${param_count}"
            params.append(document_name)
        
        if source_type:
            param_count += 1
            query += f" AND source_type = ${param_count}"
            params.append(source_type)
        
        query += f" ORDER BY embedding <-> $1 LIMIT {top_k}"
        
        rows = await conn.fetch(query, *params)
        return [
            {
                "id": row["id"],
                "page": row["page"],
                "text": row["chunk_text"],
                "distance": row["distance"],
                "source_type": row["source_type"],
                "section_name": row["section_name"],
                "url": row["url"],
            }
            for row in rows
        ]
    finally:
        await conn.close() 