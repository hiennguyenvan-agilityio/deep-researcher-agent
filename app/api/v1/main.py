from fastapi import APIRouter

# from app.api.v1.chatbot import router as chatbot_router
from app.api.v1.copilotkit import agent_router

api_router = APIRouter()
# api_router.include_router(chatbot_router, prefix="/chatbot")
api_router.include_router(agent_router, prefix="/copilotkit/agent")
