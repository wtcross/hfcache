"""Packaged lifecycle separates API observers from actual executors (ADR121)."""

import shlex
import tomllib
from pathlib import Path

import pytest

from hfcache.client_config import ClientConfig
from hfcache.server_config import validate_server_config_mapping

PACKAGING = Path(__file__).parents[2] / "packaging"
UNITS = PACKAGING / "systemd"
EXECUTORS = ("hfcache-api.service", "hfcache-verification.service")
CLIENTS = ("hfcache-sync.service", "hfcache-verify.service")
TOKEN_ENV = {
    "HF_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "HUGGINGFACE_HUB_TOKEN",
    "HUGGINGFACEHUB_API_TOKEN",
    "HF_TOKEN_PATH",
    "HFCACHE_API_TOKEN",
    "HFCACHE_MCP_TOKEN",
}


def fields(name, section):
    """Retain repeated keys: socket activation and credential lists depend on them."""
    selected, result = None, {}
    for raw in (UNITS / name).read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            selected = line[1:-1]
        elif selected == section:
            key, value = line.split("=", 1)
            result.setdefault(key, []).append(value)
    return result


@pytest.mark.parametrize("name", [*EXECUTORS, *CLIENTS])
def test_every_process_keeps_unprivileged_shared_runtime_lifetime_and_hardening(name):
    service = fields(name, "Service")
    assert service["User"] == service["Group"] == ["hfcache"]
    assert service["RuntimeDirectory"] == ["hfcache"]
    assert service["RuntimeDirectoryMode"] == ["0700"]
    assert service["RuntimeDirectoryPreserve"] == ["yes"]
    assert service["CapabilityBoundingSet"] == service["AmbientCapabilities"] == [""]
    for protection in (
        "NoNewPrivileges",
        "PrivateTmp",
        "PrivateDevices",
        "ProtectHome",
        "ProtectKernelTunables",
        "ProtectKernelModules",
        "ProtectKernelLogs",
        "ProtectControlGroups",
        "ProtectClock",
        "ProtectHostname",
        "RestrictNamespaces",
        "LockPersonality",
    ):
        assert service[protection] == ["true"], (name, protection)
    assert service["ProtectSystem"] == ["strict"]
    assert service["ProtectProc"] == ["invisible"]
    assert service["ProcSubset"] == ["pid"]
    assert set(" ".join(service["UnsetEnvironment"]).split()) >= TOKEN_ENV
    assert fields(name, "Unit")["PartOf"] == ["hfcache.target"]
    assert "#OnFailure=hfcache-failure@%n.service" in (UNITS / name).read_text()


@pytest.mark.parametrize("name", EXECUTORS)
def test_real_executors_own_archive_writes_memory_bound_and_instance_lock_parent(name):
    service = fields(name, "Service")
    assert service["ReadWritePaths"] == ["/srv/hfcache"]
    assert service["StateDirectory"] == ["hfcache"]
    assert service["StateDirectoryMode"] == ["0750"]
    assert service["MemoryHigh"] == ["4G"]
    assert "MemoryMax" not in service
    assert "RestrictSUIDSGID" not in service
    assert service["TimeoutStopSec"] == ["infinity"]
    assert fields(name, "Unit")["RequiresMountsFor"] == ["/srv/hfcache"]


def test_one_api_socket_adopts_both_configured_listeners_without_per_connection_workers():
    policy = validate_server_config_mapping(tomllib.loads((PACKAGING / "server.toml").read_text()))
    channel = fields("hfcache-api.socket", "Socket")
    assert channel["ListenStream"] == [str(policy.listener.unix_socket), "127.0.0.1:8787"]
    assert channel["FileDescriptorName"] == ["hfcache-api"]
    assert channel["SocketMode"] == ["0660"]
    assert channel["Accept"] == ["no"]
    assert channel["Service"] == ["hfcache-api.service"]
    assert fields("hfcache-api.service", "Service")["Sockets"] == ["hfcache-api.socket"]
    unit = fields("hfcache-api.service", "Unit")
    assert "hfcache-verification.service" in " ".join(unit["After"]).split()
    assert "hfcache-verification.service" not in " ".join(unit["Wants"] + unit["Requires"]).split()


@pytest.mark.parametrize("name", ["hfcache-api.socket", "hfcache-verification.socket"])
def test_socket_units_require_private_tmpfiles_parent_and_never_remove_listener_paths(name):
    unit, channel = fields(name, "Unit"), fields(name, "Socket")
    assert unit["Requires"] == unit["After"] == ["systemd-tmpfiles-setup.service"]
    assert unit["AssertPathIsDirectory"] == ["/run/hfcache"]
    assert channel["SocketUser"] == channel["SocketGroup"] == ["hfcache"]
    assert channel["DirectoryMode"] == ["0700"]
    assert channel["RemoveOnStop"] == ["no"]
    assert fields(name, "Install")["WantedBy"] == ["hfcache.target"]
    assert (
        "d /run/hfcache 0700 hfcache hfcache -"
        in (PACKAGING / "tmpfiles.d/hfcache.conf").read_text()
    )


