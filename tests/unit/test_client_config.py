"""API-011 readers resolve explicit management settings without writer state."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from hfcache import cli, client_config
from hfcache.client_config import ClientConfig, resolve_api_token, resolve_client_config
from hfcache.errors import ConfigurationError

TOKEN = "reader-key-" + "R" * 40
ARCHIVE_ID = "ad7bd2f4-f3f6-4d15-94a5-c468e10c3d18"


def protected(path: Path, token: str = TOKEN) -> Path:
    path.write_text(token + "\n")
    path.chmod(0o600)
    return path


def test_optional_default_and_atomic_endpoint_precedence(tmp_path, monkeypatch):
    default = tmp_path / "client.toml"
    monkeypatch.setattr(client_config, "DEFAULT_CLIENT_CONFIG", default)
    local = resolve_client_config()
    assert local.api_socket == Path("/run/hfcache/api.sock")
    assert local.url == "http://localhost"
    default.write_text('schema_version = 1\napi_socket = "/tmp/configured.sock"\n')
    explicit_url = resolve_client_config(api_url="https://archive.example/cache/")
    assert explicit_url.api_url == "https://archive.example/cache"
    assert explicit_url.api_socket is None
    default.write_text('schema_version = 1\napi_url = "https://archive.example"\n')
    explicit_socket = resolve_client_config(api_socket=tmp_path / "explicit.sock")
    assert explicit_socket.api_url is None
    assert explicit_socket.socket == tmp_path / "explicit.sock"


def test_explicit_missing_or_installed_invalid_settings_never_fall_back(tmp_path, monkeypatch):
    default = tmp_path / "client.toml"
    monkeypatch.setattr(client_config, "DEFAULT_CLIENT_CONFIG", default)
    with pytest.raises(ConfigurationError, match="HFAPI017"):
        resolve_client_config(default)
    default.write_text('schema_version = 1\napi_token = "must-never-appear"\n')
    with pytest.raises(ConfigurationError, match="HFAPI017") as failure:
        resolve_client_config()
    assert "must-never-appear" not in str(failure.value)
    default.unlink()  # This test owns the deliberately invalid settings file.
    default.symlink_to(tmp_path / "missing-target")
    with pytest.raises(ConfigurationError, match="HFAPI017"):
        resolve_client_config()


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"schema_version": True},
        {"schema_version": "1"},
        {"schema_version": 2},
        {"schema_version": 1, "token": TOKEN},
        {"schema_version": 1, "api_url": "http://archive.example"},
        {"schema_version": 1, "api_url": "https://archive .example"},
        {"schema_version": 1, "api_url": "https://archive.example:"},
        {"schema_version": 1, "api_url": "https://user:password@archive.example"},
        {"schema_version": 1, "api_url": "https://archive.example?token=secret"},
        {"schema_version": 1, "api_url": "https://archive.example#secret"},
        {"schema_version": 1, "api_url": "https://archive.example/a/../b"},
        {"schema_version": 1, "api_url": "https://archive.example/%2e%2e"},
        {"schema_version": 1, "api_socket": "relative.sock"},
        {"schema_version": 1, "api_token_file": "/tmp/../credential"},
        {"schema_version": 1, "credential_name": "../hub.token"},
        {"schema_version": 1, "expected_archive_id": ARCHIVE_ID.upper()},
        {"schema_version": 1, "connect_timeout": float("inf")},
        {"schema_version": 1, "read_timeout": float("nan")},
        {"schema_version": 1, "read_retries": True},
        {"schema_version": 1, "poll_interval": 0.0},
        {"schema_version": 1, "wait_timeout": -1.0},
        {"schema_version": 1, "max_response_bytes": 1},
        {"schema_version": 1, "max_pages": 10001},
        {"schema_version": 1, "api_url": "https://archive.example", "api_socket": "/tmp/api"},
    ],
)
def test_strict_client_boundary(settings):
    with pytest.raises(ValidationError):
        ClientConfig.model_validate(settings)


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://[::1]:8000",
        "https://archive.example/prefix",
    ],
)
def test_verified_remote_or_explicit_loopback_urls(url):
    assert ClientConfig(schema_version=1, api_url=url).url == url


def test_token_precedence_and_unusable_selected_source(tmp_path, monkeypatch):
    systemd = tmp_path / "credentials"
    systemd.mkdir()
    protected(systemd / "hfcache.api", "systemd-" + "S" * 40)
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(systemd))
    configured = protected(tmp_path / "configured.token", "configured-" + "C" * 40)
    explicit = protected(tmp_path / "explicit.token")
    settings = tmp_path / "client.toml"
    settings.write_text(f'schema_version = 1\napi_token_file = "{configured}"\n')
    assert resolve_api_token(resolve_client_config(settings, api_token_file=explicit)) == TOKEN
    assert resolve_api_token(resolve_client_config(settings)) == "configured-" + "C" * 40
    assert resolve_api_token(ClientConfig(schema_version=1)) == "systemd-" + "S" * 40
    explicit.chmod(0o644)
    with pytest.raises(ConfigurationError, match="HFAPI003"):
        resolve_api_token(resolve_client_config(settings, api_token_file=explicit))


def test_no_hub_or_ambient_credential_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)
    monkeypatch.setenv("HF_TOKEN", "hf_" + "H" * 40)
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", "hf_" + "H" * 40)
    monkeypatch.setenv("NETRC", str(protected(tmp_path / "netrc")))
    with pytest.raises(ConfigurationError, match="HFAPI003"):
        resolve_api_token(ClientConfig(schema_version=1))
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", "relative")
    with pytest.raises(ConfigurationError, match="HFAPI003"):
        resolve_api_token(ClientConfig(schema_version=1))


def test_credential_symlink_is_refused_without_secret_diagnostics(tmp_path):
    credential = protected(tmp_path / "real.token")
    link = tmp_path / "linked.token"
    link.symlink_to(credential)
    with pytest.raises(ConfigurationError, match="HFAPI003") as failure:
        resolve_api_token(ClientConfig(schema_version=1, api_token_file=link))
    assert TOKEN not in str(failure.value)
    assert TOKEN not in repr(failure.value)


@pytest.mark.parametrize("command", [["--help"], ["--json", "version"]])
def test_help_and_local_version_never_resolve_new_settings(tmp_path, monkeypatch, command):
    def forbidden(*args, **kwargs):
        pytest.fail("local help/version attempted writer or client configuration")

    monkeypatch.setattr(client_config, "resolve_client_config", forbidden)
    monkeypatch.setattr(cli, "load_config", forbidden)
    outcome = CliRunner().invoke(
        cli.app,
        [
            "--client-config",
            str(tmp_path / "missing.toml"),
            "--api-url",
            "invalid",
            "--api-token-file",
            str(tmp_path / "missing.token"),
            *command,
        ],
    )
    assert outcome.exit_code == 0, outcome.output


def test_client_config_fifo_is_refused_without_blocking(tmp_path):
    path = tmp_path / "settings.fifo"
    os.mkfifo(path)
    with pytest.raises(ConfigurationError, match="HFAPI017"):
        resolve_client_config(path)
