from fastapi import APIRouter

from app.api.v1.copilotkit.deep_researcher import router as deep_researcher_agent_router

agent_router = APIRouter()
agent_router.include_router(deep_researcher_agent_router)
