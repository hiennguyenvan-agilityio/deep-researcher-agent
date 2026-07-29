from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent
from fastapi import FastAPI


def init_copilotkit(app: FastAPI):
    add_langgraph_fastapi_endpoint(
        app=app,
        agent=LangGraphAGUIAgent(
            name="Deep researcher",
            description="Deep researcher agent.",
            graph=app.state.graph,
        ),
        path="/copilotkit/deep_researcher",
    )
