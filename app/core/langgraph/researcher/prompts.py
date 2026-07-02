from pathlib import Path

project_folder = Path(__file__).parent.resolve().parents[1]

WORKER_PROMPT = Path(f"{project_folder}/prompts/systhesis.md").read_text(
    encoding="utf-8"
)
