import os
import pathlib

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from ragas import Dataset, experiment

from agents.researcher.prompts import PLANNER_PROMPT

load_dotenv()


@experiment(name_prefix="planner")
async def run_experiment(row):
    query = row["query"]
    model_name = os.getenv("REASON_MODEL_NAME")
    llm = init_chat_model(model=model_name)

    prompt = ChatPromptTemplate(
        [
            ("system", PLANNER_PROMPT),
            ("human", "{query}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke({"query": query})
    prediction = response.content

    return {
        "query": query,
        "prediction": prediction,
    }


async def main():
    current_file_folder = pathlib.Path(__file__).parent.resolve()

    dataset = Dataset.load(
        name="planner",
        backend="local/csv",
        root_dir=current_file_folder,
    )
    experiment_result = await run_experiment.arun(dataset)
    print("Experiment_result: ", experiment_result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
