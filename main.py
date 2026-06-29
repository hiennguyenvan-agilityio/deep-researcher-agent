import os
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

from agents.deep_researcher.main import get_deep_researcher_agent
from utils.langfuse import get_instance

load_dotenv()

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Chat-Session-Id"],
)

chat_model_name = os.getenv(
    "CHAT_MODEL_NAME", "google_genai:gemini-3.1-flash-lite-preview"
)
reason_model_name = os.getenv(
    "REASON_MODEL_NAME", "google_genai:gemini-3.1-flash-lite-preview"
)

checkpointer = MemorySaver()

chatbot_agent = get_deep_researcher_agent(
    chat_model_name=chat_model_name,
    reason_model_name=reason_model_name,
    checkpointer=checkpointer,
)

langfuse_handler = get_instance()


async def stream_from_agent(query: str, chat_session_id: str):
    config = {
        "callbacks": [langfuse_handler],
        "configurable": {"thread_id": chat_session_id},
    }

    async for event in chatbot_agent.astream(
        {"messages": [{"role": "user", "content": query}]},
        stream_mode="messages",
        version="v2",
        config=config,
        subgraphs=True,
    ):
        message, metadata = event["data"]

        if metadata["langgraph_node"] != "synthesizer":
            continue

        yield message.content


@app.get("/")
def index():
    return {"message": "Welcome to the chat API"}


@app.get("/chat")
async def chat(q: str | None = None, chat_session_id: str | None = None):
    if q is None:
        return {"error": "No query provided"}

    chat_session_id = chat_session_id or str(uuid.uuid4())

    return StreamingResponse(
        stream_from_agent(q, chat_session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Chat-Session-Id": chat_session_id,
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
