from typing import Literal, Optional, TypedDict, Annotated


class GatekeeperOutput(TypedDict):
    """Structured output from the gatekeeper node after safety check, clarity check, and query enhancement.

    This model captures the three possible outcomes:
    - refuse: the query is unsafe or violates policy.
    - ask_user: the query is safe but unclear; specific clarification questions are asked.
    - proceed: the query is both safe and clear; a refined, enhanced query is provided for the planner.
    """

    action: Annotated[
        Literal["refuse", "ask_user", "proceed"],
        "The decision after safety and clarity checks.",
    ]
    message: Annotated[
        Optional[str],
        "Refusal message, clarification questions or clarified query to show to the user, None if proceed.",
    ]
    query: Annotated[
        Optional[str], "If proceed, the fully clarified query to pass to planner."
    ]


class ReviewerOutput(TypedDict):
    approved: Annotated[bool, "True if the answer correctly the user's request."]
    recommend_action: Annotated[
        Optional[str],
        (
            "If approved=False, provide a clear and actionable research task "
            "describing exactly what information is missing, what claims must be "
            "verified, or what analysis must be performed. None if approved=True."
        ),
    ]
