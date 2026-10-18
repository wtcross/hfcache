#!/usr/bin/env bash
#
# Install a versioned hfcache release and switch to it atomically.
#
# This is plan §21.4 executed rather than described, and it is the mechanism plan
# §30's upgrade step 3 (install into a separate release directory) and step 6
# (atomically switch the current application symlink) refer to. Rollback is the
# same tool with --switch, because a rollback that uses a different procedure
# than the install is a procedure nobody has tested.
#
# Nothing here is invoked from systemd. `uv sync` runs at deployment time, so a
# scheduled run never resolves dependencies, never writes to a release tree, and
# never needs network access for anything but the Hub.
#
# Usage:
#   sudo scripts/install-release.sh                 # build and switch
#   sudo scripts/install-release.sh --no-switch     # stage only, leave `current`
#   sudo scripts/install-release.sh --with-mcp      # include optional MCP transport
#   sudo scripts/install-release.sh --switch 0.1.0  # point `current` at a release
#   scripts/install-release.sh --list               # what is installed, and what is live
#   scripts/install-release.sh --dry-run            # review only; no writes or service calls
#
# Environment overrides, for deployments that move a default deliberately:
#   HFCACHE_PREFIX       install prefix                (default /opt/hfcache)
#   HFCACHE_SOURCE       source tree to stage          (default: this checkout)
#   HFCACHE_UV           absolute path to uv           (default: search PATH, then well-known locations)
#   HFCACHE_UV_VERSION   uv version to accept          (default: the pinned version below)
#
set -euo pipefail

