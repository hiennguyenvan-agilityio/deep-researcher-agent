import os

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

from agents.worker.prompts import WORKER_PROMPT
from agents.worker.utils.states import SearchAgentState
from agents.worker.utils.tools import exa_search_tool


def executor(state: SearchAgentState):
    model_name = os.getenv("REASON_MODEL_NAME")
    llm = init_chat_model(model=model_name, temperature=0.5).bind_tools(
        [exa_search_tool]
    )

    prompt = ChatPromptTemplate(
        [("human", WORKER_PROMPT), ("placeholder", "{messages}")],
    )

    chain = prompt | llm
    response = chain.invoke(state)

    return {"messages": response}
