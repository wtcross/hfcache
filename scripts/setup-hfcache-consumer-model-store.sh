#!/usr/bin/env bash
#
# Prepare a consumer host's local, revisioned model store.
#
# This installs the standard-library copy-and-verify helper, creates a locked
# vLLM service identity, and prepares a root-controlled model namespace. Only
# the revisions directory is writable by vLLM; the eventual current symlink
# remains a root-controlled promotion boundary.
#
# Usage:
#   sudo scripts/setup-hfcache-consumer-model-store.sh
#   sudo scripts/setup-hfcache-consumer-model-store.sh /path/to/copy-revision.py
#
# Defaults:
#   model       unsloth/Qwen3.8-27B-NVFP4
#   store       /var/lib/hfcache-models
#   capacity    100 GiB existing-plus-available space
#   identity    vllm:vllm
#
set -euo pipefail
umask 027

SERVICE_USER=vllm
SERVICE_GROUP=vllm
STORE_ROOT=/var/lib/hfcache-models
MODEL_ID=unsloth/Qwen3.8-27B-NVFP4
MODEL_ROOT=${STORE_ROOT}/${MODEL_ID}
REVISIONS_DIR=${MODEL_ROOT}/revisions
HELPER_DIR=/usr/local/libexec/hfcache
HELPER_DEST=${HELPER_DIR}/copy-revision.py
CAPACITY_BUDGET_BYTES=$((100 * 1024 * 1024 * 1024))
SOURCE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
HELPER_SOURCE=${SOURCE_ROOT}/examples/copy-revision.py

usage() {
  printf '%s\n' \
    'Prepare the local model store on an hfcache consumer.' \
    '' \
    'Usage:' \
    '  sudo setup-hfcache-consumer-model-store.sh [COPY_REVISION_PY]' \
    '' \
    'COPY_REVISION_PY defaults to examples/copy-revision.py beside this' \
    'repository or installed release. Pass it explicitly when the setup' \
    'script and copy helper were transferred to the consumer separately.'
}

die() {
  printf 'setup-hfcache-consumer-model-store: %s\n' "$*" >&2
  exit 1
}

usage_error() {
  printf 'setup-hfcache-consumer-model-store: %s\n' "$*" >&2
  printf 'Try --help for usage.\n' >&2
  exit 64
}

case ${1:-} in
  -h | --help)
    usage
    exit 0
    ;;
  --*) usage_error "unknown option: $1" ;;
  '') ;;
  *)
    HELPER_SOURCE=$1
    shift
    ;;
