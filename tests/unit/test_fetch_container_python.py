"""Decision 129: bounded explicit public fetch, authenticated publication only."""

import hashlib
import importlib.util
import io
import json
import os
import ssl
import subprocess
import sys
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/fetch-container-python.py"
URL = (
    "https://github.com/astral-sh/python-build-standalone/releases/download/20260718/"
    "cpython-3.14.6%2B20260718-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz"
)
BODY = b"synthetic archive; this helper never extracts it"


@pytest.fixture
def fetcher():
    spec = importlib.util.spec_from_file_location("fetch_python", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def manifest(tmp_path, **changes):
    fields = {"version": "3.14.6", "url": URL, "sha256": hashlib.sha256(BODY).hexdigest()}
    path = tmp_path / "images.json"
    path.write_text(json.dumps({"python_distribution": fields | changes}))
    return path


class Response:
    def __init__(self, body=BODY, headers=(), status=200):
        self.stream = io.BytesIO(body)
        self.headers = Message()
        for key, value in headers:
            self.headers[key] = value
        self.status = status
        self.closed = False

    def read1(self, size):
        return self.stream.read(size)

    def close(self):
        self.closed = True


class Opener:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = []

    def open(self, request, timeout):
        assert request.get_header("Accept-encoding") == "identity"
        assert not request.has_header("Authorization")
        self.calls.append((request.full_url, timeout))
        value = next(self.responses)
        if isinstance(value, BaseException):
            raise value
        return value


def install_response(fetcher, monkeypatch, response):
    opener = Opener(response)
    monkeypatch.setattr(fetcher, "http_opener", lambda: opener)
    return opener


def partials(tmp_path):
    return list(tmp_path.glob(".python.tar.gz.partial-*"))


def test_only_complete_matching_download_is_published_private_without_extraction(
    fetcher, monkeypatch, tmp_path
):
    source = manifest(tmp_path)
    response = Response(headers=[("Content-Length", str(len(BODY)))])
    opener = install_response(fetcher, monkeypatch, response)
    target = tmp_path / "python.tar.gz"
    result = fetcher.fetch(source, target)
    assert result == {
        "schema_version": 1,
        "python_version": "3.14.6",
        "url": URL,
        "sha256": hashlib.sha256(BODY).hexdigest(),
        "bytes": len(BODY),
        "artifact": str(target),
    }
    assert target.read_bytes() == BODY
    assert target.stat().st_mode & 0o777 == 0o600
    assert target.stat().st_nlink == 1
    assert response.closed
    assert opener.calls == [(URL, 10)]
    assert partials(tmp_path) == []
    assert sorted(path.name for path in tmp_path.iterdir()) == ["images.json", "python.tar.gz"]


@pytest.mark.parametrize(
    "changes",
    [
        {"version": True},
        {"sha256": "A" * 64},
        {"url": "http://github.com/file"},
        {"url": URL + "?token=private"},
        {"url": URL.replace("3.14.6", "3.14.7")},
        {"url": URL.replace("github.com", "github.com@attacker.invalid")},
        {"url": URL.replace("https://", " https://")},
        {"extra": "private"},
    ],
)
def test_invalid_pins_refuse_before_network_or_output(fetcher, monkeypatch, tmp_path, changes):
    source = manifest(tmp_path, **changes)
    monkeypatch.setattr(fetcher, "http_opener", lambda: pytest.fail("network before valid pins"))
    with pytest.raises(ValueError, match="pinned Python"):
        fetcher.fetch(source, tmp_path / "python.tar.gz")
    assert partials(tmp_path) == []


@pytest.mark.parametrize(
    "body",
    [
        b'{"python_distribution":{},"python_distribution":{}}',
        b"[]",
        b"[malformed",
        b" " * 65537,
    ],
)
def test_malformed_duplicate_or_oversized_metadata_refuses(fetcher, tmp_path, body):
    source = tmp_path / "images.json"
    source.write_bytes(body)
    with pytest.raises((ValueError, TypeError)):
        fetcher.distribution(source)


@pytest.mark.parametrize(
    ("path", "table"),
    [
        ("/srv/hfcache/forbidden", "1 0 0:1 / / rw - xfs /dev/a rw"),
        (
            "/mnt/alias/file",
            "1 0 0:1 / / rw - xfs /dev/a rw\n2 1 0:2 / /mnt/alias ro - nfs4 host:/a ro",
        ),
        ("/safe/file", "1 0 0:1 / / rw - autofs systemd-1 rw"),
        ("/safe/file", "malformed"),
    ],
)
def test_nonlocal_mount_guard_precedes_all_target_io(fetcher, monkeypatch, path, table):
    monkeypatch.setattr(fetcher.os, "open", lambda *_a, **_k: pytest.fail("target opened"))
    with pytest.raises(ValueError, match="pinned Python"):
        fetcher.local_path(Path(path), mountinfo=table)


def test_mount_escape_and_component_boundaries_are_recognized(fetcher):
    table = "1 0 0:1 / / rw - xfs /dev/a rw\n2 1 0:2 / /mnt/net\\040share ro - nfs4 host:/a ro"
    assert fetcher.local_path(Path("/mnt/network/file"), mountinfo=table) == Path(
        "/mnt/network/file"
    )
    with pytest.raises(ValueError, match="pinned Python"):
        fetcher.local_path(Path("/mnt/net share/file"), mountinfo=table)


def test_symlink_components_and_fifo_metadata_never_follow_or_block(fetcher, tmp_path):
    source = manifest(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(OSError, match=r"Not a directory|Too many levels"):
        fetcher.distribution(alias / source.name)
    source.unlink()
    os.mkfifo(source)
    with pytest.raises(ValueError, match="pinned Python"):
        fetcher.distribution(source)


@pytest.mark.parametrize("target_kind", ["existing", "symlink", "unsafe_parent"])
def test_existing_or_unsafe_output_is_preserved_before_network(
    fetcher, monkeypatch, tmp_path, target_kind
):
    source = manifest(tmp_path)
    target = tmp_path / "python.tar.gz"
    original = tmp_path / "evidence"
    original.write_bytes(b"preserve")
    if target_kind == "existing":
        target.write_bytes(b"preserve")
    elif target_kind == "symlink":
        target.symlink_to(original)
    else:
        tmp_path.chmod(0o777)
    monkeypatch.setattr(fetcher, "http_opener", lambda: pytest.fail("unexpected network"))
    try:
        with pytest.raises(ValueError, match="pinned Python"):
            fetcher.fetch(source, target)
    finally:
        tmp_path.chmod(0o700)
    assert original.read_bytes() == b"preserve"
    assert partials(tmp_path) == []


@pytest.mark.parametrize(
    ("headers", "body"),
    [
        ([("Content-Encoding", "gzip")], BODY),
        ([("Content-Length", "1"), ("Content-Length", "1")], BODY),
        ([("Content-Length", "9" * 5000)], BODY),
        ([("Content-Length", str(len(BODY) + 1))], BODY),
        ([("Transfer-Encoding", "gzip")], BODY),
        ([("Transfer-Encoding", "chunked"), ("Content-Length", "1")], BODY),
        ([], b"wrong digest"),
    ],
)
def test_hostile_or_incomplete_payload_retains_partial_and_never_publishes(
    fetcher, monkeypatch, tmp_path, headers, body
):
    source = manifest(tmp_path)
    response = Response(body, headers)
    install_response(fetcher, monkeypatch, response)
    with pytest.raises(ValueError, match="pinned Python"):
        fetcher.fetch(source, tmp_path / "python.tar.gz")
    assert not (tmp_path / "python.tar.gz").exists()
    assert len(partials(tmp_path)) == 1
    assert response.closed


def test_actual_stream_byte_cap_is_independent_of_declared_length(fetcher, monkeypatch, tmp_path):
    source = manifest(tmp_path)
    monkeypatch.setattr(fetcher, "_ARCHIVE_BYTES", len(BODY) - 1)
    install_response(fetcher, monkeypatch, Response())
    with pytest.raises(ValueError, match="pinned Python"):
        fetcher.fetch(source, tmp_path / "python.tar.gz")
    assert not (tmp_path / "python.tar.gz").exists()
    assert partials(tmp_path)[0].read_bytes() == b""


class UnreadableRedirect(io.BytesIO):
    def read(self, *_args):
        pytest.fail("redirect/error body must never be drained")


def redirect(
    url=URL, target="https://release-assets.githubusercontent.com/public?signature=opaque"
):
    headers = Message()
    headers["Location"] = target
    body = UnreadableRedirect(b"untrusted redirect body")
    return HTTPError(url, 302, "private server message", headers, body), body


def test_redirect_is_closed_without_draining_or_retaining_signed_url(fetcher):
    response, body = redirect()
    final = Response()
    opener = Opener(response, final)
    assert fetcher.open_response(opener, URL, float("inf")) is final
    assert body.closed
    assert len(opener.calls) == 2
    assert fetcher.NoRedirect().redirect_request() is None


@pytest.mark.parametrize(
    "target",
    [
        "http://github.com/public",
        "https://attacker.invalid/public",
        "file:///private",
        "https://github.com:443/public",
        "https://user:secret@github.com/public",
        "https://github.com/public#fragment",
        "https://github.com/\nprivate",
    ],
)
def test_unsafe_redirect_never_makes_a_second_request(fetcher, target):
    response, body = redirect(target=target)
    opener = Opener(response)
    with pytest.raises(ValueError, match="pinned Python"):
        fetcher.open_response(opener, URL, float("inf"))
    assert body.closed
    assert len(opener.calls) == 1


def test_redirect_budget_is_total_and_error_bodies_are_never_consumed(fetcher):
    responses = [redirect()[0] for _ in range(6)]
    opener = Opener(*responses)
    with pytest.raises(ValueError, match="pinned Python"):
        fetcher.open_response(opener, URL, float("inf"))
    assert len(opener.calls) == 6
    assert all(item.closed for item in responses)


def test_explicit_tls_proxy_and_auth_policy_ignores_ambient_sources(fetcher, monkeypatch):
    loaded, contexts = [], []

    class Context:
        def __init__(self, protocol):
            assert protocol == ssl.PROTOCOL_TLS_CLIENT
            contexts.append(self)

        def load_verify_locations(self, *, cafile):
            loaded.append(cafile)

    for name in (
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "ALL_PROXY",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "NETRC",
    ):
        monkeypatch.setenv(name, "/private-marker")
    monkeypatch.setattr(fetcher.ssl, "SSLContext", Context)
    monkeypatch.setattr(fetcher, "build_opener", lambda *handlers: handlers)
    handlers = fetcher.http_opener()
    assert loaded == [str(fetcher._CA_FILES[0])]
    assert handlers[0].proxies == {}
    assert handlers[1]._context is contexts[0]
    assert isinstance(handlers[2], fetcher.NoRedirect)


def test_raced_target_and_partial_replacement_are_preserved(fetcher, monkeypatch, tmp_path):
    source = manifest(tmp_path)
    install_response(fetcher, monkeypatch, Response())
    original_link = fetcher.os.link
    target = tmp_path / "python.tar.gz"

    def raced(*args, **kwargs):
        target.write_bytes(b"unexplained evidence")
        return original_link(*args, **kwargs)

    monkeypatch.setattr(fetcher.os, "link", raced)
    with pytest.raises(FileExistsError):
        fetcher.fetch(source, target)
    assert target.read_bytes() == b"unexplained evidence"
    assert partials(tmp_path)[0].read_bytes() == BODY


def test_exclusive_partial_collision_is_never_unlinked(fetcher, monkeypatch, tmp_path):
    source = manifest(tmp_path)
    monkeypatch.setattr(fetcher.secrets, "token_hex", lambda _: "fixed")
    evidence = tmp_path / ".python.tar.gz.partial-fixed"
    evidence.write_bytes(b"unknown evidence")
    with pytest.raises(FileExistsError):
        fetcher.fetch(source, tmp_path / "python.tar.gz")
    assert evidence.read_bytes() == b"unknown evidence"


def test_replaced_partial_is_preserved_and_cannot_be_published(fetcher, monkeypatch, tmp_path):
    source = manifest(tmp_path)
    install_response(fetcher, monkeypatch, Response())
    original_sync = fetcher.os.fsync
    replaced = False

    def replace_before_publish(descriptor):
        nonlocal replaced
        if not replaced:
            replaced = True
            partial = partials(tmp_path)[0]
            partial.rename(tmp_path / "retained-original")
            partial.write_bytes(b"unexplained replacement")
        original_sync(descriptor)

    monkeypatch.setattr(fetcher.os, "fsync", replace_before_publish)
    with pytest.raises(ValueError, match="pinned Python"):
        fetcher.fetch(source, tmp_path / "python.tar.gz")
    assert partials(tmp_path)[0].read_bytes() == b"unexplained replacement"
    assert (tmp_path / "retained-original").read_bytes() == BODY
    assert not (tmp_path / "python.tar.gz").exists()


def test_failure_cli_emits_no_server_input_or_success_provenance(
    fetcher, monkeypatch, tmp_path, capsys
):
    source = manifest(tmp_path)
    install_response(fetcher, monkeypatch, URLError("PRIVATE_RESPONSE_OR_TOKEN"))
    monkeypatch.setattr(
        sys,
        "argv",
        [str(SCRIPT), "--images-json", str(source), "--output", str(tmp_path / "python.tar.gz")],
    )
    assert fetcher.main() == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "PRIVATE_RESPONSE_OR_TOKEN" not in output.err
    assert len(partials(tmp_path)) == 1


def test_alarm_interrupts_blocked_exchange_preserves_partial_and_restores_state(tmp_path):
    """Only a disposable subprocess receives SIGALRM; never the pytest owner."""
    source = manifest(tmp_path)
    program = """
import importlib.util,json,signal,sys,time
from pathlib import Path
spec=importlib.util.spec_from_file_location('fetcher',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m._TOTAL_SECONDS=.05
previous=signal.getsignal(signal.SIGALRM)
class Opener:
 def open(self,*a,**kw): time.sleep(30)
m.http_opener=lambda:Opener()
started=time.monotonic()
try: m.fetch(Path(sys.argv[2]),Path(sys.argv[3]))
except ValueError: pass
else: raise AssertionError
assert time.monotonic()-started<2
assert signal.getsignal(signal.SIGALRM)==previous
assert signal.getitimer(signal.ITIMER_REAL)==(0,0)
assert not Path(sys.argv[3]).exists()
signal.setitimer(signal.ITIMER_REAL,10)
try:
 try: m.fetch(Path(sys.argv[2]),Path(sys.argv[3]))
 except ValueError: pass
 else: raise AssertionError
 assert 0<signal.getitimer(signal.ITIMER_REAL)[0]<=10
finally: signal.setitimer(signal.ITIMER_REAL,0)
print(json.dumps({'deadline':True,'preserved_alarm':True}))
"""
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            program,
            str(SCRIPT),
            str(source),
            str(tmp_path / "python.tar.gz"),
        ],
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    assert json.loads(result.stdout) == {"deadline": True, "preserved_alarm": True}
    assert len(partials(tmp_path)) == 1
