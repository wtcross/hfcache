"""Decision 147: capture only a bounded, protected and explicitly indexed UI tree."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import stat
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar, NoReturn

from hfcache.api.credential_sources import source_path
from hfcache.errors import ConfigurationError
from hfcache.models import dump
from hfcache.ui_models import UiAssetManifest
from hfcache.url_paths import uri_path

if TYPE_CHECKING:
    from collections.abc import Mapping

    from hfcache.server_config import InstalledPolicy, ServerConfig

MAX_MOUNT_BYTES = 1048576
MAX_MOUNTS = 8192
MAX_MANIFEST_BYTES = 2097152
MAX_MEMBER_BYTES = 8388608
MAX_TOTAL_BYTES = 67108864
MAX_FILES = 4096
MAX_DIRECTORIES = 4096
MAX_ENTRIES = 8193
MAX_DEPTH = 8
MAX_PATH_BYTES = 1024
MAX_FDINFO_BYTES = 4096
MOUNT_FIELDS = 6
MOUNT_TRAILING_FIELDS = 3
DEVICE_FIELDS = 2
LOCAL_FILESYSTEMS = frozenset({"ext4", "xfs", "btrfs", "tmpfs", "overlay"})
_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,254}")
_HASHED_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*-[A-Za-z0-9_-]{8,64}\.[A-Za-z0-9]+")
_ESCAPES = {"040": " ", "011": "\t", "012": "\n", "134": "\\"}
_TOKENS = {
    "hfcache-ui-base": "__HFCACHE_UI_BASE_V1__",
    "hfcache-ui-bootstrap": "__HFCACHE_UI_BOOTSTRAP_V1__",
    "hfcache-ui-fingerprint": "__HFCACHE_UI_FINGERPRINT_V1__",
    "hfcache-ui-contract": "__HFCACHE_UI_CONTRACT_V1__",
}


def refuse() -> NoReturn:
    message = "enabled UI artifact is missing, unsafe, changed or incompatible"
    raise ConfigurationError.single(message, code="HFCFG005")


def _require(condition: object) -> None:
    if not condition:
        refuse()


def _path(value: str) -> PurePosixPath:
    result = PurePosixPath(value)
    _require(value.startswith("/") and not value.startswith("//"))
    _require(str(result) == value and ".." not in result.parts)
    return result


def _unescape(value: str) -> str:
    result = []
    position = 0
    while position < len(value):
        character = value[position]
        if character == "\\":
            encoded = value[position + 1 : position + 4]
            _require(encoded in _ESCAPES)
            result.append(_ESCAPES[encoded])
            position += 4
        else:
            result.append(character)
            position += 1
    return "".join(result)


@dataclass(frozen=True, slots=True)
class MountIdentity:
    mount_id: int
    parent_id: int
    device: tuple[int, int]
    root: PurePosixPath
    mountpoint: PurePosixPath
    filesystem: str


@dataclass(frozen=True, slots=True)
class MountSnapshot:
    raw: bytes
    entries: tuple[MountIdentity, ...]

    def select(self, path: Path | PurePosixPath) -> MountIdentity:
        canonical = _path(str(path))
        matches = [row for row in self.entries if canonical.is_relative_to(row.mountpoint)]
        _require(matches)
        depth = max(len(row.mountpoint.parts) for row in matches)
        selected = [row for row in matches if len(row.mountpoint.parts) == depth]
        by_id = {row.mount_id: row for row in selected}
        parents = {row.parent_id for row in selected}
        top = [row for row in selected if row.mount_id not in parents]
        _require(len(top) == 1)
        current = top[0]
        seen = set()
        while current.mount_id not in seen:
            seen.add(current.mount_id)
            if current.parent_id not in by_id:
                break
            current = by_id[current.parent_id]
        _require(seen == set(by_id) and current.parent_id not in by_id)
        return top[0]

    def physical(self, path: Path) -> tuple[tuple[int, int], PurePosixPath]:
        row = self.select(path)
        return row.device, row.root / _path(str(path)).relative_to(row.mountpoint)

    def corroborate(self, descriptor: int, expected: MountIdentity) -> None:
        with Path(f"/proc/self/fdinfo/{descriptor}").open("rb") as stream:
            body = stream.read(MAX_FDINFO_BYTES + 1)
        _require(len(body) <= MAX_FDINFO_BYTES)
        values = [
            line.split(":", 1)[1].strip()
            for line in body.decode("ascii").splitlines()
            if line.startswith("mnt_id:")
        ]
        _require(len(values) == 1 and values[0].isascii() and values[0].isdigit())
        _require(int(values[0]) == expected.mount_id)
        info = os.fstat(descriptor)
        _require((os.major(info.st_dev), os.minor(info.st_dev)) == expected.device)


def parse_mount_snapshot(raw: bytes) -> MountSnapshot:
    """Retain Linux mount identities without touching any mapped target."""
    _require(0 < len(raw) <= MAX_MOUNT_BYTES)
    rows = []
    identifiers = set()
    for line in raw.decode("utf-8", errors="strict").splitlines():
        _require(len(rows) < MAX_MOUNTS and line.count(" - ") == 1)
        before, after = line.split(" - ")
        fields, trailing = before.split(" "), after.split(" ")
        _require(
            len(fields) >= MOUNT_FIELDS
            and len(trailing) >= MOUNT_TRAILING_FIELDS
            and all(fields)
            and all(trailing)
        )
        _require(all(value.isascii() and value.isdigit() for value in fields[:2]))
        mount_id, parent = int(fields[0]), int(fields[1])
        device = fields[2].split(":")
        _require(
            len(device) == DEVICE_FIELDS
            and all(value.isascii() and value.isdigit() for value in device)
        )
        root, where = _path(_unescape(fields[3])), _path(_unescape(fields[4]))
        _require(mount_id > 0 and parent >= 0 and mount_id not in identifiers)
        identifiers.add(mount_id)
        rows.append(
            MountIdentity(
                mount_id, parent, (int(device[0]), int(device[1])), root, where, trailing[0]
            )
        )
    _require(rows)
    return MountSnapshot(raw, tuple(rows))


def read_mount_snapshot() -> MountSnapshot:
    with Path("/proc/self/mountinfo").open("rb") as stream:
        raw = stream.read(MAX_MOUNT_BYTES + 1)
    return parse_mount_snapshot(raw)


def _overlap(left: PurePosixPath, right: PurePosixPath) -> bool:
    return left.is_relative_to(right) or right.is_relative_to(left)


def forbidden_paths(  # noqa: PLR0913 - exact independent startup authority inputs
    server: ServerConfig,
    policy: InstalledPolicy,
    *,
    state_root: Path,
    instance_lock_path: Path,
    hub_token_file: Path | None,
    environ: Mapping[str, str],
) -> tuple[Path, ...]:
    """Only already configured authority spellings; no protected target is opened."""
    paths = {
        policy.root,
        policy.path,
        server.archive_config,
        state_root,
        instance_lock_path,
        server.verification.unix_socket,
    }
    if server.listener.unix_address is not None:
        paths.add(server.listener.unix_address)
    if hub_token_file is not None:
        paths.update((hub_token_file, hub_token_file.parent))
    credentials = [
        server.credentials.writer,
        server.credentials.reader,
        server.credentials.mcp_reader,
    ]
    if server.basic is not None:
        credentials.append(server.basic.administrator)
    for source in credentials:
        if source is not None:
            resolved = source_path(source, environ)
            paths.update((resolved, resolved.parent))
    if server.listener.tls is not None:
        for path in (server.listener.tls.private_key, server.listener.tls.certificate):
            paths.update((path, path.parent))
    return tuple(sorted(paths))


def _check_disjoint(
    root: Path, forbidden: tuple[Path, ...], mounts: MountSnapshot
) -> MountIdentity:
    asset = _path(str(root))
    selected = mounts.select(root)
    _require(selected.filesystem in LOCAL_FILESYSTEMS)
    asset_device, physical_asset = mounts.physical(root)
    for path in forbidden:
        protected = _path(str(path))
        _require(not _overlap(asset, protected))
        device, physical = mounts.physical(path)
        _require(device != asset_device or not _overlap(physical_asset, physical))
    return selected


def _identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_uid,
        info.st_gid,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _protected(info: os.stat_result, *, directory: bool) -> None:
    _require((stat.S_ISDIR if directory else stat.S_ISREG)(info.st_mode))
    _require(info.st_uid in {0, os.geteuid()} and not info.st_mode & 0o022)
    if not directory:
        _require(info.st_nlink == 1)


def _linked(parent: int, name: str, descriptor: int) -> None:
    _require(
        _identity(os.stat(name, dir_fd=parent, follow_symlinks=False))
        == _identity(os.fstat(descriptor))
    )


def _open_root(path: Path, mounts: MountSnapshot) -> tuple[int, int, tuple[tuple[int, ...], ...]]:
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    descriptor = -1
    current = Path("/")
    chain = []
    try:
        _protected(os.fstat(parent), directory=True)
        mounts.corroborate(parent, mounts.select(current))
        chain.append(_identity(os.fstat(parent)))
        for number, name in enumerate(path.parts[1:]):
            current /= name
            descriptor = os.open(
                name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent
            )
            _protected(os.fstat(descriptor), directory=True)
            mounts.corroborate(descriptor, mounts.select(current))
            _linked(parent, name, descriptor)
            chain.append(_identity(os.fstat(descriptor)))
            if number == len(path.parts) - 2:
                return parent, descriptor, tuple(chain)
            os.close(parent)
            parent, descriptor = descriptor, -1
        refuse()
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)
        raise


def _verify_ancestry(
    path: Path, mounts: MountSnapshot, original: tuple[tuple[int, ...], ...]
) -> None:
    """Rewalk pinned links; shared ancestors may change unrelated children.

    Every link retains device/inode/type/mode/owner/link-count and is checked
    under protected no-follow descriptors again. The captured root retains its
    full mutation identity; ancestor directory timestamps and sizes are not a
    promise that siblings elsewhere in /opt or a fixture root stay unchanged.
    """
    parent, root, current = _open_root(path, mounts)
    try:
        _require(len(current) == len(original))
        _require(
            all(before[:6] == after[:6] for before, after in zip(original, current, strict=True))
        )
        _require(original[-1] == current[-1])
    finally:
        os.close(root)
        os.close(parent)


def _read_file(
    parent: int, name: str, maximum: int, mounts: MountSnapshot, mount: MountIdentity
) -> tuple[bytes, tuple[int, ...]]:
    descriptor = os.open(
        name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent
    )
    try:
        before = os.fstat(descriptor)
        _protected(before, directory=False)
        mounts.corroborate(descriptor, mount)
        _linked(parent, name, descriptor)
        _require(0 <= before.st_size <= maximum)
        chunks = []
        total = 0
        while total <= maximum:
            part = os.read(descriptor, min(65536, maximum + 1 - total))
            if not part:
                break
            chunks.append(part)
            total += len(part)
        _require(total == before.st_size and _identity(before) == _identity(os.fstat(descriptor)))
        _linked(parent, name, descriptor)
        return b"".join(chunks), _identity(before)
    finally:
        os.close(descriptor)


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for name, value in pairs:
        _require(name not in result)
        result[name] = value
    return result


@dataclass(frozen=True, slots=True)
class CapturedMember:
    body: bytes
    mime: str
    private_cache: bool


@dataclass(slots=True)
class UiCapture:
    manifest: UiAssetManifest
    fingerprint: str
    encoded_manifest: bytes
    members: Mapping[str, CapturedMember]
    shells: Mapping[str, bytes]
    root_descriptor: int

    def close(self) -> None:
        if self.root_descriptor >= 0:
            os.close(self.root_descriptor)
            self.root_descriptor = -1
        self.members = MappingProxyType({})
        self.shells = MappingProxyType({})
        self.encoded_manifest = b""


class _Shell(HTMLParser):
    """Accept the inert application shell, never arbitrary browser-parsed HTML."""

    _ATTRIBUTES: ClassVar[dict[str, set[str]]] = {
        "html": {"lang"},
        "head": set(),
        "body": set(),
        "title": set(),
        "meta": {"name", "content", "charset"},
        "base": {"href"},
        "script": {"type", "src", "crossorigin"},
        "link": {"rel", "href", "crossorigin", "as", "type"},
        "div": {"id", "class"},
        "main": {"aria-label"},
        "h1": set(),
        "p": {"class"},
        "span": {"class"},
        "a": {"href"},
        "noscript": set(),
        "strong": set(),
        "em": set(),
    }
    _VOID = frozenset({"meta", "base", "link"})

    def __init__(self, members: Mapping[str, CapturedMember]) -> None:
        super().__init__(convert_charrefs=True)
        self.members = members
        self.stack: list[str] = []
        self.slots: dict[str, int] = {}
        self.base = 0
        self.roots = 0
        self.reload = 0
        self.html = 0
        self.head = 0
        self.body = 0
        self.root_depth: int | None = None
        self.root_explanation = ""
        self.reload_text: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # noqa: PLR0912 - closed element-specific HTML rules
        _require(tag in self._ATTRIBUTES)
        attributes = attrs
        checked = dict(attributes)
        _require(len(checked) == len(attributes) and set(checked) <= self._ATTRIBUTES[tag])
        if tag == "html":
            _require(not self.stack)
            self.html += 1
        elif tag in {"head", "body"}:
            _require(self.stack == ["html"])
            if tag == "head":
                _require(self.head == self.body == 0)
                self.head += 1
            else:
                _require(self.head == 1 and self.body == 0)
                self.body += 1
        elif tag in {"base", "meta", "link", "title"}:
            _require(self.stack == ["html", "head"])
        elif tag == "script":
            _require(self.stack in (["html", "head"], ["html", "body"]))
        else:
            _require("body" in self.stack)
        if tag == "base":
            _require(checked == {"href": _TOKENS["hfcache-ui-base"]})
            self.base += 1
        if tag == "meta" and checked.get("name") in _TOKENS:
            name = checked["name"]
            _require(checked == {"name": name, "content": _TOKENS[name]})
            self.slots[name] = self.slots.get(name, 0) + 1
        for name, value in checked.items():
            if value is not None and any(token in value for token in _TOKENS.values()):
                _require(
                    (tag == "base" and name == "href")
                    or (tag == "meta" and name == "content" and checked.get("name") in _TOKENS)
                )
        if tag in {"script", "link"}:
            raw = checked.get("src" if tag == "script" else "href")
            if not isinstance(raw, str):
                refuse()
            path = raw.removeprefix("./")
            _require(path in self.members and path.startswith("assets/"))
            if tag == "script":
                _require(
                    checked.get("type") == "module" and self.members[path].mime == "text/javascript"
                )
            else:
                _require(checked.get("rel") in {"stylesheet", "modulepreload", "preload", "icon"})
        if tag == "div" and checked.get("id") == "root":
            _require(self.stack == ["html", "body"])
            self.roots += 1
            self.root_depth = len(self.stack) + 1
        if tag == "a":
            _require(
                checked == {"href": "./"}
                and self.root_depth is not None
                and self.reload_text is None
            )
            self.reload_text = ""
        if tag not in self._VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        _require(tag in self._VOID)
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        _require(self.stack and self.stack[-1] == tag)
        if tag == "a":
            _require(
                self.reload_text is not None and self.reload_text.strip() == "Reload interface"
            )
            self.reload += 1
            self.reload_text = None
        if self.root_depth == len(self.stack):
            self.root_depth = None
        self.stack.pop()

    def handle_data(self, data: str) -> None:
        _require(not (self.stack and self.stack[-1] == "script" and data.strip()))
        _require(not any(token in data for token in _TOKENS.values()))
        if self.reload_text is not None:
            self.reload_text += data
        elif self.root_depth is not None:
            self.root_explanation += data

    def handle_comment(self, data: str) -> None:
        _require(not any(token in data for token in _TOKENS.values()))

    def handle_decl(self, decl: str) -> None:
        _require(decl.lower() == "doctype html")

    def unknown_decl(self, data: str) -> None:
        del data
        refuse()

    def handle_pi(self, data: str) -> None:
        del data
        refuse()


def render_shell(
    raw: bytes, members: Mapping[str, CapturedMember], *, prefix: str, fingerprint: str
) -> bytes:
    """Validate exact byte/token placement before replacing only approved inert slots."""
    parser = _Shell(members)
    parser.feed(raw.decode("utf-8", errors="strict"))
    parser.close()
    _require(
        not parser.stack
        and parser.html == parser.head == parser.body == parser.base == parser.roots == 1
    )
    _require(
        parser.reload >= 1
        and parser.root_explanation.strip()
        and parser.slots == dict.fromkeys(_TOKENS, 1)
    )
    for name, token in _TOKENS.items():
        _require(raw.count(token.encode()) == (2 if name == "hfcache-ui-base" else 1))
    replacements = {
        _TOKENS["hfcache-ui-base"]: uri_path(prefix + "/ui/"),
        _TOKENS["hfcache-ui-bootstrap"]: uri_path(prefix + "/ui/bootstrap.json"),
        _TOKENS["hfcache-ui-fingerprint"]: fingerprint,
        _TOKENS["hfcache-ui-contract"]: "1",
    }
    rendered = raw
    for token, value in replacements.items():
        rendered = rendered.replace(token.encode(), html.escape(value, quote=True).encode())
    _require(len(rendered) <= MAX_MEMBER_BYTES)
    return rendered


def capture_assets(  # noqa: PLR0913, PLR0915 - one pinned capture transaction and ownership transfer
    server: ServerConfig,
    policy: InstalledPolicy,
    *,
    state_root: Path,
    instance_lock_path: Path,
    application_version: str,
    wire_source_digest: str,
    hub_token_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> UiCapture | None:
    """Capture before store construction; disabled web performs no mount or asset I/O."""
    if not server.web.enabled:
        return None
    parent = root = -1
    try:
        if server.web.asset_root is None or server.web.manifest_sha256 is None:
            refuse()
        path = server.web.asset_root
        mounts = read_mount_snapshot()
        forbidden = forbidden_paths(
            server,
            policy,
            state_root=state_root,
            instance_lock_path=instance_lock_path,
            hub_token_file=hub_token_file,
            environ=os.environ if environ is None else environ,
        )
        mount = _check_disjoint(path, forbidden, mounts)
        parent, root, ancestry = _open_root(path, mounts)
        raw, manifest_identity = _read_file(
            root, "manifest.json", MAX_MANIFEST_BYTES, mounts, mount
        )
        fingerprint = hashlib.sha256(raw).hexdigest()
        _require(fingerprint == server.web.manifest_sha256)
        manifest = UiAssetManifest.model_validate(json.loads(raw, object_pairs_hook=_unique))
        _require(dump(manifest) == raw)
        _require(
            manifest.build.application_version == application_version
            and manifest.build.wire_source_digest == wire_source_digest
        )
        _require(
            hashlib.sha256(dump(manifest.build.toolchain)).hexdigest()
            == manifest.build.toolchain_sha256
        )
        indexed = {member.path: member for member in manifest.members}
        captured: dict[str, CapturedMember] = {}
        counts = {"entries": 0, "files": 0, "directories": 0, "bytes": 0}

        def walk(descriptor: int, relative: str, depth: int) -> None:
            _require(depth <= MAX_DEPTH)
            before = os.fstat(descriptor)
            _protected(before, directory=True)
            mounts.corroborate(descriptor, mount)
            with os.scandir(descriptor) as entries:
                for entry in entries:
                    counts["entries"] += 1
                    _require(counts["entries"] <= MAX_ENTRIES and depth <= MAX_DEPTH)
                    _require(_COMPONENT.fullmatch(entry.name) is not None)
                    name = relative + entry.name
                    _require(len(name) <= MAX_PATH_BYTES)
                    status = entry.stat(follow_symlinks=False)
                    if stat.S_ISDIR(status.st_mode):
                        counts["directories"] += 1
                        _require(counts["directories"] <= MAX_DIRECTORIES)
                        child = os.open(
                            entry.name,
                            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                            dir_fd=descriptor,
                        )
                        try:
                            _linked(descriptor, entry.name, child)
                            walk(child, name + "/", depth + 1)
                            _linked(descriptor, entry.name, child)
                        finally:
                            os.close(child)
                    elif name == "manifest.json":
                        _require(_identity(status) == manifest_identity)
                    else:
                        counts["files"] += 1
                        _require(counts["files"] <= MAX_FILES and name in indexed)
                        member = indexed[name]
                        body, _ = _read_file(
                            descriptor,
                            entry.name,
                            min(member.bytes, MAX_MEMBER_BYTES),
                            mounts,
                            mount,
                        )
                        counts["bytes"] += len(body)
                        _require(
                            counts["bytes"] <= MAX_TOTAL_BYTES
                            and len(body) == member.bytes
                            and hashlib.sha256(body).hexdigest() == member.sha256
                        )
                        captured[name] = CapturedMember(
                            body,
                            member.mime,
                            name.startswith("assets/")
                            and _HASHED_NAME.fullmatch(entry.name) is not None,
                        )
            _require(_identity(before) == _identity(os.fstat(descriptor)))

        walk(root, "", 1)
        _require(set(captured) == set(indexed))
        _require(
            hashlib.sha256(captured["licenses.json"].body).hexdigest()
            == manifest.build.licenses_sha256
        )
        _require(
            hashlib.sha256(captured["THIRD_PARTY_NOTICES.txt"].body).hexdigest()
            == manifest.build.notices_sha256
        )
        members = MappingProxyType(captured)
        prefixes = {"", server.listener.root_path}
        shells = MappingProxyType(
            {
                prefix: render_shell(
                    captured["index.html"].body, members, prefix=prefix, fingerprint=fingerprint
                )
                for prefix in prefixes
            }
        )
        _linked(parent, path.name, root)
        _verify_ancestry(path, mounts, ancestry)
        _require(read_mount_snapshot().raw == mounts.raw)
        result = UiCapture(manifest, fingerprint, raw, members, shells, root)
        root = -1
        return result  # noqa: TRY300 - transfer the one root FD before finally closes remaining owners
    except OSError, ValueError, UnicodeError, RecursionError:
        refuse()
    finally:
        if root >= 0:
            os.close(root)
        if parent >= 0:
            os.close(parent)
