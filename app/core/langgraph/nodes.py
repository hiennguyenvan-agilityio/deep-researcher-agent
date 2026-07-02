from langchain.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from app.core.prompts import GATEKEEPER_PROMPT
from app.core.services.llm import get_reason_model
from app.schemas.graph import AgentState, GatekeeperOutput
from app.core.langgraph.researcher.graph import researcher_agent


def gatekeeper(state: AgentState):
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


def researcher(state: AgentState):
    response = researcher_agent.invoke({"query": state["query"]})

    message = response["messages"][-1]

    return {"messages": message}
