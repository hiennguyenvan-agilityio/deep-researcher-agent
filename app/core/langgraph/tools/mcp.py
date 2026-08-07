import asyncio
import hashlib
import os
import ssl
from typing import Literal
from dotenv import load_dotenv

import httpx
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

SearchPlatform = Literal["tavily", "exa", "duckduckgo"]

_tool_cache: dict[SearchPlatform, list] = {}
_tool_cache_lock = asyncio.Lock()

MCP_SEARCH_CERT_SHA256 = os.environ["MCP_SEARCH_CERT_SHA256"].lower()

# Unset/empty for a hosted server with a CA-signed cert: falls back to the
# system trust store instead of pinning a local self-signed file.
MCP_SEARCH_CERT_PATH = os.getenv("MCP_SEARCH_CERT_PATH") or None


def _mcp_token() -> str:
    return os.environ["MCP_AUTH_TOKEN"]


class PinnedFingerprintTransport(httpx.AsyncHTTPTransport):
    """Rejects the connection unless the server's leaf certificate matches
    expected_fingerprint (ASI04 supply chain protection — see docs/mcp-security.md).

    The TLS handshake itself already only trusts the cafile passed to the
    factory that builds this transport, so this check is defense-in-depth:
    it fails loudly and explicitly instead of relying solely on the
    handshake having silently done the right thing.
    """

    def __init__(self, expected_fingerprint: str, **kwargs):
        super().__init__(**kwargs)
        self._expected_fingerprint = expected_fingerprint.lower()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        response = await super().handle_async_request(request)

        ssl_object = response.extensions["network_stream"].get_extra_info("ssl_object")
        actual_fp = hashlib.sha256(ssl_object.getpeercert(binary_form=True)).hexdigest()

        if actual_fp != self._expected_fingerprint:
            raise ConnectionError(
                f"MCP certificate fingerprint mismatch. "
                f"Expected: {self._expected_fingerprint}, got: {actual_fp}. Possible MITM."
            )

        return response


def make_pinned_httpx_client_factory(cafile: str | None, cert_sha256: str):
    """Build an httpx_client_factory pinned to one server's cert/fingerprint.

    cafile pins the TLS handshake to one exact self-signed cert — pass None
    for a hosted server with a CA-signed cert, where the system trust store
    already validates the chain and there's no single file to pin. The
    fingerprint check still runs either way, as defense-in-depth.

    Each MCP server connection needs its own cafile + fingerprint pair, so
    this returns a closure rather than taking them as extra args directly —
    langchain_mcp_adapters calls the factory with exactly
    (headers, timeout, auth), it can't pass per-server config through.
    """

    def factory(
        headers: dict[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        auth: httpx.Auth | None = None,
    ) -> httpx.AsyncClient:
        ssl_context = ssl.create_default_context(cafile=cafile)

        return httpx.AsyncClient(
            headers=headers,
            timeout=timeout,
            auth=auth,
            transport=PinnedFingerprintTransport(
                expected_fingerprint=cert_sha256, verify=ssl_context
            ),
        )

    return factory


client = MultiServerMCPClient(
    {
        "mySearchServer": {
            "transport": "http",
            "url": os.getenv("MCP_SERVER_URL"),
            "headers": {"Authorization": f"Bearer {_mcp_token()}"},
            "httpx_client_factory": make_pinned_httpx_client_factory(
                MCP_SEARCH_CERT_PATH, MCP_SEARCH_CERT_SHA256
            ),
        }
    }
)


def get_tool_tags(tool) -> list[str]:
    return (tool.metadata or {}).get("_meta", {}).get("fastmcp", {}).get("tags", [])


async def load_researcher_tools(
    search_platform: SearchPlatform = "exa",
    force: bool = False,
):
    if not force and (cached := _tool_cache.get(search_platform)):
        return cached

    async with _tool_cache_lock:
        # Re-check: a concurrent Send-dispatched searcher may have
        # populated the cache while we were waiting on the lock.
        if not force and (cached := _tool_cache.get(search_platform)):
            return cached

        filtered_tools = [
            tool
            for tool in await client.get_tools()
            if search_platform in get_tool_tags(tool)
        ]

        _tool_cache[search_platform] = filtered_tools

        return filtered_tools
