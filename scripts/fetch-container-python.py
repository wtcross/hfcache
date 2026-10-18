#!/usr/bin/env python3
"""Explicitly fetch one pinned public interpreter, never extract it.

Only a verified archive receives the requested new filename. Failed/interrupted
partials remain local evidence. The builder independently authenticates and
extracts the archive; this host-only helper imports no application/credentials.
"""

import argparse
import hashlib
import json
import os
import re
import secrets
import signal
import ssl
import stat
import sys
import threading
import time
from contextlib import contextmanager
from http.client import HTTPException
from pathlib import Path
from typing import NoReturn
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener

_METADATA_BYTES = 65536
_MOUNT_BYTES = 8 * 1024 * 1024
_ARCHIVE_BYTES = 128 * 1024 * 1024
_CHUNK_BYTES = 65536
_TOTAL_SECONDS = 300
_SOCKET_SECONDS = 10
_REDIRECTS = 5
_URL_BYTES = 8192
_LOCAL = frozenset({"btrfs", "ext2", "ext3", "ext4", "overlay", "tmpfs", "xfs"})
_HOSTS = frozenset(
    {"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}
)
_REDIRECT_CODES = frozenset({301, 302, 303, 307, 308})
_CA_FILES = (
    Path("/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem"),
    Path("/etc/ssl/certs/ca-certificates.crt"),
)


def refuse() -> NoReturn:
    message = "pinned Python artifact fetch refused"
    raise ValueError(message)


@contextmanager
def deadline():
    """Linux CLI budget includes resolver, headers, redirects and slow framing."""
    if threading.current_thread() is not threading.main_thread():
        refuse()
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    if previous_timer != (0.0, 0.0):
        refuse()  # Never consume, extend or replace somebody else's alarm.
    previous_handler = signal.getsignal(signal.SIGALRM)

    def expired(*_):
        refuse()

    signal.signal(signal.SIGALRM, expired)
    try:
        signal.setitimer(signal.ITIMER_REAL, _TOTAL_SECONDS)
        yield time.monotonic() + _TOTAL_SECONDS
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)


def local_path(path, *, mountinfo=None):
    """Refuse network mounts before any target traversal; never resolve aliases."""
    if ".." in path.parts or any(not char.isprintable() for char in str(path)):
        refuse()
    path = Path(os.path.abspath(path))  # noqa: PTH100 - lexical; never resolve a NAS alias
    if path == Path("/srv") or Path("/srv") in path.parents or path == Path("/"):
        refuse()
    if mountinfo is None:
        with Path("/proc/self/mountinfo").open("rb") as stream:
            body = stream.read(_MOUNT_BYTES + 1)
        if len(body) > _MOUNT_BYTES:
            refuse()
        mountinfo = body.decode("utf-8", errors="strict")
    matches = []
    for line in mountinfo.splitlines():
        before, separator, after = line.partition(" - ")
        fields, tail = before.split(), after.split()
        if not separator or len(fields) < 6 or len(tail) < 3:  # noqa: PLR2004
            refuse()
        where = Path(re.sub(r"\\([0-7]{3})", lambda item: chr(int(item[1], 8)), fields[4]))
        if not where.is_absolute():
            refuse()
        if where == path or where in path.parents:
            matches.append((len(where.parts), tail[0]))
    depth = max((level for level, _ in matches), default=-1)
    if not matches or any(kind not in _LOCAL for level, kind in matches if level == depth):
        refuse()
    return path


def open_parent(path):
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parent.parts[1:]:
            following = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = following
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            refuse()
        result[key] = value
    return result


def distribution(path):
    path = local_path(path)
    parent = open_parent(path)
    try:
        descriptor = os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=parent,
        )
    finally:
        os.close(parent)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > _METADATA_BYTES:
            refuse()
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            body = stream.read(_METADATA_BYTES + 1)
        after = os.fstat(descriptor)
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if len(body) > _METADATA_BYTES or any(
            getattr(before, key) != getattr(after, key) for key in fields
        ):
            refuse()
    finally:
        os.close(descriptor)
    value = json.loads(body, object_pairs_hook=no_duplicates)["python_distribution"]
    if not isinstance(value, dict) or set(value) != {"version", "url", "sha256"}:
        refuse()
    if any(type(item) is not str for item in value.values()):
        refuse()
    version, url, expected = value["version"], value["url"], value["sha256"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) or not re.fullmatch(
        r"[0-9a-f]{64}", expected
    ):
        refuse()
    pattern = (
        r"https://github\.com/astral-sh/python-build-standalone/releases/download/"
        r"(?P<build>[0-9]{8})/cpython-"
        + re.escape(version)
        + r"%2B(?P=build)-x86_64-unknown-linux-gnu-install_only_stripped\.tar\.gz"
    )
    if not re.fullmatch(pattern, url):
        refuse()
    return version, url, expected


