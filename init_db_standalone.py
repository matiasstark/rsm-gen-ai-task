import asyncio
import asyncpg
import os

# Database configuration
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

async def get_connection():
    return await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )

async def init_database():
    """Initialize the database by creating the rag_chunks table."""
    print("Initializing database...")
    
    try:
        # Test connection first
        conn = await get_connection()
        await conn.close()
        print("Database connection successful")
        
        # Create the table
        conn = await get_connection()
        try:
            await conn.execute(CREATE_TABLE_SQL)
            print("Database table created successfully")
        finally:
            await conn.close()
        
        # Verify table exists
        conn = await get_connection()
        try:
            result = await conn.fetchval("SELECT COUNT(*) FROM rag_chunks")
            print(f"Table verification successful. Current row count: {result}")
        finally:
            await conn.close()
            
        print("Database initialization completed successfully!")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(init_database())
    if not success:
        exit(1) 