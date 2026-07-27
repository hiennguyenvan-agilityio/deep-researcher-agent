from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import load_env_file
from app.api.v1.main import api_router
from app.core.langgraph.graph import get_graph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.api.copilotkit.main import init_copilotkit


load_env_file()


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
        app.state.graph = await get_graph(checkpointer=checkpointer)

        init_copilotkit(app)

        yield


app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Chat-Session-Id"],
)

api_v1_str = os.getenv("API_V1_STR", "/api/v1")

app.include_router(api_router, prefix=api_v1_str, tags=["v1"])
