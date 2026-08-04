from app.schemas.graph import AgentState

initial_state: AgentState = {
    "todos": [],  # Reset task list
    "loop_count": 0,  # Reset loop limit counter
    "orchestrator_messages": [],
}
