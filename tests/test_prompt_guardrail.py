import asyncio
import os
from pathlib import Path

from app.core.services.aws import apply_guardrail


PROMPTS_DIR = Path(__file__).resolve().parents[1] / "app" / "core" / "prompts"

# Same env gate nodes.py itself uses (gatekeeper()/synthesizer()) — the
# guardrail is optional infra, not every environment has AWS creds/a
# configured guardrail, so skip rather than fail when it's unset.
GUARDRAIL_CONFIGURED = bool(os.getenv("BEDROCK_GUARDRAIL_ID"))


def test_prompts_pass_bedrock_guardrail():
    if not GUARDRAIL_CONFIGURED:
        print("BEDROCK_GUARDRAIL_ID not set — skipping Bedrock guardrail check.")
        return

    prompt_files = sorted(PROMPTS_DIR.glob("*.md"))
    assert prompt_files, f"No prompt files found in {PROMPTS_DIR}"

    async def _scan_all():
        failures = []

        for path in prompt_files:
            text = path.read_text(encoding="utf-8")
            intervened = await apply_guardrail(text, "INPUT")
            if intervened:
                failures.append(path.name)

        return failures

    failures = asyncio.run(_scan_all())

    assert not failures, "Prompt files flagged by Bedrock guardrail:\n" + "\n".join(
        failures
    )


if __name__ == "__main__":
    test_prompts_pass_bedrock_guardrail()
    print(f"All prompts in {PROMPTS_DIR} passed the Bedrock guardrail check.")
