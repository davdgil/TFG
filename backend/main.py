import asyncio
from src.config.mongo import connect_db, close_db


async def main():
    await connect_db()
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
