#!/usr/bin/env bash
#
# Test the deployed §22.5 hardening instead of assuming it.
#
# Runs scripts/hardening-probe.py in a transient unit carrying the *installed*
# hfcache-sync.service's `[Service]` properties, read out of the unit file at run
# time. That is the whole point: a probe that restated the settings would pass
# while the deployed unit drifted away from it.
#
# Re-run this after any change to the unit's hardening, and after a
# huggingface_hub, hf_xet, or Python upgrade — a sandbox is a statement about
# which syscalls and paths a dependency needs, and dependencies change.
#
# Usage:
#   sudo scripts/check-hardening.sh                       # the sync unit's hardening
#   sudo scripts/check-hardening.sh hfcache-verify.service
#
set -euo pipefail

UNIT=${1:-hfcache-sync.service}
UNIT_PATH=/etc/systemd/system/${UNIT}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROBE=${HERE}/hardening-probe.py

[[ ${EUID} -eq 0 ]] || {
  printf 'check-hardening: must run as root to start a transient unit\n' >&2
  exit 1
}
[[ -r ${UNIT_PATH} ]] || {
  printf 'check-hardening: %s is not installed\n' "${UNIT_PATH}" >&2
  exit 1
}
[[ -r ${PROBE} ]] || {
  printf 'check-hardening: %s is missing\n' "${PROBE}" >&2
  exit 1
}

# Every `[Service]` property except the ones that name the work. `ExecStart` is
# replaced by the probe; `Type` and the two `TimeoutStartSec`/`Environment` lines
# are kept, because the environment is part of what is being tested and a oneshot
# is what runs in production.
mapfile -t PROPERTIES < <(
  awk '
    /^\[Service\]/ { inside = 1; next }
    /^\[/          { inside = 0 }
    inside && /^[A-Za-z][A-Za-z0-9]*=/ {
      split($0, parts, "=")
      if (parts[1] == "ExecStart" || parts[1] == "Type") next
      print $0
    }
  ' "${UNIT_PATH}"
)

(( ${#PROPERTIES[@]} > 0 )) || {
  printf 'check-hardening: no [Service] properties found in %s\n' "${UNIT_PATH}" >&2
  exit 1
}

printf '\033[1m==> %s: %d properties under test\033[0m\n' "${UNIT}" "${#PROPERTIES[@]}"
printf '  %s\n' "${PROPERTIES[@]}"

ARGUMENTS=(--pipe --wait --collect --quiet --unit "hfcache-hardening-probe-$$")
for property in "${PROPERTIES[@]}"; do
  ARGUMENTS+=(--property "${property}")
done
# The probe reads the archive through the same mount boundary the real unit does.
ARGUMENTS+=(--property RequiresMountsFor=/srv/hfcache)

printf '\n\033[1m==> probe\033[0m\n'
systemd-run "${ARGUMENTS[@]}" \
  /opt/hfcache/current/.venv/bin/python "${PROBE}"
