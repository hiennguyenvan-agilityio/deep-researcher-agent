import os

from agents.deep_researcher.main import get_deep_researcher_agent

reason_model_name = os.getenv("REASON_MODEL_NAME")
chat_model_name = os.getenv("CHAT_MODEL_NAME")

deep_researcher_agent = get_deep_researcher_agent(
    chat_model_name=chat_model_name, reason_model_name=reason_model_name
)