def test_private_worker_has_no_credentials_and_hides_same_uid_sources_and_cached_tokens():
    worker = fields("hfcache-verification.service", "Service")
    assert not {key for key in worker if "Credential" in key}
    assert TOKEN_ENV | {"CREDENTIALS_DIRECTORY"} <= set(
        " ".join(worker["UnsetEnvironment"]).split()
    )
    hidden = set(" ".join(worker["InaccessiblePaths"]).split())
    assert {
        "-/run/credentials",
        "-/etc/credstore",
        "-/etc/credstore.encrypted",
        "-/etc/hfcache/credentials",
        "-/var/lib/hfcache/hf-home",
    } <= hidden
    environment = dict(value.split("=", 1) for value in worker["Environment"])
    assert environment["HF_HUB_OFFLINE"] == environment["HF_DATASETS_OFFLINE"] == "1"
    assert environment["HF_HUB_DISABLE_TELEMETRY"] == "1"
    assert environment["HF_HOME"] == "/var/lib/hfcache/verification-hf-home"
    assert environment["HF_XET_CACHE"] == "/var/cache/hfcache-verification/xet"
    assert worker["IPAddressDeny"] == ["any"]
    assert "PrivateNetwork" not in worker
    command = shlex.split(worker["ExecStart"][0])
    assert command[:3] == [
        "/opt/hfcache/current/.venv/bin/python",
        "-m",
        "hfcache.verification_worker",
    ]
    assert command[-2:] == ["--api-user", "hfcache"]
    assert not any("%U" in value or "%u" in value for value in command)
    channel = fields("hfcache-verification.socket", "Socket")
    assert channel["ListenStream"] == ["/run/hfcache/verification.sock"]
    assert channel["FileDescriptorName"] == ["hfcache-verification"]
    assert channel["SocketMode"] == ["0600"]
    assert channel["Accept"] == ["no"]


@pytest.mark.parametrize(
    ("name", "command", "directory"),
    [
        ("hfcache-sync.service", "sync", "sync"),
        ("hfcache-verify.service", "verify-full", "verify"),
    ],
)
def test_scheduled_names_are_unlimited_oneshots_with_fixed_api_only_observers(
    name, command, directory
):
    service = fields(name, "Service")
    invocation = shlex.split(service["ExecStart"][0])
    assert invocation == [
        "/opt/hfcache/current/.venv/bin/python",
        "-m",
        "hfcache.scheduled_client",
        "--client-config",
        "/etc/hfcache/scheduled-client.toml",
        "--state-directory",
        f"/var/lib/hfcache/scheduled/{directory}",
        command,
    ]
    assert service["Type"] == ["oneshot"]
    assert service["TimeoutStartSec"] == ["infinity"]
    assert service["StateDirectory"] == [f"hfcache/scheduled/{directory}"]
    assert service["StateDirectoryMode"] == ["0700"]
    assert service["IPAddressDeny"] == ["any"]
    assert service["RestrictAddressFamilies"] == ["AF_UNIX"]
    assert "ReadWritePaths" not in service
    assert "-/srv/hfcache" in " ".join(service["InaccessiblePaths"]).split()
    assert not any("HF_HOME=" in value for value in service.get("Environment", []))
    assert service["LoadCredentialEncrypted"] == [
        "hfcache.api:/etc/credstore.encrypted/hfcache.api"
    ]
    assert "ImportCredential" not in service


def test_api_alone_imports_hub_token_and_uses_the_same_name_bound_writer_credential():
    api = fields("hfcache-api.service", "Service")
    assert api["ImportCredential"] == ["hf-token"]
    assert api["LoadCredentialEncrypted"] == ["hfcache.api:/etc/credstore.encrypted/hfcache.api"]
    policy = tomllib.loads((PACKAGING / "server.toml").read_text())
    assert policy["credentials"] == {"writer": {"systemd_name": "hfcache.api"}}
    client = ClientConfig.model_validate(
        tomllib.loads((PACKAGING / "scheduled-client.example.toml").read_text())
    )
    assert client.credential_name == "hfcache.api"
    assert client.api_socket == Path("/run/hfcache/api.sock")
    assert client.expected_archive_id is not None
    assert client.api_token_file is None
    legacy = fields("hfcache-sync.service.d/credential.conf.example", "Service")
    assert legacy["ImportCredential"] == [""]


def test_timer_calendars_target_and_disabled_verify_contract_are_preserved():
    sync, verify = fields("hfcache-sync.timer", "Timer"), fields("hfcache-verify.timer", "Timer")
    assert sync["OnCalendar"] == ["*-*-* 02:00:00"]
    assert sync["RandomizedDelaySec"] == ["30m"]
    assert sync["AccuracySec"] == ["1m"]
    assert verify["OnCalendar"] == ["Wed *-01,04,07,10-01..07 04:00:00"]
    assert verify["RandomizedDelaySec"] == ["2h"]
    assert sync["Persistent"] == verify["Persistent"] == ["true"]
    assert fields("hfcache.target", "Unit")["Wants"] == ["srv-hfcache.automount"]
    assert "left disabled" in (UNITS / "hfcache-verify.timer").read_text()
