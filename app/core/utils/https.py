import hashlib
import ssl

import httpx


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
