import os
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

from app.core.langgraph.tools.mcp import load_researcher_tools
from app.core.prompts import RESEARCHER_PROMPT
from app.schemas.graph import ResearchAgentState


async def executor(state: ResearchAgentState):
    model_name = os.getenv("REASON_MODEL_NAME")
    search_platform = os.getenv("SEARCH_PLATFORM", "exa")
    tools = await load_researcher_tools(search_platform=search_platform)
    llm = init_chat_model(model=model_name, temperature=0.5).bind_tools(tools)

    prompt = ChatPromptTemplate(
        [
            ("system", RESEARCHER_PROMPT),
            ("human", "{task}"),
            ("placeholder", "{messages}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke(state)

    return {"messages": response}