PREFIX=${HFCACHE_PREFIX:-/opt/hfcache}
SOURCE=${HFCACHE_SOURCE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
# Shared with disposable upgrade/rollback fixtures, never sourced from an installed
# application or the archive. This library performs no work merely by loading it.
SCRIPT_DIRECTORY=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "${SCRIPT_DIRECTORY}/release-functions.sh"

# Pinned, because a deployment tool that silently accepts whatever resolver
# happens to be installed is not a deployment tool (plan §21.4). Override
# deliberately, in the environment, when the pin is being moved on purpose.
REQUIRED_UV_VERSION=${HFCACHE_UV_VERSION:-0.11.32}

# The interpreter the service runs. It must not come from a home directory: the
# hardened unit sets ProtectHome=true (plan §22.5), so a venv whose `home` points
# under /home starts on a workstation and fails as a service. CentOS Stream 10
# ships 3.12 and EPEL reaches 3.13, so 3.14 is a uv-managed build installed into
# a root-owned system location and pinned there.
PYTHON_VERSION=$(cat "${SOURCE}/.python-version")
export UV_PYTHON_INSTALL_DIR="${PREFIX}/python"

# What a release tree contains. Enough to build the venv, deploy the units, and
# read the documentation on the host — and nothing that only the repository needs.
RELEASE_CONTENT=(
  .python-version
  LICENSE
  README.md
  docs
  examples
  packaging
  pyproject.toml
  scripts
  src
  uv.lock
)

DIRECTORY_MODE=0755
FILE_MODE=0644

step() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
die() {
  printf 'install-release: %s\n' "$*" >&2
  exit 1
}

uv_binary() {
  # Resolvable as the invoking user or as the operator who owns the toolchain;
  # sudo strips PATH, and uv is a user install on this host (plan §35.1).
  if [[ -n ${HFCACHE_UV:-} ]]; then
    printf '%s\n' "${HFCACHE_UV}"
    return
  fi
  local candidate
  for candidate in "$(command -v uv 2> /dev/null || true)" \
    /usr/local/bin/uv /usr/bin/uv "${SUDO_USER:+/home/${SUDO_USER}/.local/bin/uv}"; do
    [[ -n ${candidate} && -x ${candidate} ]] && {
      printf '%s\n' "${candidate}"
      return
    }
  done
  die 'uv is not on PATH; set HFCACHE_UV to its absolute path'
}

release_version() {
  # From the source tree's own metadata, so the directory name and the version
  # the CLI reports cannot disagree.
  sed -n 's/^version = "\(.*\)"$/\1/p' "${SOURCE}/pyproject.toml" | head -1
}

smoke() (
  # The release's own entry point, run from the release's own environment. A
  # release that cannot report its version is not one to switch to.
  local binary=$1
  "${binary}" --help > /dev/null
  "${binary}" version
  "${binary}" --json version > /dev/null
  "$(dirname "${binary}")/python" -I -c \
    'import fastapi, uvicorn, hfcache.server, hfcache.verification_worker, hfcache.scheduled_client'
  if ${WITH_MCP:-false}; then
    "$(dirname "${binary}")/python" -I -c \
      'import hfcache.mcp; from fastmcp.server.auth import TokenVerifier, AccessToken'
  fi
  local scratch
  scratch=$(mktemp -d)
  trap 'rm -rf -- "${scratch}"' EXIT
  printf 'schema_version=1\n[storage]\narchive_root="%s/archive"\narchive_id="00000000-0000-0000-0000-000000000001"\n[hub]\ntoken_mode="disabled"\n' \
    "${scratch}" > "${scratch}/config.toml"
  "${binary}" --config "${scratch}/config.toml" config validate --local > /dev/null
  local archive_config=${HFCACHE_ARCHIVE_CONFIG:-/etc/hfcache/config.toml}
  if [[ -r ${archive_config} ]]; then
    step 'installed archive policy syntax and constraints'
    # Build/stage needs neither API nor Hub secrets. The real daemon owns
    # credential validation and archive proof; required Hub mode is valid here.
    "$(dirname "${binary}")/python" -I - "${archive_config}" <<'PY'
import sys
from pathlib import Path
from hfcache.config import load_config
from hfcache.errors import HfcacheError

try:
    load_config(Path(sys.argv[1]))
except HfcacheError as error:
    sys.stderr.write("install-release: archive policy rejected; use explicit local validation for details\n")
    raise SystemExit(int(error.exit_code)) from None
PY
  else
    printf 'no archive policy available; installed synthetic --local smoke passed\n'
  fi
)

MODE=install
SWITCH_TARGET=
DRY_RUN=false
WITH_MCP=false
for argument in "$@"; do
  case "${argument}" in
    --no-switch) MODE=stage ;;
    --list) MODE=list ;;
    --dry-run) DRY_RUN=true ;;
    --with-mcp) WITH_MCP=true ;;
    --switch)
      MODE=switch
      SWITCH_TARGET=pending
      ;;
    -h | --help)
      sed -n '3,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      [[ ${SWITCH_TARGET} == pending ]] || die "unknown argument: ${argument}"
      SWITCH_TARGET=${argument}
      ;;
  esac
done
[[ ${SWITCH_TARGET} == pending ]] && die '--switch requires a version'
canonical_absolute_path "${PREFIX}" || die 'unsafe install prefix'
[[ -z ${SWITCH_TARGET} ]] || valid_release_version "${SWITCH_TARGET}"
if ${WITH_MCP} && [[ ${MODE} == switch || ${MODE} == list ]]; then
  die '--with-mcp applies only when building or staging a release'
fi
RELEASE_EXTRAS=(--extra server)
if ${WITH_MCP}; then
  RELEASE_EXTRAS+=(--extra mcp)
fi

if ${DRY_RUN}; then
  printf 'mode: %s\nprefix: %s\nsource: %s\n' "${MODE}" "${PREFIX}" "${SOURCE}"
  if ${WITH_MCP}; then
    printf 'dependency profile: locked server and mcp extras; no dev or editable install\n'
  else
    printf 'dependency profile: locked server extra; no dev or editable install\n'
  fi
  printf 'smoke: installed help/version/server imports, synthetic validate --local and policy parsing\n'
  printf 'switch/rebuild guard: timers, clients, API/verification sockets and executors inactive\n'
  printf 'orphan guard: noncreating exclusive shared-lock check retained through switch\n'
  printf 'archive operations: none; no service stop/start or timer activation\n'
  [[ -z ${SWITCH_TARGET} ]] || printf 'switch target: %s\n' "${SWITCH_TARGET}"
  exit 0
