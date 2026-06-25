from langchain.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.graph import MessagesState

from agents.deep_researcher.prompts import GATEKEEPER_PROMPT
from agents.deep_researcher.utils.states import GuardState
from agents.deep_researcher.utils.structuted_outputs import GatekeeperOutput
from resources.models import get_reason_model
from resources.vitual_file_system import get_vfs
from utils.common import get_text_from_llm_response
from agents.researcher.main import researcher_agent


def gatekeeper(state: MessagesState) -> GuardState:
    """Perform safety/clarity/enhancement check and return structured decision."""

    llm = get_reason_model().with_structured_output(GatekeeperOutput)

    prompt = ChatPromptTemplate(
        [
            ("system", GATEKEEPER_PROMPT),
            ("placeholder", "{messages}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke(state)

    action = response.get("action")

    if action == "proceed":
        query = response.get("query")

        return {"query": query, "action": action}

    message = response.get("message")

    return {"messages": AIMessage(content=message), "action": action}


def researcher(state: GuardState, config: RunnableConfig):
    response = researcher_agent.invoke({"query": state["query"]})

    ai_response_text = get_text_from_llm_response(response["messages"][-1])

    vfs = get_vfs()
    thread_id = config["configurable"]["thread_id"]
    vfs.writetext(f"research_result_{thread_id}.txt", ai_response_text)

    return
