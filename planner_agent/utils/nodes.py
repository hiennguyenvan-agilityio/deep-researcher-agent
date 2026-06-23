from langchain_core.prompts import ChatPromptTemplate

from planner_agent.prompts import PLANNER_PROMPT
from planner_agent.utils.states import PlannerAgentState
from resources.models import get_reason_model
from tools.todo import write_todos


def make_plan_node(state: PlannerAgentState):
    """Orchestrator that generates a plan for the researcher"""

    planner = get_reason_model().bind_tools([write_todos])

    prompt = ChatPromptTemplate([
        ("system", PLANNER_PROMPT),
        ("human", "{query}"),
    ])

    chain = prompt | planner
    response = chain.invoke(state)

    return {"messages": response}