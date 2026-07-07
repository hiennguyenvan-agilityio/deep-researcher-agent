
## Replanning Instructions

The planning instructions are:

{planner_instruction}

The current research execution plan is:

{todos}

Additional research notes (if available):

{research_notes}

Review the planning instructions, current todo list, research notes, and the latest user request, then update the plan by calling `write_todos`.

When replanning:
- Preserve all completed tasks exactly as they are.
- Update pending tasks when additional context or clarification would make them more specific or executable.
- Remove pending tasks that are no longer relevant.
- Add any new tasks required to satisfy the updated objective.
- Preserve the execution flow of the existing plan. Do not renumber completed tasks. The `step` values of pending and newly added tasks should continue from the existing plan while respecting task dependencies and maximizing parallelism.
- Remove duplicate or overlapping tasks.
- Ensure the final todo list completely reflects the current research objective while preserving completed work.
