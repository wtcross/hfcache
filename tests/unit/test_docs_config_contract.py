"""Documented defaults and numeric constraints agree with strict model domains."""

import ast
import json
import re
import tomllib
from pathlib import Path

import pytest
from pydantic import ValidationError

from hfcache.client_config import ClientConfig
from hfcache.config import (
    HubConfig,
    RepairConfig,
    RepositoryConfig,
    StorageConfig,
    SyncConfig,
    VerificationConfig,
)
from hfcache.server_config import (
    ListenerConfig,
    ServerLimits,
    VerificationExecutorConfig,
    validate_server_config_mapping,
)

ROOT = Path(__file__).parents[2]


def rows(text, heading):
    section = text.split(heading, 1)[1]
    result = {}
    started = False
    for line in section.splitlines():
        if not line.startswith("|"):
            if started:
                break
            continue
        started = True
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line)[1:-1]]
        if cells and re.fullmatch(r"`[a-z_][a-z_.]*`", cells[0]):
            key = cells[0].strip("`")
            assert key not in result
            result[key] = cells[1:]
    assert result
    return result


def default_value(cell):
    if cell in {"absent", "omitted"}:
        return None
    match = re.search(r"`([^`]+)`", cell)
    value = match[1] if match else cell
    if value in {"true", "false"}:
        return value == "true"
    try:
        return ast.literal_eval(value)
    except ValueError, SyntaxError:
        return value


def assert_defaults(documented, instance, column=0):
    assert set(documented) == set(type(instance).model_fields)
    values = instance.model_dump(mode="json")
    for key, cells in documented.items():
        if type(instance).model_fields[key].is_required():
            assert "required" in cells[column]
        else:
            assert default_value(cells[column]) == values[key], key


def assert_numeric_bounds(cells, schema):
    numbers = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", cells[-1].split(";", 1)[0])]
    assert len(numbers) == 2
    lower = "exclusiveMinimum" if "exclusiveMinimum" in schema else "minimum"
    upper = "exclusiveMaximum" if "exclusiveMaximum" in schema else "maximum"
    assert numbers == [schema[lower], schema[upper]]
    if lower == "exclusiveMinimum":
        assert "(" in cells[-1] or "greater than" in cells[-1]
    interval = re.search(r"([\[(])\s*\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?\s*([\])])", cells[-1])
    if interval:
        assert (interval[1] == "(") == (lower == "exclusiveMinimum")
        assert (interval[2] == ")") == (upper == "exclusiveMaximum")
    else:
        assert upper == "maximum"


def assert_archive_constraints(text):
    storage = rows(text, "## 4. `[storage]`")
    properties = StorageConfig.model_json_schema()["properties"]
    for key in ("minimum_free_space_gib", "minimum_free_space_percent"):
        assert_numeric_bounds(storage[key], properties[key])
    choices = [int(value) for value in re.findall(r"`(\d+)`", storage["maximum_revisions"][-1])]
    # This is a custom validator domain, not a JSON-schema enum.
    permitted = []
    for value in range(1, 11):
        try:
            StorageConfig.model_validate(
                {
                    "archive_root": "/fixture/archive",
                    "archive_id": "01234567-89ab-4cde-8fab-0123456789ab",
                    "maximum_revisions": value,
                }
            )
        except ValidationError:
            continue
        permitted.append(value)
    assert choices == permitted
    combined = rows(text, "## 5. `[sync]`")
    for prefix, model in (("sync", SyncConfig), ("verification", VerificationConfig)):
        for key, schema in model.model_json_schema()["properties"].items():
            if "minimum" in schema or "exclusiveMinimum" in schema:
                assert_numeric_bounds(combined[prefix + "." + key], schema)
    grace = combined["repair.retired_instance_grace_hours"][-1]
    minimum, maximum = [int(value) for value in re.findall(r"\d+", grace)]
    assert (
        maximum
        == RepairConfig.model_json_schema()["properties"]["retired_instance_grace_hours"]["maximum"]
    )
    assert (
        RepairConfig(retired_instance_grace_hours=minimum).retired_instance_grace_hours == minimum
    )
    with pytest.raises(ValidationError):
        RepairConfig(retired_instance_grace_hours=minimum - 1)
    hashing = combined["verification.hash_new_content"][-1]
    assert hashing == "Must be `true`"


