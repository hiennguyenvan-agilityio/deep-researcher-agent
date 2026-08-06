import logging

from ag_ui.core.events import RunErrorEvent
from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from copilotkit import LangGraphAGUIAgent
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import StreamingResponse

from app.core.services.auth import get_user
from app.core.services.langfuse import get_instance


logger = logging.getLogger(__name__)

_agent = None

router = APIRouter()


@router.post("/deep_researcher")
async def deep_researcher_endpoint(input_data: RunAgentInput, request: Request):
    global _agent

    token = input_data.forwarded_props.get("Authorization")

    if _agent is None:
        _agent = LangGraphAGUIAgent(
            name="deep_researcher",
            description="Deep researcher agent.",
            graph=request.app.state.graph,
        )

    user = await get_user(token)
    langfuse_handler = get_instance()
    # Clone so each request gets isolated state (see LangGraphAgent.clone).
    request_agent = _agent.clone()
    request_agent.config = {
        **request_agent.config,
        "configurable": {
            **request_agent.config.get("configurable", {}),
            "user": user,
        },
        "callbacks": request_agent.config.get("callbacks", []) + [langfuse_handler],
    }

    encoder = EventEncoder(accept=request.headers.get("accept"))

    async def event_generator():
        try:
            async for event in request_agent.run(input_data):
                yield encoder.encode(event)
        except Exception:
            logger.exception("Graph run failed for thread %s", input_data.thread_id)
            yield encoder.encode(
                RunErrorEvent(
                    message="Oops! Something went wrong on our side. Please try again in a moment."
                )
            )

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())


def init_copilotkit(app: FastAPI):
    agent = LangGraphAGUIAgent(
        name="deep_researcher",
        description="Deep researcher agent.",
        graph=app.state.graph,
    )

    @router.post("/copilotkit/agent/deep_researcher")
    async def deep_researcher_endpoint(input_data: RunAgentInput, request: Request):
        token = input_data.forwarded_props.get("Authorization")

        user = await get_user(token)
        # Clone so each request gets isolated state (see LangGraphAgent.clone).
        request_agent = agent.clone()
        request_agent.config = {
            **request_agent.config,
            "configurable": {
                **request_agent.config.get("configurable", {}),
                "user": user,
            },
        }

        encoder = EventEncoder(accept=request.headers.get("accept"))

        async def event_generator():
            try:
                async for event in request_agent.run(input_data):
                    yield encoder.encode(event)
            except Exception:
                logger.exception("Graph run failed for thread %s", input_data.thread_id)
                yield encoder.encode(
                    RunErrorEvent(
                        message="Sorry, something went wrong on our end. Please try again in a moment."
                    )
                )

        return StreamingResponse(
            event_generator(), media_type=encoder.get_content_type()
        )
