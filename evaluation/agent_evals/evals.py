import os
import pathlib
import uuid

from dotenv import load_dotenv
from openai import AsyncOpenAI
from ragas import Dataset, experiment
from ragas.llms import llm_factory
from ragas.metrics.collections import AnswerAccuracy
from langgraph.checkpoint.memory import MemorySaver

from agents.deep_researcher.main import get_deep_researcher_agent
from utils.langfuse import get_instance

load_dotenv()

client = AsyncOpenAI()
llm = llm_factory("gpt-4o-mini", client=client)

answer_accuracy = AnswerAccuracy(llm=llm)

langfuse_handler = get_instance()


@experiment()
async def run_experiment(row):
    question = row["question"]
    answer = row["answer"]

    chat_model_name = os.getenv("CHAT_MODEL_NAME")
    reason_model_name = os.getenv("REASON_MODEL_NAME")

    checkpointer = MemorySaver()

    deep_researcher_agent = get_deep_researcher_agent(
        chat_model_name=chat_model_name,
        reason_model_name=reason_model_name,
        checkpointer=checkpointer,
    )

    thread_id = str(uuid.uuid4())
    config = {"callbacks": [langfuse_handler], "configurable": {"thread_id": thread_id}}

    # Get the model's prediction
    response = deep_researcher_agent.invoke(
        {"messages": [{"role": "user", "content": question}]}, config
    )
    prediction = response["messages"][-1].content

    # Calculate the correctness metric
    answer_accuracy_score = await answer_accuracy.ascore(
        user_input=question,
        response=prediction,
        reference=answer,
    )

    return {
        "question": question,
        "prediction": prediction,
        "thread_id": thread_id,
        "answer_accuracy": answer_accuracy_score.value,
    }


async def main():
    current_file_folder = pathlib.Path(__file__).parent.resolve()

    dataset = Dataset.load(
        name="three_research_queries",
        backend="local/csv",
        root_dir=current_file_folder,
    )
    experiment_result = await run_experiment.arun(dataset)
    print("Experiment_result: ", experiment_result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
