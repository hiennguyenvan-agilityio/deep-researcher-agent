import logging

from ag_ui.core.events import RunErrorEvent
from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from copilotkit import LangGraphAGUIAgent
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

from app.core.services.auth import get_user

logger = logging.getLogger(__name__)


def init_copilotkit(app: FastAPI):
    agent = LangGraphAGUIAgent(
        name="deep_researcher",
        description="Deep researcher agent.",
        graph=app.state.graph,
    )

    @app.post("/copilotkit/agent/deep_researcher")
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
