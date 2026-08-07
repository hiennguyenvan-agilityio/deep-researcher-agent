# Deep Researcher MCP Server

MCP server exposing web search tools over HTTP, built with [FastMCP](https://gofastmcp.com/). Consumed by the main deep researcher agent (`app/core/langgraph/tools/mcp.py`) via `MCP_SERVER_URL`.

## Tools

| Tool | Tag | Backend |
|---|---|---|
| `tavily_search` | `tavily` | [Tavily](https://tavily.com/) |
| `exa_search_tool` | `exa` | [Exa](https://exa.ai/) |
| `duckduckgo_search_tool` | `duckduckgo` | DuckDuckGo (no API key needed) |

Each tool takes a `query: str` and returns a JSON string: a list of `{"title", "url", "text"}` objects, 5 results max.

Tags let the calling agent filter to one search platform at a time (`load_researcher_tools(search_platform=...)` in the main app) instead of exposing all three every turn.

## Setup

Requires Python 3.13+.

1. Install dependencies:
   ```
   uv sync
   ```
2. Copy `.env.sample` to `.env` and fill in API keys:
   ```
   cp .env.sample .env
   ```
   ```
   TAVILY_API_KEY=<api_key>
   EXA_API_KEY=<api_key>
   ```
   DuckDuckGo needs no key.

## Running locally over HTTPS

Generate a self-signed cert (once):
```
openssl req -x509 -newkey rsa:4096 \
  -keyout certs/key.pem \
  -out certs/cert.pem \
  -days 365 \
  -nodes \
  -subj "/CN=localhost"
```

Get its SHA-256 fingerprint and set it as `MCP_SEARCH_CERT_SHA256` in the **main app's** `.env` — also point `MCP_SEARCH_CERT_PATH` there at this `cert.pem` (the client pins against both; see [docs/mcp-security.md](../docs/mcp-security.md)):
```
openssl x509 -in certs/cert.pem -noout -fingerprint -sha256 | cut -d= -f2 | tr -d ':' | tr 'A-F' 'a-f'
```

Run the server:
```
uvicorn main:app --port 8081 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
```

The MCP endpoint is then reachable at `https://localhost:8081/mcp`.

> Note: if the caller's `MCP_SERVER_URL` is set to `http://` instead of `https://`, requests will fail against this SSL-enabled server — keep the scheme in sync on both sides.
>
> Whenever `certs/cert.pem` is regenerated (expiry, rotation), `MCP_SEARCH_CERT_SHA256` on the client must be updated too — a stale pin fails closed (`ConnectionError`), it doesn't silently trust the new cert.
