from pathlib import Path

current_file_folder = Path(__file__).parent.resolve()

GATEKEEPER_PROMPT = Path(f"{current_file_folder}/gatekeeper.txt").read_text(
    encoding="utf-8"
)
