import asyncio
from db import create_table

if __name__ == "__main__":
    asyncio.run(create_table())
    print("Database initialized and table created (if not exists).") 