fi

if [[ ${MODE} == list ]]; then
  printf 'prefix:  %s\n' "${PREFIX}"
  printf 'current: %s\n' "$(readlink "${PREFIX}/current" 2> /dev/null || printf 'not set')"
  printf 'releases:\n'
  installed_releases | sed 's/^/  /'
  exit 0
fi

[[ ${EUID} -eq 0 ]] || die "must run as root to write ${PREFIX}"

if [[ ${MODE} == switch ]]; then
  require_quiescent
  switch_to "${SWITCH_TARGET}"
  exit 0
fi

VERSION=$(release_version)
[[ -n ${VERSION} ]] || die "could not read the version from ${SOURCE}/pyproject.toml"
valid_release_version "${VERSION}"
if [[ ${MODE} == install ]] || \
  [[ $(readlink "${PREFIX}/current" 2>/dev/null) == "releases/${VERSION}" ]]; then
  require_quiescent
fi
RELEASE="${PREFIX}/releases/${VERSION}"
UV=$(uv_binary)

step "uv ${REQUIRED_UV_VERSION}"
FOUND=$("${UV}" --version | awk '{print $2}')
[[ ${FOUND} == "${REQUIRED_UV_VERSION}" ]] ||
  die "uv ${FOUND} is installed but this release pins ${REQUIRED_UV_VERSION} (${UV})"
printf '%s\n' "${UV}"

