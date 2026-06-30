from pathlib import Path

current_file_folder = Path(__file__).parent.resolve()

WORKER_PROMPT = Path(f"{current_file_folder}/worker.txt").read_text(encoding="utf-8")
