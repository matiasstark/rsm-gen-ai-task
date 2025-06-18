import asyncio
import asyncpg
from db import get_connection

async def check_table():
    conn = await get_connection()
    try:
        # Check if table exists
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'rag_chunks'
            );
        """)
        if result:
            print("Table 'rag_chunks' exists.")
            # Print columns
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'rag_chunks';
            """)
            print("Columns:")
            for col in columns:
                print(f"  {col['column_name']}: {col['data_type']}")
        else:
            print("Table 'rag_chunks' does NOT exist.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_table()) 