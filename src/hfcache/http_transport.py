"""Verified, bounded HTTPX construction for later API clients (decision 112).

This primitive performs no API request. It rejects ambient proxies/credentials
and redirects by construction; API-011 supplies endpoint and response policy.
"""

import ssl
from typing import TYPE_CHECKING

import httpx

from hfcache.unix_http import UnixHTTPTransport

if TYPE_CHECKING:
    from pathlib import Path


def create_http_client(
    *, unix_socket: Path | None = None, ca_file: Path | None = None
) -> httpx.Client:
    """Construct an explicitly verified client; callers own closing its resources."""
    context = ssl.create_default_context(cafile=ca_file)
    limits = httpx.Limits(max_connections=8, max_keepalive_connections=4)
    transport = (
        UnixHTTPTransport(unix_socket, limits=limits)
        if unix_socket is not None
        else httpx.HTTPTransport(
            verify=context,
            trust_env=False,
            retries=0,
            limits=limits,
        )
    )
    return httpx.Client(
        transport=transport,
        verify=context,
        trust_env=False,
        follow_redirects=False,
        timeout=httpx.Timeout(connect=5, read=30, write=30, pool=5),
        limits=limits,
    )
