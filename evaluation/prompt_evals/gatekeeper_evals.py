import os
import pathlib

from dotenv import load_dotenv
from langchain_classic.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from ragas import Dataset, experiment

from agents.deep_researcher.prompts import GATEKEEPER_PROMPT


load_dotenv()

@experiment(name_prefix="gatekeeper")
async def run_experiment(row):
    question = row["question"]
    model_name = os.getenv("REASON_MODEL_NAME")
    llm = init_chat_model(model=model_name)

    prompt = ChatPromptTemplate(
        [
            ("system", GATEKEEPER_PROMPT),
            ("placeholder", "{messages}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke({"messages": [{"role": "user", "content": question}]})
    action = response["action"]

    return {
        "question": question,
        "action": action,
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