"""The directly used HTTPX factory enforces verified bounded transport defaults."""

import ssl

import httpx

from hfcache.http_transport import create_http_client


def test_httpx_factory_ignores_ambient_auth_proxies_and_never_follows_redirects(
    tmp_path, monkeypatch
):
    requests = []
    arguments = {}

    def respond(request):
        requests.append(request)
        return httpx.Response(302, headers={"location": "https://other.example.com/"})

    def transport(**kwargs):
        arguments.update(kwargs)
        return httpx.MockTransport(respond)

    monkeypatch.setenv("HTTPS_PROXY", "http://untrusted.example.com:8888")
    monkeypatch.setenv("NETRC", str(tmp_path / "ambient.netrc"))
    (tmp_path / "ambient.netrc").write_text(
        "machine archive.example.com login user password ambient-secret"
    )
    monkeypatch.setattr(httpx, "HTTPTransport", transport)
    with create_http_client(unix_socket=tmp_path / "api.sock") as client:
        assert client.get("https://archive.example.com/version").status_code == 302
        assert client.timeout.connect == 5
        assert client.timeout.pool == 5
        assert client.timeout.read == 30
        assert client.timeout.write == 30
    assert len(requests) == 1
    assert "authorization" not in requests[0].headers
    assert arguments["trust_env"] is False
    assert arguments["retries"] == 0
    assert arguments["uds"] == str(tmp_path / "api.sock")
    assert arguments["verify"].verify_mode == ssl.CERT_REQUIRED
    assert arguments["verify"].check_hostname is True
    assert arguments["limits"].max_connections == 8


def test_real_default_httpx_client_is_constructed_and_closed_without_network():
    with create_http_client() as client:
        assert client.is_closed is False
        assert client.follow_redirects is False
    assert client.is_closed is True