esac
(( $# == 0 )) || usage_error "unexpected argument: $1"

for command_name in \
  awk chmod chown df dirname du getent groupadd id install python3 readlink \
  sha256sum useradd usermod; do
  command -v "${command_name}" > /dev/null ||
    die "required command not found: ${command_name}"
done

(( EUID == 0 )) || die 'must run as root (for example, with sudo)'
[[ -f ${HELPER_SOURCE} ]] || die "copy helper not found: ${HELPER_SOURCE}"
[[ -r ${HELPER_SOURCE} ]] || die "copy helper is not readable: ${HELPER_SOURCE}"

# Loading --help exercises the helper with the consumer's system Python without
# contacting the archive or the Hub. The helper deliberately has no dependency
# beyond the Python standard library (docs/consumers.md).
python3 "${HELPER_SOURCE}" --help > /dev/null

# Refuse path aliases before changing ownership. A separately mounted filesystem
# at STORE_ROOT is fine; an unexpected symlink is not a model-store boundary.
for path in \
  "${STORE_ROOT}" \
  "${STORE_ROOT}/unsloth" \
  "${MODEL_ROOT}" \
  "${REVISIONS_DIR}"; do
  [[ ! -L ${path} ]] || die "refusing to use symlinked store path: ${path}"
  [[ ! -e ${path} || -d ${path} ]] ||
    die "store path exists and is not a directory: ${path}"
done

# A directory cannot reserve blocks. Check the filesystem before making host
# changes and count an existing model tree toward the 100 GiB budget so reruns
# remain idempotent after a revision has been copied.
CAPACITY_PATH=${STORE_ROOT}
while [[ ! -e ${CAPACITY_PATH} ]]; do
  PARENT=$(dirname "${CAPACITY_PATH}")
  [[ ${PARENT} != "${CAPACITY_PATH}" ]] ||
    die "could not find a filesystem containing ${STORE_ROOT}"
  CAPACITY_PATH=${PARENT}
done

AVAILABLE_BYTES=$(df --block-size=1 --output=avail "${CAPACITY_PATH}" | awk 'NR == 2 { print $1 }')
[[ ${AVAILABLE_BYTES} =~ ^[0-9]+$ ]] || die 'could not determine available storage'

MODEL_BYTES=0
if [[ -d ${MODEL_ROOT} ]]; then
  MODEL_BYTES=$(du --summarize --block-size=1 "${MODEL_ROOT}" | awk '{ print $1 }')
fi
[[ ${MODEL_BYTES} =~ ^[0-9]+$ ]] || die 'could not determine existing model-store usage'

USABLE_BUDGET=$((AVAILABLE_BYTES + MODEL_BYTES))
(( USABLE_BUDGET >= CAPACITY_BUDGET_BYTES )) ||
  die 'model store has less than 100 GiB of existing-plus-available capacity'

if ! getent group "${SERVICE_GROUP}" > /dev/null; then
  groupadd --system "${SERVICE_GROUP}"
fi

NOLOGIN_SHELL=$(command -v nologin 2> /dev/null || printf '/usr/sbin/nologin')
[[ -x ${NOLOGIN_SHELL} ]] || die "nologin shell not found: ${NOLOGIN_SHELL}"

if getent passwd "${SERVICE_USER}" > /dev/null; then
  [[ $(id -u "${SERVICE_USER}") != 0 ]] ||
    die "existing ${SERVICE_USER} account unexpectedly has UID 0"
  [[ $(id -gn "${SERVICE_USER}") == "${SERVICE_GROUP}" ]] ||
    die "existing ${SERVICE_USER} account does not use ${SERVICE_GROUP} as its primary group"
else
  useradd \
    --system \
    --gid "${SERVICE_GROUP}" \
    --home-dir "${STORE_ROOT}" \
    --no-create-home \
    --shell "${NOLOGIN_SHELL}" \
    --comment 'vLLM inference service' \
    "${SERVICE_USER}"
fi

# Password lock plus nologin makes the account service-only. Repeat this on
# every run so the script converges an existing account back to that state.
usermod --lock --shell "${NOLOGIN_SHELL}" "${SERVICE_USER}"

install -d -o root -g root -m 0755 "${HELPER_DIR}"
[[ ! -L ${HELPER_DEST} ]] || die "refusing to replace symlink: ${HELPER_DEST}"

if [[ $(readlink -f "${HELPER_SOURCE}") == "${HELPER_DEST}" ]]; then
  chown root:root "${HELPER_DEST}"
  chmod 0755 "${HELPER_DEST}"
else
  install -o root -g root -m 0755 "${HELPER_SOURCE}" "${HELPER_DEST}"
fi

# vLLM may create only unique revision destinations. Root retains the model
# root so the serving pointer can be switched separately after verification.
install -d -o root -g "${SERVICE_GROUP}" -m 0750 "${STORE_ROOT}"
install -d -o root -g "${SERVICE_GROUP}" -m 0750 "${STORE_ROOT}/unsloth"
install -d -o root -g "${SERVICE_GROUP}" -m 0750 "${MODEL_ROOT}"
install -d -o "${SERVICE_USER}" -g "${SERVICE_GROUP}" -m 0750 "${REVISIONS_DIR}"

printf 'Consumer model store prepared.\n'
printf '  account:    %s:%s (locked, non-login)\n' "${SERVICE_USER}" "${SERVICE_GROUP}"
printf '  helper:     %s\n' "${HELPER_DEST}"
printf '  model root: %s\n' "${MODEL_ROOT}"
printf '  revisions:  %s\n' "${REVISIONS_DIR}"
printf '  free space: %s GiB\n' "$((AVAILABLE_BYTES / 1024 / 1024 / 1024))"
printf '\nFor each copy, generate a new destination that does not already exist:\n'
printf '  slot="$(date -u +%%Y%%m%%dT%%H%%M%%SZ)-$(< /proc/sys/kernel/random/uuid)"\n'
printf '  destination="%s/${slot}"\n' "${REVISIONS_DIR}"
printf 'Never pass the model root or a live/current path as --destination.\n'
