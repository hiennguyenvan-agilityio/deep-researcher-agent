from pathlib import Path

current_file_folder = Path(__file__).parent.resolve()

GATEKEEPER_PROMPT = Path(f"{current_file_folder}/gatekeeper.md").read_text(
    encoding="utf-8"
)

PLANNER_PROMPT = Path(f"{current_file_folder}/planner.md").read_text(encoding="utf-8")

RESEARCHER_PROMPT = Path(f"{current_file_folder}/research.md").read_text(
    encoding="utf-8"
)

SYNTHESIS_PROMPT = Path(f"{current_file_folder}/systhesis.md").read_text(
    encoding="utf-8"
)
