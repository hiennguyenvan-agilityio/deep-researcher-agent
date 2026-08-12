from pathlib import Path

from llm_guard import scan_prompt
from llm_guard.input_scanners import InvisibleText, PromptInjection, Toxicity

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "app" / "core" / "prompts"

# Same scanner set gatekeeper() runs against user input (nodes.py) — applied
# here to our own authored prompts as a sanity check.
SCANNERS = [
    PromptInjection(),
    Toxicity(),
    InvisibleText(),
]


def test_prompts_pass_llm_guard():
    prompt_files = sorted(PROMPTS_DIR.glob("*.md"))
    assert prompt_files, f"No prompt files found in {PROMPTS_DIR}"

    failures = []

    for path in prompt_files:
        text = path.read_text(encoding="utf-8")
        _, results_valid, _ = scan_prompt(SCANNERS, text)

        failed_scanners = [name for name, ok in results_valid.items() if not ok]
        if failed_scanners:
            failures.append(f"{path.name}: failed {failed_scanners}")

    assert not failures, "Prompt files flagged by llm-guard:\n" + "\n".join(failures)


if __name__ == "__main__":
    test_prompts_pass_llm_guard()
    print(f"All prompts in {PROMPTS_DIR} passed llm-guard scanners.")
