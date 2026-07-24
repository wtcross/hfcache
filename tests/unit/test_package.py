"""The package is importable and reports the version that is installed."""

import os
from pathlib import Path

import hfcache


def test_version_comes_from_installed_metadata():
    assert hfcache.__version__
    assert hfcache.__version__ != "0.0.0+unknown"


def test_ambient_hub_state_is_isolated():
    # Guards the autouse fixture in conftest.py: if this ever fails, tests can
    # silently reuse the host's ~/.cache/huggingface tree or a cached token.
    assert "HF_TOKEN" not in os.environ
    assert "HUGGING_FACE_HUB_TOKEN" not in os.environ
    assert Path(os.environ["HF_HOME"]) != Path.home() / ".cache" / "huggingface"
