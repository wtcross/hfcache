#!/usr/bin/env bash
# Explicit inventory and disposable workloads; see docs/security.md.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
exec python3 "${HERE}/hardening-probe.py" --wrapper "$@"
