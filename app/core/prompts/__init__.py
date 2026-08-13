from pathlib import Path

current_file_folder = Path(__file__).parent.resolve()

REFUSE_PROMPT = Path(f"{current_file_folder}/refuse.md").read_text(encoding="utf-8")
REQUEST_TOO_LONG_SUB_PROMPT = Path(
    f"{current_file_folder}/request_too_long.md"
).read_text(encoding="utf-8")

ORCHESTRATOR_PROMPT = Path(f"{current_file_folder}/orchestrator.md").read_text(
    encoding="utf-8"
)

SEARCHER_PROMPT = Path(f"{current_file_folder}/searcher.md").read_text(encoding="utf-8")

SYNTHESIS_PROMPT = Path(f"{current_file_folder}/synthesiser.md").read_text(
    encoding="utf-8"
)
