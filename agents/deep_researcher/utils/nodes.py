from langchain.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import MessagesState

from agents.deep_researcher.prompts import GATEKEEPER_PROMPT
from agents.deep_researcher.utils.states import GuardState
from agents.deep_researcher.utils.structuted_outputs import GatekeeperOutput
from resources.models import get_reason_model
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


def researcher(state: GuardState):
    response = researcher_agent.invoke({"query": state["query"]})

    message = response["messages"][-1]

    return {"messages": message}
