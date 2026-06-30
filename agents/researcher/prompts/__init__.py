from pathlib import Path

current_file_folder = Path(__file__).parent.resolve()

PLANNER_PROMPT = Path(f"{current_file_folder}/planner.txt").read_text(encoding="utf-8")

SYSTHESIS_PROMPT = Path(f"{current_file_folder}/systhesis.txt").read_text(
    encoding="utf-8"
)
