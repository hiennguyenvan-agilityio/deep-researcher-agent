import os
import pathlib
import asyncio

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from ragas import Dataset, experiment
from ragas.metrics import MetricResult, discrete_metric

from agents.deep_researcher.prompts import GATEKEEPER_PROMPT
from agents.deep_researcher.utils.structuted_outputs import GatekeeperOutput

load_dotenv()

experiment_concurrency = int(os.getenv("EVAL_EXPERIMENT_CONCURRENCY", 10))
_semaphore = asyncio.Semaphore(experiment_concurrency)


@discrete_metric(name="action", allowed_values=["pass", "fail"])
def action_correct(prediction: str, actual: str):
    """Make action accuracy of the prediction."""
    return (
        MetricResult(value="pass", reason="")
        if prediction == actual
        else MetricResult(value="fail", reason="")
    )


@experiment(name_prefix="gatekeeper")
async def run_experiment(row):
    async with _semaphore:
        question = row["query"]
        expecting_action = row["action"]
        model_name = os.getenv("REASON_MODEL_NAME")
        llm = init_chat_model(model=model_name).with_structured_output(GatekeeperOutput)

        prompt = ChatPromptTemplate(
            [
                ("system", GATEKEEPER_PROMPT),
                ("placeholder", "{messages}"),
            ]
        )

        chain = prompt | llm
        response = await chain.ainvoke(
            {"messages": [{"role": "user", "content": question}]}
        )
        action = response["action"]
        feedback = response.get("message")
        refined_query = response.get("query")

        score = action_correct.score(prediction=expecting_action, actual=action)

        return {
            "question": question,
            "expect_action": expecting_action,
            "actual_action": action,
            "action_correct": score.value,
            "reason": feedback,
            "refined_query": refined_query,
        }


async def main():
    current_file_folder = pathlib.Path(__file__).parent.resolve()

    dataset = Dataset.load(
        name="gatekeeper_queries",
        backend="local/csv",
        root_dir=current_file_folder,
    )
    experiment_result = await run_experiment.arun(dataset)
    print("Experiment_result: ", experiment_result)


if __name__ == "__main__":
    asyncio.run(main())
