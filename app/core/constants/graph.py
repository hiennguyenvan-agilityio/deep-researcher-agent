from app.schemas.graph import AgentState

initial_state: AgentState = {
    "query": None,  # Explicitly clear previous query state
    "todos": [],  # Reset task list
    "loop_count": 0,  # Reset loop limit counter
    "orchestrator_messages": [],
}
