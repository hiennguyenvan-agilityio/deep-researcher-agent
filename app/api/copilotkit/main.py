import os

from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.langgraph.graph import get_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    DB_URI = (
        f"postgresql://"
        f"{os.getenv('CHECKPOINTER_DB_USER')}:"
        f"{os.getenv('CHECKPOINTER_DB_PASSWORD')}@"
        f"{os.getenv('CHECKPOINTER_DB_HOST')}:"
        f"{os.getenv('CHECKPOINTER_DB_PORT')}/"
        f"{os.getenv('CHECKPOINTER_DB_NAME')}"
    )

    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        graph = await get_graph(checkpointer=checkpointer)

        add_langgraph_fastapi_endpoint(
            app=app,
            agent=LangGraphAGUIAgent(
                name="Deep researcher",
                description="An example agent.",
                graph=graph,
            ),
            path="/copilotkit/deep_researcher",
        )

        yield
