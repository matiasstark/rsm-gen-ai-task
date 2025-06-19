import asyncio
from rag_microservice.db import drop_table, reset_table, get_connection

async def test_db_operations():
    """Test the database drop and reset operations."""
    
    print("Testing database operations...")
    
    # Test drop table
    print("\n1. Testing drop_table()...")
    await drop_table()
    
    # Test reset table
    print("\n2. Testing reset_table()...")
    await reset_table()
    
    # Verify table exists by checking if we can connect and query
    print("\n3. Verifying table was created...")
    conn = await get_connection()
    try:
        result = await conn.fetchval("SELECT COUNT(*) FROM rag_chunks")
        print(f"Table exists and has {result} rows")
    finally:
        await conn.close()
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_db_operations()) 