def test_archive_numeric_choices_hashing_and_grace_constraint_cells_match_models():
    assert_archive_constraints((ROOT / "docs/configuration.md").read_text())


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("`1 <= n <= 32`", "`1 <= n <= 99`"),
        ("`3` or `5`", "`3` or `7`"),
        ("`168 <= n <= 8760`", "`167 <= n <= 8760`"),
        ("Must be `true`", "May be `false`"),
    ],
)
def test_wrong_archive_constraint_cells_are_rejected(old, new):
    text = (ROOT / "docs/configuration.md").read_text()
    assert old in text
    with pytest.raises((AssertionError, ValidationError)):
        assert_archive_constraints(text.replace(old, new))


@pytest.mark.parametrize("interval", ["(0, 300)", "[0, 300]", "(1, 10000]"])
def test_changed_interval_inclusivity_is_rejected(interval):
    schema = {"exclusiveMinimum": 0, "maximum": 300}
    if "10000" in interval:
        schema = {"minimum": 1, "maximum": 10000}
    with pytest.raises(AssertionError):
        assert_numeric_bounds(["5", "Finite " + interval], schema)


def assert_server_limits(text):
    documented = rows(text, "### Resource settings")
    assert_defaults(documented, ServerLimits())
    properties = ServerLimits.model_json_schema()["properties"]
    for key, cells in documented.items():
        assert_numeric_bounds(cells, properties[key])


def test_all_server_resource_defaults_and_ranges_match_models():
    assert_server_limits((ROOT / "docs/server.md").read_text())


@pytest.mark.parametrize("change", ["default", "minimum", "maximum", "missing"])
def test_wrong_documented_server_limits_fail_comparison(change):
    text = (ROOT / "docs/server.md").read_text()
    old = "| `max_request_bytes` | `1048576` | `1024`\u2013`16777216` |"
    replacement = {
        "default": old.replace("1048576", "2048576"),
        "minimum": old.replace("1024", "1025"),
        "maximum": old.replace("16777216", "16777217"),
        "missing": "",
    }[change]
    assert old in text
    with pytest.raises(AssertionError):
        assert_server_limits(text.replace(old, replacement))


def test_client_numeric_defaults_and_inclusive_exclusive_bounds_match_model():
    text = (ROOT / "docs/api-client.md").read_text()
    documented = rows(text, "| Setting | Default | Range / purpose |")
    instance = ClientConfig(schema_version=1)
    properties = ClientConfig.model_json_schema()["properties"]
    numeric = {
        key
        for key, value in properties.items()
        if value.get("type") in {"integer", "number"} and key != "schema_version"
    }
    assert set(documented) == numeric
    for key, cells in documented.items():
        assert default_value(cells[0]) == getattr(instance, key)
        assert_numeric_bounds(cells, properties[key])


def test_listener_and_verifier_defaults_match_models_and_documented_domains():
    text = (ROOT / "docs/server.md").read_text()
    listener = rows(text, "### Listener settings")
    verifier = rows(text, "### Private verifier client settings")
    assert_defaults(listener, ListenerConfig())
    assert_defaults(verifier, VerificationExecutorConfig())
    assert_numeric_bounds(
        listener["tcp_port"], ListenerConfig.model_json_schema()["properties"]["tcp_port"]
    )
    for key in ("timeout_seconds", "poll_seconds", "max_frame_bytes"):
        assert_numeric_bounds(
            verifier[key], VerificationExecutorConfig.model_json_schema()["properties"][key]
        )


def test_archive_policy_table_defaults_and_required_fields_match_models():
    text = (ROOT / "docs/configuration.md").read_text()
    assert_defaults(rows(text, "## 3. `[hub]`"), HubConfig(), column=1)
    storage = StorageConfig.model_validate(
        {"archive_root": "/fixture/archive", "archive_id": "01234567-89ab-4cde-8fab-0123456789ab"}
    )
    assert_defaults(rows(text, "## 4. `[storage]`"), storage, column=1)
    combined = rows(text, "## 5. `[sync]`")
    for prefix, instance in (
        ("sync", SyncConfig()),
        ("verification", VerificationConfig()),
        ("repair", RepairConfig()),
    ):
        subset = {
            key.removeprefix(prefix + "."): cells
            for key, cells in combined.items()
            if key.startswith(prefix + ".")
        }
        assert_defaults(subset, instance, column=1)
    assert_defaults(
        rows(text, "## 6. `[[repositories]]`"),
        RepositoryConfig(id="org/model", type="model"),
        column=1,
    )


