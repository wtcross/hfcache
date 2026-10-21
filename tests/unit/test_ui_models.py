"""Independent UI wire goldens and adversarial trust-boundary examples."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from hfcache.models import dump
from hfcache.ui_models import (
    UiAdminPermission,
    UiAssetManifest,
    UiAssetMember,
    UiBootstrap,
    UiBuildIdentity,
    UiBuildMetadata,
    UiHtmlMetaIdentity,
    UiPaths,
    UiToolchain,
    UiUser,
)
from tests.fixtures.ui_examples import ui_asset_manifest, ui_bootstrap


def model_examples():
    manifest = ui_asset_manifest()
    bootstrap = ui_bootstrap()
    return (
        manifest,
        manifest.build,
        manifest.build.toolchain,
        manifest.meta_identity,
        manifest.members[0],
        bootstrap,
        bootstrap.paths,
        bootstrap.user,
        bootstrap.user.admin_permissions[0],
        bootstrap.build,
    )


def test_every_ui_wire_field_is_required_and_unknown_fields_refuse():
    examples = model_examples()
    assert {type(example) for example in examples} == {
        UiAdminPermission,
        UiAssetManifest,
        UiAssetMember,
        UiBootstrap,
        UiBuildIdentity,
        UiBuildMetadata,
        UiHtmlMetaIdentity,
        UiPaths,
        UiToolchain,
        UiUser,
    }
    for example in examples:
        payload = example.model_dump(mode="json")
        with pytest.raises(ValidationError):
            type(example).model_validate(payload | {"unreviewed": True})
        for name in payload:
            missing = deepcopy(payload)
            del missing[name]
            with pytest.raises(ValidationError):
                type(example).model_validate(missing)
        with pytest.raises(ValidationError):
            example.unreviewed = True


@pytest.mark.parametrize("value", [True, False, 1.0, "1", 0, 2, None])
@pytest.mark.parametrize(
    "field", ["schema_version", "ui_contract_version", "rest_api_schema_version"]
)
def test_bootstrap_versions_refuse_coercion_and_future_contracts(field, value):
    payload = ui_bootstrap().model_dump(mode="json")
    payload[field] = value
    with pytest.raises(ValidationError):
        UiBootstrap.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("instance_id", "E" * 32),
        ("authority_epoch", "f" * 32),
        ("instance_id", "e" * 31),
        ("wire_source_digest", "f" * 64),
        ("configured_archive_id", "not-a-uuid"),
        ("configured_archive_id", "01234567-89AB-CDEF-0123-456789ABCDEF"),
        ("archive_identity_source", "live_probe"),
        ("config_fingerprint", "f" * 64),
        ("configured_origin", "http://archive.invalid"),
        ("configured_origin", "https://archive.invalid/"),
        ("configured_origin", "https://user:secret@archive.invalid"),
        ("configured_origin", "https://archive.invalid/ui"),
        ("configured_origin", "https://archive.invalid?query"),
        ("configured_origin", "https://archive.invalid#fragment"),
        ("configured_origin", "https://ARCHIVE.invalid"),
        ("configured_origin", "https://archive.invalid\n"),
        ("configured_origin", "https://archivé.invalid"),
    ],
)
def test_bootstrap_rejects_unbound_or_unsafe_identity(field, value):
    payload = ui_bootstrap().model_dump(mode="json")
    payload[field] = value
    with pytest.raises(ValidationError):
        UiBootstrap.model_validate(payload)


@pytest.mark.parametrize(
    ("prefix", "encoded"),
    [("", ""), ("/management", "/management"), ("/équipe/模型", "/%C3%A9quipe/%E6%A8%A1%E5%9E%8B")],
)
@pytest.mark.parametrize("native", [False, True])
def test_paths_bind_raw_prefix_to_encoded_endpoints(prefix, encoded, native):
    effective = "" if native else prefix
    base = "" if native else encoded
    paths = UiPaths(
        public_prefix=prefix,
        effective_prefix=effective,
        ui_base=base + "/ui/",
        bootstrap=base + "/ui/bootstrap.json",
        api_base=base + "/api/v1",
        mcp_base=base + "/mcp/",
    )
    assert paths.public_prefix == prefix
    assert UiPaths.model_validate_json(dump(paths)) == paths
    assert paths.model_copy(update={"mcp_base": None}).mcp_base is None


@pytest.mark.parametrize(
    "prefix",
    [
        "//foreign.invalid",
        "/",
        "/a/",
        "/a//b",
        "/a/./b",
        "/a/../b",
        "/%61",
        "/a?b",
        "/a#b",
        "/a\\b",
        "/a b",
        "/a\x00",
        "/" + "é" * 512,
    ],
)
def test_paths_refuse_ambiguous_and_oversize_prefixes(prefix):
    payload = ui_bootstrap().paths.model_dump(mode="json")
    payload["public_prefix"] = prefix
    with pytest.raises(ValidationError):
        UiPaths.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("effective_prefix", "/other"),
        ("ui_base", "https://foreign.invalid/ui/"),
        ("bootstrap", "/management/ui/bootstrap.json?other"),
        ("api_base", "/api/v1"),
        ("mcp_base", "/management/mcp"),
    ],
)
def test_paths_refuse_endpoint_confusion(field, value):
    payload = ui_bootstrap().paths.model_dump(mode="json")
    payload[field] = value
    with pytest.raises(ValidationError):
        UiPaths.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("path", "../index.html"),
        ("path", "/index.html"),
        ("path", "assets/../index.html"),
        ("path", "assets//app.js"),
        ("path", "assets/é.js"),
        ("path", "assets/app%2ejs"),
        ("path", "assets/app.svg"),
        ("path", "assets/app.js.map"),
        ("path", "app.js"),
        ("path", "assets/" + "a" * 253 + ".js"),
        ("path", "assets/" + "a/" * 7 + "app.js"),
        ("path", "assets/other.html"),
        ("mime", "application/javascript"),
        ("mime", "text/plain"),
        ("mime", "image/svg+xml"),
        ("bytes", True),
        ("bytes", "1"),
        ("bytes", -1),
        ("bytes", 8388609),
        ("sha256", "A" * 64),
    ],
)
def test_asset_member_rejects_payload_escape_and_loose_metadata(field, value):
    member = next(member for member in ui_asset_manifest().members if member.path.endswith(".js"))
    payload = member.model_dump(mode="json")
    payload[field] = value
    with pytest.raises(ValidationError):
        UiAssetMember.model_validate(payload)


@pytest.mark.parametrize(
    "attack",
    ["reorder", "duplicate", "missing", "license_hash", "notice_hash", "aggregate", "empty_html"],
)
def test_manifest_rejects_incomplete_ambiguous_or_unbound_members(attack):
    payload = ui_asset_manifest().model_dump(mode="json")
    members = payload["members"]
    if attack == "reorder":
        members.reverse()
    elif attack == "duplicate":
        members.append(deepcopy(members[-1]))
    elif attack == "missing":
        members[:] = [item for item in members if item["path"] != "licenses.json"]
    elif attack == "license_hash":
        payload["build"]["licenses_sha256"] = "f" * 64
    elif attack == "notice_hash":
        payload["build"]["notices_sha256"] = "f" * 64
    elif attack == "aggregate":
        for index in range(9):
            members.append(
                {
                    "path": f"assets/z{index}.js",
                    "bytes": 8388608,
                    "sha256": "f" * 64,
                    "mime": "text/javascript",
                }
            )
        members.sort(key=lambda item: item["path"])
    else:
        next(item for item in members if item["path"] == "index.html")["bytes"] = 0
    with pytest.raises(ValidationError):
        UiAssetManifest.model_validate(payload)


@pytest.mark.parametrize(
    ("granted", "effective", "reason", "accepted"),
    [
        (False, False, "not_granted", True),
        (True, False, "feature_unavailable", True),
        (True, True, "allowed", True),
        (False, True, "allowed", False),
        (True, False, "allowed", False),
        (False, False, "feature_unavailable", False),
    ],
)
def test_permission_projection_cannot_escalate_a_grant(granted, effective, reason, accepted):
    payload = {
        "capability": "config-read",
        "granted": granted,
        "effective": effective,
        "reason": reason,
    }
    if accepted:
        assert UiAdminPermission.model_validate(payload).effective == effective
    else:
        with pytest.raises(ValidationError):
            UiAdminPermission.model_validate(payload)


@pytest.mark.parametrize(
    "attack", ["subject", "display", "method", "class", "caps", "permissions", "missing_permission"]
)
def test_user_projection_preserves_principal_and_exact_capability_order(attack):
    payload = ui_bootstrap().user.model_dump(mode="json")
    if attack == "subject":
        payload["subject"] = "archive admin"
    elif attack == "display":
        payload["display_name"] = "someone-else"
    elif attack == "method":
        payload["authentication_method"] = "bearer"
    elif attack == "class":
        payload["credential_class"] = "rest-reader"
    elif attack == "caps":
        payload["rest_capabilities"].reverse()
    elif attack == "permissions":
        payload["admin_permissions"].reverse()
    else:
        payload["admin_permissions"].pop()
    with pytest.raises(ValidationError):
        UiUser.model_validate(payload)