def url_text(url):
    if (
        len(url) > _URL_BYTES
        or any(char.isspace() or not char.isprintable() for char in url)
        or "\\" in url
    ):
        refuse()


def public_url(url):
    url_text(url)
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in _HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
        or parsed.fragment
    ):
        refuse()
    return url


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        # The default handler drains fp.read() without a bound. Follow manually.
        return None


def http_opener():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    for path in _CA_FILES:
        try:
            context.load_verify_locations(cafile=str(path))
        except FileNotFoundError:
            continue
        break
    else:
        refuse()
    return build_opener(ProxyHandler({}), HTTPSHandler(context=context), NoRedirect())


def open_response(opener, url, until):
    for redirects in range(_REDIRECTS + 1):
        if time.monotonic() >= until:
            refuse()
        request = Request(public_url(url), headers={"Accept-Encoding": "identity"})  # noqa: S310 - verified HTTPS allowlist
        try:
            response = opener.open(request, timeout=_SOCKET_SECONDS)
        except HTTPError as error:
            response = error
        if response.status == 200:  # noqa: PLR2004
            return response
        try:
            locations = response.headers.get_all("Location", [])
            if (
                response.status not in _REDIRECT_CODES
                or len(locations) != 1
                or redirects == _REDIRECTS
            ):
                refuse()
            url_text(locations[0])  # urljoin/urlsplit otherwise discard raw controls.
            url = public_url(urljoin(url, locations[0]))
        finally:
            response.close()  # Never read redirect/error bodies or log signed URLs.
    return refuse()


def content_length(response):
    encodings = response.headers.get_all("Content-Encoding", [])
    lengths = response.headers.get_all("Content-Length", [])
    transfers = response.headers.get_all("Transfer-Encoding", [])
    if (
        encodings not in ([], ["identity"])
        or len(lengths) > 1
        or transfers not in ([], ["chunked"])
    ):
        refuse()
    if transfers and lengths:
        refuse()
    if not lengths:
        return None
    value = lengths[0]
    if not value.isascii() or not value.isdecimal() or len(value) > 10:  # noqa: PLR2004
        refuse()
    size = int(value)
    if not 0 < size <= _ARCHIVE_BYTES:
        refuse()
    return size


def same_inode(left, right):
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino) and stat.S_ISREG(
        right.st_mode
    )


def download(descriptor, url, until):
    digest, size = hashlib.sha256(), 0
    response = open_response(http_opener(), url, until)
    try:
        declared = content_length(response)
        while True:
            body = response.read1(_CHUNK_BYTES)
            if time.monotonic() >= until:
                refuse()
            if not body:
                break
            size += len(body)
            if size > _ARCHIVE_BYTES:
                refuse()
            digest.update(body)
            view = memoryview(body)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    refuse()
                view = view[written:]
    finally:
        response.close()
    if declared is not None and size != declared:
        refuse()
    return digest.hexdigest(), size


def fetch(images, output):
    if os.geteuid() == 0:
        refuse()
    with deadline() as until:
        version, url, expected = distribution(images)
        output = local_path(output)
        parent = open_parent(output)
        try:
            directory = os.fstat(parent)
            if directory.st_uid != os.geteuid() or stat.S_IMODE(directory.st_mode) & 0o022:
                refuse()
            try:
                os.stat(output.name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                refuse()
            partial = "." + output.name + ".partial-" + secrets.token_hex(8)
            descriptor = os.open(
                partial,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
                dir_fd=parent,
            )
            try:
                identity = os.fstat(descriptor)
                actual, size = download(descriptor, url, until)
                if actual != expected:
                    refuse()
                os.fsync(descriptor)
                if not same_inode(identity, os.stat(partial, dir_fd=parent, follow_symlinks=False)):
                    refuse()
                # Exclusive publication cannot replace a raced existing target.
                os.link(
                    partial,
                    output.name,
                    src_dir_fd=parent,
                    dst_dir_fd=parent,
                    follow_symlinks=False,
                )
                os.fsync(parent)
                if not same_inode(identity, os.stat(partial, dir_fd=parent, follow_symlinks=False)):
                    refuse()
                os.unlink(partial, dir_fd=parent)
                os.fsync(parent)
            finally:
                os.close(descriptor)
        finally:
            os.close(parent)
    return {
        "schema_version": 1,
        "python_version": version,
        "url": url,
        "sha256": expected,
        "bytes": size,
        "artifact": str(output),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    try:
        evidence = fetch(options.images_json, options.output)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        RecursionError,
        URLError,
        HTTPException,
        KeyboardInterrupt,
    ):
        print("Python artifact fetch refused; retain partial evidence for review", file=sys.stderr)
        return 1
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