@pytest.mark.parametrize("value", [2, 4, 6])
def test_documented_retention_choices_are_not_a_contiguous_range(value):
    with pytest.raises(ValidationError):
        StorageConfig.model_validate(
            {
                "archive_root": "/fixture/archive",
                "archive_id": "01234567-89ab-4cde-8fab-0123456789ab",
                "maximum_revisions": value,
            }
        )


def test_documented_hashing_and_repair_floor_are_enforced_by_semantic_validators():
    with pytest.raises(ValidationError):
        VerificationConfig(hash_new_content=False)
    with pytest.raises(ValidationError):
        RepairConfig(retired_instance_grace_hours=167)
    assert RepairConfig(retired_instance_grace_hours=168).retired_instance_grace_hours == 168


def test_rootless_templates_keep_files_nested_sockets_and_worker_ready_service():
    text = (ROOT / "packaging/containers/server.toml.in").read_text()
    data = tomllib.loads(
        text.replace("@ALLOWED_HOSTS@", '["localhost"]').replace(
            "@HOSTNAME@", "archive.example.com"
        )
    )
    validate_server_config_mapping(data)
    assert data["mcp_enabled"] is True
    assert data["listener"]["unix_enabled"] is True
    assert data["listener"]["tcp_enabled"] is False
    assert data["listener"]["unix_socket"] == "/run/hfcache/api/api.sock"
    assert data["verification"]["unix_socket"] == "/run/hfcache/verification/verification.sock"
    assert {name: source["file"] for name, source in data["credentials"].items()} == {
        "writer": "/run/secrets/hfcache.api",
        "reader": "/run/secrets/hfcache.api-reader",
        "mcp_reader": "/run/secrets/hfcache.mcp-reader",
    }
    unit = (ROOT / "packaging/containers/hfcache-api.service").read_text()
    assert "Requires=hfcache-verification.service" in unit
    assert "Requires=hfcache-verification.socket" not in unit


def assert_runtime_facts(text):
    section = text.split("### Selected runtime facts", 1)[1].split("[Containerfile]", 1)[0]
    documented = dict(re.findall(r"^\| ([^|]+?) \| `([^`]+)` \|$", section, re.MULTILINE))
    pins = json.loads((ROOT / "packaging/containers/images.json").read_text())
    settings = tomllib.loads(
        (ROOT / "packaging/containers/server.toml.in")
        .read_text()
        .replace("@ALLOWED_HOSTS@", '["localhost"]')
    )
    worker_unit = (ROOT / "packaging/containers/hfcache-verification.service").read_text()
    socket_unit = (ROOT / "packaging/containers/hfcache-verification.socket").read_text()
    assert documented == {
        "Application/build base": pins["python"].split("@", 1)[0],
        "Caddy base": pins["caddy"].split("@", 1)[0],
        "CA donor": pins["ca_bundle_image"].split("@", 1)[0],
        "Application Python": pins["python_distribution"]["version"],
        "API socket": settings["listener"]["unix_socket"],
        "Private worker socket": settings["verification"]["unix_socket"],
        "Worker service type": re.findall(r"(?m)^Type=(.+)$", worker_unit)[0],
        "Rootless socket manual start": re.findall(r"(?m)^RefuseManualStart=.+$", socket_unit)[0],
    }


def test_documented_base_images_listener_and_readiness_match_actual_artifacts():
    assert_runtime_facts((ROOT / "docs/containers.md").read_text())


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("registry.access.redhat.com/ubi10/ubi-micro", "debian:slim-trixie"),
        ("`/run/hfcache/api/api.sock`", "`/run/hfcache/api.sock`"),
        ("| Worker service type | `notify` |", "| Worker service type | `simple` |"),
    ],
)
def test_obsolete_image_listener_or_readiness_facts_fail(old, new):
    text = (ROOT / "docs/containers.md").read_text()
    with pytest.raises(AssertionError):
        assert_runtime_facts(text.replace(old, new))
