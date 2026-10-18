"""Shared pytest configuration.

The autouse fixture here is a correctness control, not a convenience. The
writer host carries an ambient `~/.cache/huggingface` tree and may carry a
cached token; either could make a test pass by reusing state the application
under test never fetched. `docs/security.md` T-07 requires that ambient
Hugging Face discovery never influence behaviour, so the test suite proves it
by removing that state from every test's environment.
"""

from typing import TYPE_CHECKING

import pytest

from hfcache.redaction import clear_registered_secrets

if TYPE_CHECKING:
    from pathlib import Path

_AMBIENT_HUB_VARS = (
    # systemd sets this for any unit with LoadCredential=. The suite must never
    # read a real credential installed on the writer host, so it is removed here
    # and every credential test supplies its own directory explicitly.
    "CREDENTIALS_DIRECTORY",
    "HF_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "HUGGINGFACE_HUB_TOKEN",
    "HF_HOME",
    "HF_HUB_CACHE",
    "HUGGINGFACE_HUB_CACHE",
    "HF_XET_CACHE",
    "HF_ENDPOINT",
    "HF_HUB_OFFLINE",
)


@pytest.fixture(autouse=True)
def _isolate_registered_secrets():
    """Known credential values are process-local configuration, isolated per test."""
    clear_registered_secrets()
    yield
    clear_registered_secrets()


@pytest.fixture(scope="session")
def isolated_hub_home(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A throwaway HF_HOME shared by the session, never the user's."""
    return tmp_path_factory.mktemp("hf-home")


@pytest.fixture(autouse=True)
def _isolate_hub_environment(monkeypatch: pytest.MonkeyPatch, isolated_hub_home: Path) -> None:
    """Remove ambient Hugging Face state from every test's environment.

    `monkeypatch` restores everything at teardown, so no cleanup is needed here.
    """
    for name in _AMBIENT_HUB_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HF_HOME", str(isolated_hub_home))
    monkeypatch.setenv("HF_HUB_CACHE", str(isolated_hub_home / "hub"))
    monkeypatch.setenv("HF_XET_CACHE", str(isolated_hub_home / "xet"))
