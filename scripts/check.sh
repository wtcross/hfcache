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

step 'ruff format --check'
uv run ruff format --check .

step 'ruff check'
uv run ruff check .

step 'pyrefly check'
uv run pyrefly check

step 'pytest'
uv run pytest

step 'uv build'
uv build

if [[ $WITH_BUILD -eq 1 ]]; then
  step 'wheel install smoke test'
  uv run pytest -m build
fi

printf '\n\033[1;32mall checks passed\033[0m\n'
