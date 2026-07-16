import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import load_env_file
from app.api.v1.main import api_router

##############
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent
from fastapi.concurrency import asynccontextmanager
from langgraph.checkpoint.memory import MemorySaver

from app.core.langgraph.graph import get_graph

chat_model_name = os.getenv(
    "CHAT_MODEL_NAME", "google_genai:gemini-3.1-flash-lite-preview"
)
reason_model_name = os.getenv(
    "REASON_MODEL_NAME", "google_genai:gemini-3.1-flash-lite-preview"
)

checkpointer = MemorySaver()


@asynccontextmanager
async def lifespan(app: FastAPI):
    graph = await get_graph(
        chat_model_name=chat_model_name,
        reason_model_name=reason_model_name,
        checkpointer=checkpointer,
    )

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


##############

load_env_file()

# app = FastAPI()
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
