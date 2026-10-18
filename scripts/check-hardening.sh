#!/usr/bin/env bash
# Probe actual executors using installed unit/drop-in properties (decision 121).
# This is an operator command; --dry-run with --unit-directory permits fixtures.
# Never infer executor hardening from a scheduled API-client wrapper.
set -euo pipefail

UNIT=hfcache-api.service
UNIT_DIRECTORY=
DRY_RUN=false
ARCHIVE=/srv/hfcache
CREDENTIAL_PROBE=
while (( $# )); do
  case $1 in
    --dry-run) DRY_RUN=true ;;
    --unit-directory) shift; UNIT_DIRECTORY=${1:?missing unit directory} ;;
    --archive-root) shift; ARCHIVE=${1:?missing archive root} ;;
    --credential-probe) shift; CREDENTIAL_PROBE=${1:?missing protected probe file} ;;
    hfcache-api.service|hfcache-verification.service) UNIT=$1 ;;
    *) printf 'check-hardening: use an actual API or verification executor unit\n' >&2; exit 1 ;;
  esac
  shift
done
[[ ${ARCHIVE} == /* && ${ARCHIVE} != / && ${ARCHIVE} != */ && ${ARCHIVE} != *//* &&
   ${ARCHIVE} != *\\* && /${ARCHIVE}/ != */../* && /${ARCHIVE}/ != */./* &&
   ! ${ARCHIVE} =~ [[:cntrl:]] ]] || {
  printf 'check-hardening: archive root must be an absolute non-root path\n' >&2; exit 1;
}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROBE=${HERE}/hardening-probe.py
EXECUTOR=api
[[ ${UNIT} != hfcache-verification.service ]] || EXECUTOR=verification

if ! ${DRY_RUN}; then
  [[ ${EUID} -eq 0 ]] || {
    printf 'check-hardening: must run as root to start a transient unit\n' >&2; exit 1;
  }
  [[ -z ${UNIT_DIRECTORY} ]] || {
    printf 'check-hardening: fixture unit directories are dry-run only\n' >&2; exit 1;
  }
  [[ $(realpath -e -- "${ARCHIVE}") == "${ARCHIVE}" ]] || {
    printf 'check-hardening: archive root must resolve to its canonical path\n' >&2; exit 1;
  }
fi
if [[ -n ${UNIT_DIRECTORY} ]]; then
  CONTENT=$(cat -- "${UNIT_DIRECTORY}/${UNIT}")
else
  # Includes installed drop-ins; do not silently probe only the packaged fragment.
  CONTENT=$(systemctl cat --no-pager "${UNIT}")
fi
[[ -r ${PROBE} ]] || { printf 'check-hardening: probe script is missing\n' >&2; exit 1; }

mapfile -t PROPERTIES < <(
  awk '
    /^\[Service\]/ { inside = 1; next }
    /^\[/          { inside = 0 }
    inside && /^[A-Za-z][A-Za-z0-9]*=/ {
      split($0, parts, "="); key=parts[1]
      # Work and daemon-lifecycle directives cannot be inherited by a oneshot
      # probe. In particular, never acquire production activation descriptors,
      # execute lifecycle hooks, or restart a failed probe automatically.
      if (key ~ /^Exec/ || key == "Type" || key == "Restart" ||
          key == "RestartSec" || key == "Sockets" || key == "WatchdogSec" ||
          key == "PIDFile" || key == "BusName" || key == "NotifyAccess" ||
          key == "RuntimeMaxSec") next
      print $0
    }
  ' <<< "${CONTENT}"
)
(( ${#PROPERTIES[@]} > 0 )) || {
  printf 'check-hardening: no service properties found\n' >&2; exit 1;
}

# Report property names only: a local drop-in must not leak a literal secret via
# this diagnostic, even when that drop-in violates credential conventions.
printf 'executor: %s (%s); %d installed properties\n' "${UNIT}" "${EXECUTOR}" "${#PROPERTIES[@]}"
for property in "${PROPERTIES[@]}"; do printf '  %s\n' "${property%%=*}"; done
if ${DRY_RUN}; then
  printf 'dry run: no transient unit, network, credential or archive probe executed\n'
  exit 0
fi
if [[ ${EXECUTOR} == verification ]]; then
  [[ ${CREDENTIAL_PROBE} == /* && -f ${CREDENTIAL_PROBE} && ! -L ${CREDENTIAL_PROBE} &&
     $(realpath -e -- "${CREDENTIAL_PROBE}") == "${CREDENTIAL_PROBE}" ]] || {
    printf 'check-hardening: verification needs --credential-probe for a known protected source file\n' >&2
    exit 1
  }
fi
ARGUMENTS=(--pipe --wait --collect --quiet --unit "hfcache-hardening-probe-$$"
  --property Type=oneshot)
for property in "${PROPERTIES[@]}"; do ARGUMENTS+=(--property "${property}"); done
ARGUMENTS+=(--property "RequiresMountsFor=${ARCHIVE}"
  --setenv "HFCACHE_PROBE_EXECUTOR=${EXECUTOR}" --setenv "HFCACHE_PROBE_ARCHIVE=${ARCHIVE}")
[[ -z ${CREDENTIAL_PROBE} ]] || ARGUMENTS+=(--setenv "HFCACHE_PROBE_CREDENTIAL=${CREDENTIAL_PROBE}")
systemd-run "${ARGUMENTS[@]}" /opt/hfcache/current/.venv/bin/python "${PROBE}"
