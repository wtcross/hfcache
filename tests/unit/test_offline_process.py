"""Offline policy is initialized before Hub imports in an isolated process."""

import os
import subprocess
import sys

import pytest

from hfcache.offline import OFFLINE_VARIABLE


@pytest.mark.parametrize("previous", [None, "0", "1"])
def test_offline_initialization_is_permanent_in_child_and_never_changes_parent(previous):
    environment = dict(os.environ)
    if previous is None:
        environment.pop(OFFLINE_VARIABLE, None)
    else:
        environment[OFFLINE_VARIABLE] = previous
    parent_before = os.environ.get(OFFLINE_VARIABLE)
    program = """
import os
from hfcache.offline import initialize_offline_process
initialize_offline_process()
initialize_offline_process()
from huggingface_hub import constants
assert os.environ["HF_HUB_OFFLINE"] == "1"
assert constants.HF_HUB_OFFLINE
"""
    result = subprocess.run(
        [sys.executable, "-c", program],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert os.environ.get(OFFLINE_VARIABLE) == parent_before
