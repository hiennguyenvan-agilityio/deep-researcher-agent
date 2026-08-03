import os
import aioboto3
from typing import Literal

REGION = os.environ.get("AWS_REGION", "us-east-1")

aws_session = aioboto3.Session()


async def apply_guardrail(
    text: str, source: Literal["INPUT", "OUTPUT"], grounding_source: str | None = None
):
    """
    Apply guardrail to the given text using AWS Bedrock.

    Args:
        text (str): The input text to be checked.
        source (str): The source of the input text.
        grounding_source (str | None): Optional grounding source for the guardrail.

    Returns:
        bool: True if the guardrail intervened, False otherwise.
    """

    content = [{"text": {"text": text[:10_000]}}]
    GID = os.environ.get("BEDROCK_GUARDRAIL_ID")
    GVER = os.environ.get("BEDROCK_GUARDRAIL_VERSION")

    if grounding_source:
        content.append(
            {
                "text": {
                    "text": grounding_source[:10_000],
                    "qualifiers": ["grounding_source"],
                }
            }
        )

    async with aws_session.client(
        "bedrock-runtime", region_name=REGION
    ) as bedrock_client:
        response = await bedrock_client.apply_guardrail(
            guardrailIdentifier=GID,
            guardrailVersion=GVER,
            source=source,
            content=content,
        )

        return response["action"] == "GUARDRAIL_INTERVENED"
