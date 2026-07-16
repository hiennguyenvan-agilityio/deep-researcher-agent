import asyncio
import os

from dotenv import load_dotenv

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

load_dotenv()

DB_URI = (
    f"postgresql://"
    f"{os.getenv('CHECKPOINTER_DB_USER')}:"
    f"{os.getenv('CHECKPOINTER_DB_PASSWORD')}@"
    f"{os.getenv('CHECKPOINTER_DB_HOST')}:"
    f"{os.getenv('CHECKPOINTER_DB_PORT')}/"
    f"{os.getenv('CHECKPOINTER_DB_NAME')}"
)


async def main():
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()


if __name__ == "__main__":
    print("DB_URI", DB_URI)
    asyncio.run(main())
