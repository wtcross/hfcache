"""Offline initialization for a dedicated verification process (INV-015).

The future private executor calls this once before importing Hub libraries or
accepting work. Shared services never change process-wide networking flags;
the installed executor's systemd sandbox must separately deny IP sockets.
"""

import os

OFFLINE_VARIABLE = "HF_HUB_OFFLINE"


def initialize_offline_process() -> None:
    """Set the library offline switch once at isolated-process startup, permanently."""
    os.environ[OFFLINE_VARIABLE] = "1"
