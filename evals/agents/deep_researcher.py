import os
import pathlib
import uuid
import asyncio

from dotenv import load_dotenv
from openai import AsyncOpenAI
from ragas import Dataset, experiment
from ragas.llms import llm_factory
from ragas.metrics.collections import AnswerAccuracy, Faithfulness
from langgraph.checkpoint.memory import MemorySaver

from app.core.langgraph.graph import get_graph
from app.core.services.file_system import get_fs
from app.core.services.langfuse import get_instance

load_dotenv()

client = AsyncOpenAI()
llm = llm_factory("gpt-4o-mini", client=client)

answer_accuracy = AnswerAccuracy(llm=llm)
faithfulness = Faithfulness(llm=llm)

langfuse_handler = get_instance()

experiment_concurrency = int(os.getenv("EVAL_EXPERIMENT_CONCURRENCY", 10))
_semaphore = asyncio.Semaphore(experiment_concurrency)


@experiment()
async def run_experiment(row):
    async with _semaphore:
        question = row["question"]
        answer = row["answer"]

        chat_model_name = os.getenv("CHAT_MODEL_NAME")
        reason_model_name = os.getenv("REASON_MODEL_NAME")

        checkpointer = MemorySaver()

        deep_researcher_agent = await get_graph(
            chat_model_name=chat_model_name,
            reason_model_name=reason_model_name,
            checkpointer=checkpointer,
        )

        thread_id = str(uuid.uuid4())
        config = {
            "callbacks": [langfuse_handler],
            "configurable": {"thread_id": thread_id},
        }

        # Get the model's prediction
        response = await deep_researcher_agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]}, config
        )
        prediction = response["messages"][-1].content

        # Calculate the correctness metric
        answer_accuracy_score = await answer_accuracy.ascore(
            user_input=question,
            response=prediction,
            reference=answer,
        )

        fs = get_fs()
        research_node_path = f"research_note_{thread_id}.txt"
        context = fs.readtext(research_node_path)

        faithfulness_score = await faithfulness.ascore(
            user_input=question,
            response=prediction,
            retrieved_contexts=[context],
        )

        return {
            "thread_id": thread_id,
            "question": question,
            "prediction": prediction,
            "answer_accuracy": answer_accuracy_score.value,
            "faithfulness": faithfulness_score.value,
            "reason": answer_accuracy_score.reason,
        }


async def main():
    current_file_folder = pathlib.Path(__file__).parent.resolve()

    dataset = Dataset.load(
        name="gaia_text_10",
        backend="local/csv",
        root_dir=current_file_folder,
    )
    experiment_result = await run_experiment.arun(dataset)
    print("Experiment_result: ", experiment_result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
