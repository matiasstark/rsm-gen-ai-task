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
    embedding VECTOR({VECTOR_DIM})
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

async def insert_chunk(document_name: str, page: int, chunk_text: str, embedding: List[float]) -> None:
    conn = await get_connection()
    try:
        await conn.execute(
            """
            INSERT INTO rag_chunks (document_name, page, chunk_text, embedding)
            VALUES ($1, $2, $3, $4)
            """,
            document_name, page, chunk_text, str(embedding)
        )
    finally:
        await conn.close()

async def insert_chunks(chunks: List[Dict[str, Any]], document_name: str) -> None:
    conn = await get_connection()
    try:
        await conn.executemany(
            """
            INSERT INTO rag_chunks (document_name, page, chunk_text, embedding)
            VALUES ($1, $2, $3, $4)
            """,
            [
                (
                    document_name,
                    chunk["page"],
                    chunk["text"],
                    str(chunk["embedding"]),
                )
                for chunk in chunks
            ]
        )
    finally:
        await conn.close()

async def similarity_search(query_embedding: List[float], document_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
    conn = await get_connection()
    try:
        rows = await conn.fetch(
            f"""
            SELECT id, page, chunk_text, embedding, embedding <-> $1 AS distance
            FROM rag_chunks
            WHERE document_name = $2
            ORDER BY embedding <-> $1
            LIMIT {top_k}
            """,
            str(query_embedding),
            document_name,
        )
        return [
            {
                "id": row["id"],
                "page": row["page"],
                "text": row["chunk_text"],
                "distance": row["distance"],
            }
            for row in rows
        ]
    finally:
        await conn.close() 