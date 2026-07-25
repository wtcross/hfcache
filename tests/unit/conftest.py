"""Fixtures that need real machinery rather than a stand-in.

The TLS server here exists so `hfcache.hub.verify_tls` can be tested doing what
it actually does — a handshake with certificate verification — without the unit
suite touching the network. Only the trust anchor is injected; the code under
test still verifies.
"""

import shutil
import socket
import ssl
import subprocess
import threading
from pathlib import Path  # noqa: TC003 - `_certificate` takes and returns one at run time

import pytest


def _certificate(directory: Path) -> tuple[Path, Path]:
    """Mint a self-signed certificate for `localhost`, valid for a day."""
    openssl = shutil.which("openssl")
    if openssl is None:  # pragma: no cover - openssl is present on every target host
        pytest.skip("openssl is not on PATH")
    key = directory / "key.pem"
    certificate = directory / "cert.pem"
    subprocess.run(
        [
            openssl,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-keyout",
            str(key),
            "-out",
            str(certificate),
            "-days",
            "1",
            "-nodes",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost",
        ],
        check=True,
        capture_output=True,
        timeout=60,
    )
    return key, certificate


@pytest.fixture(scope="session")
def tls_server(tmp_path_factory: pytest.TempPathFactory):
    """A local TLS listener, its port, and a context that trusts it.

    Session-scoped because minting a key is the slow part and the server holds no
    per-test state: it completes one handshake and closes.
    """
    directory = tmp_path_factory.mktemp("tls")
    key, certificate = _certificate(directory)

    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(certfile=certificate, keyfile=key)

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(8)
    port = listener.getsockname()[1]

    def serve() -> None:
        while True:
            try:
                raw, _ = listener.accept()
            except OSError:
                return
            try:
                with server_context.wrap_socket(raw, server_side=True):
                    pass
            except OSError, ssl.SSLError:
                # A client that refused our certificate is a case under test.
                raw.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()

    trust = ssl.create_default_context(cafile=str(certificate))
    yield certificate, port, trust

    listener.close()
