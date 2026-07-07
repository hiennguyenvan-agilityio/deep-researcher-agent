import json
import os
from pathlib import Path
from typing import TypedDict
import asyncio

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from openai import AsyncOpenAI
from ragas import Dataset, experiment
from ragas.llms import llm_factory
from ragas.metrics.collections import ToolCallAccuracy
from ragas.messages import AIMessage, ToolCall
from ragas.metrics import MetricResult, numeric_metric

from app.core.langgraph.tools.todo import write_todos
from app.core.prompts import PLANNER_PROMPT
from app.schemas.todo import Todo

load_dotenv()


class Scores(TypedDict):
    relevance_alignment: int
    completeness_coverage: int
    clarity_actionability: int
    granularity: int
    feasibility: int
    overall: int


class Evaluation(TypedDict):
    scores: Scores
    reason: str


client = AsyncOpenAI()
llm = llm_factory("gpt-5.1", client=client)

current_file_folder = Path(__file__).parent.resolve()

QUALITY_CHECK_PROMPT = Path(
    f"{current_file_folder}/planner_quality_check_prompt.txt"
).read_text(encoding="utf-8")

experiment_concurrency = int(os.getenv("EVAL_EXPERIMENT_CONCURRENCY", 10))
_semaphore = asyncio.Semaphore(experiment_concurrency)


@numeric_metric(name="quality_check")
def quality_check(query: str, tasks: list[Todo]):
    """Check quality of tasks, which generate from planner"""

    llm = init_chat_model("gpt-5.1", temperature=0).with_structured_output(Evaluation)

    prompt = ChatPromptTemplate.from_template(QUALITY_CHECK_PROMPT)

    chain = prompt | llm
    response = chain.invoke({"query": query, "tasks": json.dumps(tasks)})
    score = response["scores"]["overall"] / 5.0

    return MetricResult(value=score, reason=response["reason"])


@experiment(name_prefix="planner")
async def run_experiment(row):
    async with _semaphore:
        query = row["query"]
        model_name = os.getenv("REASON_MODEL_NAME")
        tools = [write_todos]
        llm = init_chat_model(model=model_name).bind_tools(tools)

        prompt = ChatPromptTemplate(
            [
                ("system", PLANNER_PROMPT),
                ("human", "{query}"),
            ]
        )

        chain = prompt | llm
        response = chain.invoke({"query": query, "research_notes": None})

        # We only need to verify that the write_todos tool is called. Since ToolCall requires arguments, we ignore the actual arguments by passing the expected reference arguments.
        args = response.tool_calls[0]["args"]
        todos = args["todos"]

        reference_tool_calls = [
            ToolCall(
                name="write_todos",
                args=args,
            )
        ]

        user_input = [
            AIMessage(
                content="",
                tool_calls=[
                    ToolCall(
                        name=tc["name"],
                        args=tc["args"],
                    )
                    for tc in response.tool_calls
                ],
            ),
        ]

        tool_call_accuracy = ToolCallAccuracy()
        tool_call_accuracy_result = await tool_call_accuracy.ascore(
            user_input=user_input,
            reference_tool_calls=reference_tool_calls,
        )

        quality_check_result = await quality_check.ascore(query=query, tasks=todos)

        return {
            "query": query,
            "tool_call_accuracy": tool_call_accuracy_result.value,
            "quality": quality_check_result.value,
            "suggestions": quality_check_result.reason,
        }


async def main():
    dataset = Dataset.load(
        name="planner_queries",
        backend="local/csv",
        root_dir=current_file_folder,
    )
    experiment_result = await run_experiment.arun(dataset)
    print("Experiment_result: ", experiment_result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
