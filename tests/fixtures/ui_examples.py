"""Inert schema examples; these are not built-release or browser acceptance data."""

from hashlib import sha256

from hfcache.models import dump
from hfcache.ui_models import UiAssetManifest, UiBootstrap, UiBuildMetadata, UiToolchain

UI_BODIES = {
    "THIRD_PARTY_NOTICES.txt": b"Inert schema example notices.\n",
    "assets/app-12345678.js": b"export {};\n",
    "index.html": (
        b'<!doctype html><html lang="en"><head><meta charset="UTF-8">'
        b'<base href="__HFCACHE_UI_BASE_V1__">'
        b'<meta name="hfcache-ui-base" content="__HFCACHE_UI_BASE_V1__">'
        b'<meta name="hfcache-ui-bootstrap" content="__HFCACHE_UI_BOOTSTRAP_V1__">'
        b'<meta name="hfcache-ui-fingerprint" content="__HFCACHE_UI_FINGERPRINT_V1__">'
        b'<meta name="hfcache-ui-contract" content="__HFCACHE_UI_CONTRACT_V1__">'
        b'<title>Inert schema fixture</title></head><body><div id="root">'
        b'<p>The interface has not started.</p><a href="./">Reload interface</a>'
        b'</div><script type="module" src="./assets/app-12345678.js"></script>'
        b"</body></html>\n"
    ),
    "licenses.json": b"[]\n",
}


def ui_build_metadata() -> UiBuildMetadata:
    toolchain = UiToolchain(node="24.18.1", pnpm="11.18.0", typescript="6.0.3", vite="8.3.4")
    return UiBuildMetadata(
        application_version="0.2.2",
        source_commit="a" * 40,
        source_snapshot_sha256="b" * 64,
        source_dirty=True,
        ui_contract_version=1,
        rest_api_schema_version=1,
        wire_source_digest="c" * 64,
        pnpm_lock_sha256="d" * 64,
        toolchain=toolchain,
        toolchain_sha256=sha256(dump(toolchain)).hexdigest(),
        licenses_sha256=sha256(UI_BODIES["licenses.json"]).hexdigest(),
        notices_sha256=sha256(UI_BODIES["THIRD_PARTY_NOTICES.txt"]).hexdigest(),
    )


def ui_asset_manifest() -> UiAssetManifest:
    mime = {
        "THIRD_PARTY_NOTICES.txt": "text/plain",
        "assets/app-12345678.js": "text/javascript",
        "index.html": "text/html",
        "licenses.json": "application/json",
    }
    return UiAssetManifest.model_validate(
        {
            "schema_version": 1,
            "kind": "hfcache_web_assets",
            "build": ui_build_metadata().model_dump(),
            "entrypoint": "index.html",
            "meta_identity": {
                "ui_base": "__HFCACHE_UI_BASE_V1__",
                "bootstrap_path": "__HFCACHE_UI_BOOTSTRAP_V1__",
                "asset_fingerprint": "__HFCACHE_UI_FINGERPRINT_V1__",
                "ui_contract": "__HFCACHE_UI_CONTRACT_V1__",
            },
            "members": [
                {
                    "path": path,
                    "bytes": len(body),
                    "sha256": sha256(body).hexdigest(),
                    "mime": mime[path],
                }
                for path, body in sorted(UI_BODIES.items())
            ],
        }
    )


def ui_bootstrap() -> UiBootstrap:
    manifest = ui_asset_manifest()
    return UiBootstrap.model_validate(
        {
            "schema_version": 1,
            "kind": "hfcache_ui_bootstrap",
            "ui_contract_version": 1,
            "rest_api_schema_version": 1,
            "wire_source_digest": "c" * 64,
            "instance_id": "e" * 32,
            "authority_epoch": "e" * 32,
            "configured_archive_id": "01234567-89ab-cdef-0123-456789abcdef",
            "archive_identity_source": "installed_policy",
            "config_fingerprint": None,
            "configured_origin": "https://archive.invalid",
            "paths": {
                "public_prefix": "/management",
                "effective_prefix": "/management",
                "ui_base": "/management/ui/",
                "bootstrap": "/management/ui/bootstrap.json",
                "api_base": "/management/api/v1",
                "mcp_base": "/management/mcp/",
            },
            "user": {
                "subject": "archive-admin",
                "display_name": "archive-admin",
                "authentication_method": "basic",
                "credential_class": "rest-writer",
                "rest_capabilities": ["read", "write"],
                "admin_permissions": [
                    {
                        "capability": capability,
                        "granted": True,
                        "effective": False,
                        "reason": "feature_unavailable",
                    }
                    for capability in (
                        "config-read",
                        "config-write",
                        "host-read",
                        "observer-stop",
                        "schedule-write",
                    )
                ],
            },
            "build": {
                "asset_manifest_sha256": sha256(dump(manifest)).hexdigest(),
                "metadata": manifest.build.model_dump(),
            },
        }
    )
