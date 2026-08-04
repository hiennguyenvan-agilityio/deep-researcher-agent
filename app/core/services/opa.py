import os
import httpx


OPA_URL = os.environ.get("OPA_URL", "http://127.0.0.1:8181/v1/data")


async def get_opa_data(policy_path: str, input: dict, default=None):
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            r = await client.post(f"{OPA_URL}/{policy_path}", json={"input": input})
            r.raise_for_status()

            res = r.json().get("result", {})

            return res
    except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError):
        return default


async def opa_check(policy_path: str, input: dict):
    res = await get_opa_data(policy_path, input, {})

    return res.get("allow", False)
