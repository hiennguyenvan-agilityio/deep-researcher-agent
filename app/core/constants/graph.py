from app.schemas.graph import AgentState

INITIAL_STATE: AgentState = {
    "todos": [],  # Reset task list
    "loop_count": 0,  # Reset loop limit counter
    "orchestrator_messages": [],
}
