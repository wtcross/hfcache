#!/usr/bin/env bash
#
# Provider-neutral quality gate.
#
# Runs exactly the checks docs/plan.md §8.4 requires, in order, and stops at the
# first failure. There is no CI-provider configuration anywhere in this
# repository on purpose: whatever runs this — a shell, a hook, a pipeline —
# invokes the same script an operator does, so a green pipeline and a green
# workstation mean the same thing.
#
# Usage:
#   scripts/check.sh              # the §8.4 gate
#   scripts/check.sh --with-build # additionally build and smoke-test the wheel
#
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

WITH_BUILD=0
for arg in "$@"; do
  case "$arg" in
    --with-build) WITH_BUILD=1 ;;
    -h | --help)
      sed -n '3,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      printf 'unknown argument: %s\n' "$arg" >&2
      exit 64
      ;;
  esac
done

if ! command -v uv > /dev/null 2>&1; then
  printf 'uv is not on PATH; see README.md\n' >&2
  exit 69
fi

step() {
  printf '\n\033[1m==> %s\033[0m\n' "$*"
}

step 'uv lock --check'
uv lock --check

step 'uv sync --locked --extra server'
uv sync --locked --extra server

step 'ruff format --check'
uv run --locked --extra server ruff format --check .

step 'ruff check'
uv run --locked --extra server ruff check .

step 'pyrefly check'
uv run --locked --extra server pyrefly check

step 'pytest'
uv run --locked --extra server pytest

step 'uv build'
uv build

step 'locked base and server wheel installations'
uv run --locked --extra server python scripts/check-installations.py

# Cockpit plugin gate (docs/cockpit.md §8): frozen install, lint, unit tests,
# and a production build, when cockpit/ and the toolchain are both present.
# The skip is loud so a green gate on a toolchain-less host cannot be mistaken
# for plugin coverage; a CPT package lands only from a host where this stage
# ran (decision 88).
PNPM_BIN="$(command -v pnpm || true)"
if [[ -z $PNPM_BIN && -x "${PNPM_HOME:-$HOME/.local/share/pnpm}/bin/pnpm" ]]; then
  PNPM_BIN="${PNPM_HOME:-$HOME/.local/share/pnpm}/bin/pnpm"
fi
if [[ -d cockpit && -n $PNPM_BIN ]] && command -v make > /dev/null 2>&1; then
  step 'cockpit plugin gate'
  make -C cockpit check PNPM="$PNPM_BIN"
elif [[ -d cockpit ]]; then
  printf '\nNOTE: cockpit/ exists but pnpm or make is missing — plugin gate SKIPPED (docs/cockpit.md §8)\n' >&2
fi

if [[ $WITH_BUILD -eq 1 ]]; then
  step 'wheel install smoke test'
  uv run --locked --extra server pytest -m build
fi

printf '\n\033[1;32mall checks passed\033[0m\n'
