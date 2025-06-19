import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to Python path for Docker environment
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from db import create_table, get_connection
except ImportError:
    # Fallback for when running from different directory
    sys.path.insert(0, str(current_dir.parent))
    from rag_microservice.db import create_table, get_connection

async def init_database():
    """Initialize the database by creating the rag_chunks table."""
    print("Initializing database...")
    
    try:
        # Test connection first
        conn = await get_connection()
        await conn.close()
        print("Database connection successful")
        
        # Create the table
        await create_table()
        print("Database table created successfully")
        
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
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(init_database()) 