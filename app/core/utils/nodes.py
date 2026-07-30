from langchain_core.runnables import RunnableConfig


def get_node_config(
    config: RunnableConfig, emit_messages: bool, emit_tool_calls: bool
) -> RunnableConfig:
    metadata = config.get("metadata") or {}

    return {
        **config,
        "metadata": {
            **metadata,
            "emit-messages": emit_messages,
            "emit-tool-calls": emit_tool_calls,
            "copilotkit:emit-messages": emit_messages,
            "copilotkit:emit-tool-calls": emit_tool_calls,
        },
    }
