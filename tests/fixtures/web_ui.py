"""Synthetic indexed files for source boundary tests, never release evidence."""

import hashlib
import secrets
import tempfile
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from hfcache.api.basic import create_administrator_record
from hfcache.models import dump
from hfcache.reporting import RuntimeVersions
from hfcache.server_config import (
    InstalledPolicy,
    ServerConfig,
    WebConfig,
    validate_server_config_mapping,
)
from hfcache.ui_models import UiAssetManifest, UiToolchain
from tests.fixtures.examples import ARCHIVE_ID

WIRE_DIGEST = "a" * 64
WRITER = "writer_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
SHELL = b"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8">
<base href="__HFCACHE_UI_BASE_V1__">
<meta name="hfcache-ui-base" content="__HFCACHE_UI_BASE_V1__">
<meta name="hfcache-ui-bootstrap" content="__HFCACHE_UI_BOOTSTRAP_V1__">
<meta name="hfcache-ui-fingerprint" content="__HFCACHE_UI_FINGERPRINT_V1__">
<meta name="hfcache-ui-contract" content="__HFCACHE_UI_CONTRACT_V1__">
<title>Archive interface</title>
<script type="module" src="./assets/main-AbCd1234.js"></script>
<link rel="stylesheet" href="./assets/main-AbCd1234.css">
</head><body><div id="root"><p>The interface is loading. If startup fails, reload it.</p>
<a href="./">Reload interface</a></div></body></html>"""


@cache
def administrator():
    password = secrets.token_urlsafe(32).encode()
    return create_administrator_record("ui-source-administrator", "human", password), password


@dataclass
class UiProfile:
    root: Path
    server: ServerConfig
    policy: InstalledPolicy
    bodies: dict[str, bytes]
    password: bytes = field(repr=False)

    @property
    def assets(self) -> Path:
        return self.root / "artifact"

    @property
    def lock(self) -> Path:
        return self.root / "runtime/api.lock"

    def repin(self) -> None:
        self.server = self.server.model_copy(
            update={
                "web": WebConfig.model_validate(
                    {
                        "enabled": True,
                        "asset_root": str(self.assets),
                        "manifest_sha256": hashlib.sha256(
                            (self.assets / "manifest.json").read_bytes()
                        ).hexdigest(),
                    }
                )
            }
        )


def make_profile(*, prefix: str = "", shell: bytes = SHELL) -> UiProfile:
    scratch = Path(__file__).resolve().parents[2] / ".scratch"
    root = Path(tempfile.mkdtemp(prefix="web-005-unit-", dir=scratch))
    for name in ("artifact/assets", "credentials", "policy", "runtime"):
        (root / name).mkdir(parents=True, mode=0o700)
    record, password = administrator()
    (root / "credentials/administrator.json").write_bytes(dump(record))
    (root / "credentials/writer").write_text(WRITER)
    for path in (root / "credentials").iterdir():
        path.chmod(0o600)
    config = root / "policy/archive.toml"
    config.write_text(
        f'schema_version=1\n[storage]\narchive_root="{root / "archive"}"\n'
        f'archive_id="{ARCHIVE_ID}"\n'
    )
    bodies = {
        "index.html": shell,
        "assets/main-AbCd1234.js": b"export const unitFixture = true;\n",
        "assets/main-AbCd1234.css": b"body { color: #111; }\n",
        "licenses.json": b"{}\n",
        "THIRD_PARTY_NOTICES.txt": b"Synthetic unit fixture notices.\n",
    }
    for name, body in bodies.items():
        (root / "artifact" / name).write_bytes(body)
    toolchain = UiToolchain(node="24.18.1", pnpm="11.18.0", typescript="6.0.3", vite="8.3.4")
    manifest = UiAssetManifest.model_validate(
        {
            "schema_version": 1,
            "kind": "hfcache_web_assets",
            "entrypoint": "index.html",
            "meta_identity": {
                "ui_base": "__HFCACHE_UI_BASE_V1__",
                "bootstrap_path": "__HFCACHE_UI_BOOTSTRAP_V1__",
                "asset_fingerprint": "__HFCACHE_UI_FINGERPRINT_V1__",
                "ui_contract": "__HFCACHE_UI_CONTRACT_V1__",
            },
            "build": {
                "application_version": RuntimeVersions.measured().application,
                "source_commit": "0" * 40,
                "source_snapshot_sha256": "b" * 64,
                "source_dirty": True,
                "ui_contract_version": 1,
                "rest_api_schema_version": 1,
                "wire_source_digest": WIRE_DIGEST,
                "pnpm_lock_sha256": "c" * 64,
                "toolchain": toolchain.model_dump(),
                "toolchain_sha256": hashlib.sha256(dump(toolchain)).hexdigest(),
                "licenses_sha256": hashlib.sha256(bodies["licenses.json"]).hexdigest(),
                "notices_sha256": hashlib.sha256(bodies["THIRD_PARTY_NOTICES.txt"]).hexdigest(),
            },
            "members": [
                {
                    "path": name,
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "mime": "text/html"
                    if name == "index.html"
                    else "text/css"
                    if name.endswith(".css")
                    else "text/javascript"
                    if name.endswith(".js")
                    else "application/json"
                    if name.endswith(".json")
                    else "text/plain",
                }
                for name, body in sorted(bodies.items())
            ],
        }
    )
    encoded = dump(manifest)
    (root / "artifact/manifest.json").write_bytes(encoded)
    server = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(config),
            "state_directory": str(root / "state"),
            "credentials": {"writer": {"file": str(root / "credentials/writer")}},
            "basic": {
                "origin": "https://testserver",
                "administrator": {"file": str(root / "credentials/administrator.json")},
            },
            "listener": {
                "root_path": prefix,
                "allowed_hosts": ["testserver"],
                "allowed_origins": ["https://testserver"],
            },
            "web": {
                "enabled": True,
                "asset_root": str(root / "artifact"),
                "manifest_sha256": hashlib.sha256(encoded).hexdigest(),
            },
        }
    )
    return UiProfile(root, server, InstalledPolicy.open(server), bodies, password)
