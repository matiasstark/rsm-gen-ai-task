import asyncio
from rag_microservice.db import get_connection

async def count_rows():
    conn = await get_connection()
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM rag_chunks;")
        print(f"rag_chunks table contains {count} rows.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(count_rows()) 