step "CPython ${PYTHON_VERSION} under ${UV_PYTHON_INSTALL_DIR}"
install -d -m "${DIRECTORY_MODE}" -o root -g root "${UV_PYTHON_INSTALL_DIR}"
# Idempotent: uv reuses a matching interpreter already in the install directory
# and downloads one only when there is none. The download is verified by uv
# against the python-build-standalone release metadata.
"${UV}" python install "${PYTHON_VERSION}"
# `--managed-python --system` so the answer is the interpreter installed above
# rather than whatever virtual environment the invoking directory happens to hold
# — running this from the source checkout would otherwise resolve its own .venv.
INTERPRETER=$("${UV}" python find --managed-python --system "${PYTHON_VERSION}")
case "${INTERPRETER}" in
  "${UV_PYTHON_INSTALL_DIR}"/*) : ;;
  *) die "uv resolved ${INTERPRETER}, which is outside ${UV_PYTHON_INSTALL_DIR}" ;;
esac
printf '%s\n' "${INTERPRETER}"

step "release tree ${RELEASE}"
# The *sources* are staged and renamed in, so a copy interrupted half way never
# becomes a release directory. The **environment is built in its final path**,
# which is not a choice: a venv records absolute paths in `pyvenv.cfg` and in
# every console-script shebang, so one built elsewhere and moved is a venv whose
# interpreter does not exist. What guards a failed build instead is `switch_to`,
# which refuses a release with no `.venv/bin/hfcache` — an incomplete release can
# be left behind, but it can never become live.
STAGING="${PREFIX}/releases/.${VERSION}.$$"
RESTORE=
cleanup() {
  rm -rf "${STAGING}"
  # A same-version rebuild moved the old tree aside. Put it back, so a failed
  # build leaves the release that was there rather than nothing at all.
  [[ -n ${RESTORE} && -d ${RESTORE} ]] && {
    rm -rf "${RELEASE}"
    mv -T "${RESTORE}" "${RELEASE}"
  }
  return 0
}
trap cleanup EXIT
install -d -m "${DIRECTORY_MODE}" -o root -g root "${PREFIX}/releases" "${STAGING}"
for item in "${RELEASE_CONTENT[@]}"; do
  [[ -e "${SOURCE}/${item}" ]] || die "the source tree has no ${item}"
  cp -R "${SOURCE}/${item}" "${STAGING}/"
done

if [[ -d ${RELEASE} ]]; then
  # Reinstalling a version that is already installed. `current` is a symlink to
  # the release *name*, so it dangles while this runs — which is why plan §30's
  # upgrade stops `hfcache.target` and waits for active jobs before step 3.
  if [[ $(readlink "${PREFIX}/current" 2> /dev/null) == "releases/${VERSION}" ]]; then
    printf 'rebuilding quiesced release %s; runtime lock retained\n' "${VERSION}" >&2
  fi
  RESTORE="${RELEASE}.replaced.$$"
  mv -T "${RELEASE}" "${RESTORE}"
fi
mv -T "${STAGING}" "${RELEASE}"
STAGING=

step "uv sync --frozen ${RELEASE_EXTRAS[*]} --no-dev --no-editable"
# `--no-editable` so the installed package is a built wheel rather than a path
# reference: nothing at runtime reads `src/`, and the venv keeps working if the
# release tree's sources are later made unreadable.
# `--no-python-downloads` so this step can only use the interpreter pinned above.
(
  cd "${RELEASE}"
  "${UV}" sync --frozen "${RELEASE_EXTRAS[@]}" --no-dev --no-editable --no-python-downloads \
    --python "${PYTHON_VERSION}"
)

step 'ownership and modes'
# Root-owned and read-only to the service identity (plan §21.4): the account that
# runs the archive cannot modify the code that runs it, so a compromise of the
# service cannot become a persistent change to the application.
chown -R root:root "${RELEASE}"
chmod -R u=rwX,go=rX "${RELEASE}"
find "${RELEASE}" -type d -exec chmod "${DIRECTORY_MODE}" {} +
find "${RELEASE}" -type f ! -perm -u=x -exec chmod "${FILE_MODE}" {} +

# The interpreter directory is outside ${RELEASE} and is not rebuilt per release,
# so the sweep above never reaches it. `uv python install` leaves its own lock
# file at 0666 (`REL-002`), which is a world-writable regular file inside a
# prefix plan §21.4 requires be root-owned and read-only to everything else.
# Nothing is lost by narrowing it: every caller of `uv python install` here is
# root, and root ignores the write bit.
find "${UV_PYTHON_INSTALL_DIR}" -maxdepth 1 -type f -perm -o+w \
  -exec chmod "${FILE_MODE}" {} + 2> /dev/null || true

step 'smoke checks'
smoke "${RELEASE}/.venv/bin/hfcache"

# Everything the new release needed is durable; the old tree is no longer a
# fallback and the trap must not restore it.
[[ -n ${RESTORE} ]] && rm -rf "${RESTORE}"
RESTORE=
trap - EXIT

if [[ -x /usr/sbin/restorecon ]]; then
  step 'restorecon'
  # `-F` as well as `-R`: without it restorecon leaves the SELinux *user* part
  # alone, and a tree root created at a shell carries `unconfined_u` rather than
  # the `system_u` a system-installed file should have. The type is what the
  # targeted policy enforces on, so this is consistency rather than a fix — but an
  # inconsistent label is one more thing an operator reading an AVC has to rule
  # out. Reported and not fatal: a release that is built and smoke-tested is still
  # a good release on a host with SELinux disabled.
  /usr/sbin/restorecon -RF "${PREFIX}" || printf 'restorecon reported a problem\n' >&2
fi

if [[ ${MODE} == stage ]]; then
  step 'staged'
  printf 'release %s is installed; `current` is unchanged\n' "${VERSION}"
  exit 0
fi

step 'switch'
switch_to "${VERSION}"

printf '\n\033[1;32mrelease %s is live at %s/current\033[0m\n' "${VERSION}" "${PREFIX}"
printf 'retained releases:\n'
installed_releases | sed 's/^/  /'
