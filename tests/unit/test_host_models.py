"""Decision150 source-schema refusals; no simulated profile is platform acceptance."""

import copy

import pytest
from pydantic import ValidationError

from hfcache.errors import ExitCode, HostAdministrationUnavailableError
from hfcache.host_models import HOST_ACTIONS, HostStatus, unavailable_host_status
from hfcache.server_config import HostHelperConfig
from hfcache.taxonomy import classify
from tests.fixtures.host_examples import host_status


@pytest.mark.parametrize("profile", ["native", "rootless"])
def test_deployment_digest_is_optional_additional_pin_not_self_hashing_template(profile):
    settings = HostHelperConfig(enabled=True, profile=profile, api_host_gid=983)
    assert settings.enabled is True
    assert settings.deployment_sha256 is None
    assert settings.api_host_gid == 983


def test_configuration_only_is_not_archive_permission_or_guard_evidence():
    result = host_status()
    assert result.state == "supported"
    assert result.facts is not None
    assert result.facts.guard == "absent"
    assert result.permissions.configuration is True
    assert not any(
        getattr(result.permissions, x)
        for x in ("archive", "hub", "control", "schedule", "observer")
    )


@pytest.mark.parametrize(
    "reason",
    ["helper-disabled", "helper-unavailable", "helper-timeout", "helper-refused", "helper-busy"],
)
def test_unavailable_has_no_partial_binding_facts_or_permissions(reason):
    result = unavailable_host_status(reason)
    assert result.state == "unavailable"
    assert result.reason == reason
    assert result.profile is result.binding is result.facts is None
    assert not any(result.permissions.model_dump().values())
    assert set(result.permission_reasons.model_dump().values()) == {"helper-unavailable"}


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("schema_version",), True),
        (("schema_version",), "1"),
        (("schema_version",), 2),
        (("profile",), "container"),
        (("state",), "healthy"),
        (("reason",), "policy-missing"),
        (("binding", "source_dirty"), 1),
        (("binding", "archive_root"), "/tmp/archive"),
        (("binding", "archive_id"), "bad"),
        (("binding", "release_version"), "../0.2.2"),
        (("binding", "deployment_sha256"), "A" * 64),
        (("binding", "policy_sha256"), "a" * 63),
        (("permissions", "archive"), 0),
        (("permissions", "configuration"), "true"),
        (("permission_reasons", "configuration"), "policy-denied"),
        (("permission_reasons", "archive"), "granted"),
        (("facts", "guard"), "unknown"),
        (("facts", "archive_mount"), "rw"),
        (("facts", "sync_schedule", "revision"), "e" * 64),
        (("facts", "sync_schedule", "source"), "default"),
        (("facts", "sync_schedule", "on_calendar"), "daily"),
        (("facts", "sync_schedule", "randomized_delay_sec"), "1min"),
    ],
)
def test_contradictory_or_coerced_status_refuses(path, value):
    data = host_status().model_dump(mode="json")
    target = data
    for name in path[:-1]:
        target = target[name]
    target[path[-1]] = value
    with pytest.raises(ValidationError):
        HostStatus.model_validate(data)


@pytest.mark.parametrize("action", ["schedule", "observer"])
def test_rootless_cannot_gain_unproved_system_control(action):
    data = host_status().model_dump(mode="json")
    data["permissions"][action] = True
    data["permission_reasons"][action] = "granted"
    with pytest.raises(ValidationError, match="rootless"):
        HostStatus.model_validate(data)


@pytest.mark.parametrize("missing", ["profile", "binding", "facts"])
def test_supported_cannot_omit_authority(missing):
    data = host_status().model_dump(mode="json")
    data[missing] = None
    with pytest.raises(ValidationError):
        HostStatus.model_validate(data)


@pytest.mark.parametrize("action", HOST_ACTIONS)
def test_unknown_cannot_carry_true_grants(action):
    data = unavailable_host_status().model_dump(mode="json")
    data["state"] = "unknown"
    data["reason"] = "facts-unavailable"
    data["permissions"][action] = True
    data["permission_reasons"][action] = "granted"
    with pytest.raises(ValidationError):
        HostStatus.model_validate(data)


def test_guard_must_be_real_and_always_removes_archive_permission():
    data = host_status().model_dump(mode="json")
    data["state"] = "guarded"
    with pytest.raises(ValidationError):
        HostStatus.model_validate(data)
    data["facts"]["guard"] = "held"
    assert HostStatus.model_validate(data).state == "guarded"
    data["permissions"]["archive"] = True
    data["permission_reasons"]["archive"] = "granted"
    with pytest.raises(ValidationError):
        HostStatus.model_validate(data)


def test_fixed_unit_map_rejects_extra_and_missing_service():
    data = host_status().model_dump(mode="json")
    data["facts"]["units"]["arbitrary.service"] = data["facts"]["units"]["hfcache-sync.service"]
    with pytest.raises(ValidationError):
        HostStatus.model_validate(data)
    del data["facts"]["units"]["arbitrary.service"]
    del data["facts"]["units"]["hfcache-verify.timer"]
    with pytest.raises(ValidationError):
        HostStatus.model_validate(data)


@pytest.mark.parametrize(
    "level", [(), ("binding",), ("permissions",), ("facts",), ("facts", "sync_schedule")]
)
def test_unknown_status_fields_are_not_accepted(level):
    data = host_status().model_dump(mode="json")
    target = data
    for field in level:
        target = target[field]
    target["arbitrary"] = "denied"
    with pytest.raises(ValidationError):
        HostStatus.model_validate(data)


def test_native_fixed_source_schedule_is_observation_not_new_calendar_validation():
    data = host_status().model_dump(mode="json")
    data["profile"] = "native"
    data["facts"]["sync_schedule"] = {
        "state": "observed",
        "reason": None,
        "source": "managed",
        "revision": "f" * 64,
        "on_calendar": "daily",
        "randomized_delay_sec": "15min",
    }
    observed = HostStatus.model_validate(data)
    assert observed.facts is not None
    assert observed.facts.sync_schedule.on_calendar == "daily"
    for replacement in ["daily\nInjected=true", "e" * 4097, "每日"]:
        changed = copy.deepcopy(data)
        changed["facts"]["sync_schedule"]["on_calendar"] = replacement
        with pytest.raises(ValidationError):
            HostStatus.model_validate(changed)


@pytest.mark.parametrize(
    "data",
    [
        {"enabled": True},
        {"enabled": False, "profile": "native"},
        {"enabled": True, "profile": "native", "deployment_sha256": "a" * 64, "api_host_gid": True},
        {"enabled": True, "profile": "native", "deployment_sha256": "x", "api_host_gid": 981},
        {"enabled": True, "profile": "rootless", "deployment_sha256": "a" * 64, "api_host_gid": 0},
        {
            "enabled": True,
            "profile": "native",
            "deployment_sha256": "a" * 64,
            "api_host_gid": 981,
            "socket": "/tmp/other",
        },
    ],
)
def test_helper_opt_in_has_no_partial_or_caller_selected_authority(data):
    with pytest.raises(ValidationError):
        HostHelperConfig.model_validate(data)


def test_helper_unavailable_has_stable_service_failure_taxonomy():
    error = HostAdministrationUnavailableError()
    assert error.status_code == 503
    assert error.exit_code == classify("HFAPI022") == ExitCode.SAFETY
    assert error.problems[0].code == "HFAPI022"
