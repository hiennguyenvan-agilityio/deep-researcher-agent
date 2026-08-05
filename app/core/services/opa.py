import os
import httpx


OPA_URL = os.environ.get("OPA_URL", "http://127.0.0.1:8181/v1/data")


async def opa_check(policy_path: str, input: dict, default=None) -> tuple[bool, dict]:
    """Evaluate an OPA policy and return the allow decision with its result data.

    Args:
        policy_path: OPA policy path, appended to OPA_URL.
        input: Input document sent to OPA under the "input" key.
        default: Fallback result used on request failure or when "allow" is
            missing from the response.

    Returns:
        Tuple of (allow, result) where allow is the resolved permission and
        result is the raw OPA response data (or default on failure).
    """
    defaultPermission = (default or {}).get("allow", False)

    try:
        async with httpx.AsyncClient(timeout=2) as client:
            r = await client.post(f"{OPA_URL}/{policy_path}", json={"input": input})
            r.raise_for_status()

            res = r.json().get("result", {}) or default

            return res.get("allow", defaultPermission), res
    except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError):
        return defaultPermission, default
