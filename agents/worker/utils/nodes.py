from langchain_core.prompts import ChatPromptTemplate

from agents.worker.prompt import WORKER_PROMPT
from agents.worker.utils.states import SearchAgentState
from agents.worker.utils.tools import search_tool
from resources.models import get_chat_model


def executor(state: SearchAgentState):
    llm = get_chat_model().bind_tools([search_tool])

    prompt = ChatPromptTemplate(
        [("human", WORKER_PROMPT), ("placeholder", "{messages}")]
    )

    chain = prompt | llm
    response = chain.invoke(state)

    return {"messages": response}
