#!/usr/bin/env bash
#
# Provider-neutral quality gate.
#
# Runs exactly the checks docs/development.md quality gate requires, in order, and stops at the
# first failure. There is no CI-provider configuration anywhere in this
# repository on purpose: whatever runs this — a shell, a hook, a pipeline —
# invokes the same script an operator does, so a green pipeline and a green
# workstation mean the same thing.
#
# Usage:
#   scripts/check.sh              # the §8.4 gate
#   scripts/check.sh --with-build # additionally build and smoke-test the wheel
#   scripts/check.sh --require-web # strict web, generated contracts and real API read fixture
#   scripts/check.sh --with-web-functional # final installed shared-Caddy acceptance
#
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

WITH_BUILD=0
REQUIRE_WEB=0
WITH_WEB_FUNCTIONAL=0
for arg in "$@"; do
  case "$arg" in
    --with-build) WITH_BUILD=1 ;;
    --require-web) REQUIRE_WEB=1 ;;
    --with-web-functional) WITH_WEB_FUNCTIONAL=1; REQUIRE_WEB=1 ;;
    -h | --help)
      printf '%s\n' \
        'Usage: scripts/check.sh [--with-build] [--require-web] [--with-web-functional]' \
        '  --with-build       additionally smoke-test the installed wheel' \
        '  --require-web      require frozen web/contracts, source browser workflows and real API read fixture' \
        '  --with-web-functional require all installed shared-Caddy functional cases in all profiles' \
        '                       requires explicit HFCACHE_WEB_FUNCTIONAL_MANIFEST; implies --require-web' \
        '  -h, --help         show this help without running checks' \
        'See docs/development.md for provisioning and acceptance limits.'
      exit 0
      ;;
    *)
      printf 'unknown argument: %s\n' "$arg" >&2
      exit 64
      ;;
  esac
done

find_pnpm() {
  PNPM_BIN="$(command -v pnpm || true)"
  if [[ -z $PNPM_BIN && -x "${PNPM_HOME:-$HOME/.local/share/pnpm}/bin/pnpm" ]]; then
    PNPM_BIN="${PNPM_HOME:-$HOME/.local/share/pnpm}/bin/pnpm"
  fi
}

require_web() {
  find_pnpm
  local required
  for required in web/package.json web/pnpm-lock.yaml web/tsconfig.json \
    web/src/wire/contracts.json web/src/wire/generated.ts web/src/wire/unicode-data.json \
    web/scripts/generate-wire.ts web/scripts/check-library-zoom.ts \
    web/scripts/check-auth-sandbox-tests.ts web/test/auth-api/sandbox.test.mjs \
    web/scripts/check-functional-driver-tests.ts web/test/functional-api/driver.test.mjs \
    web/test/auth-api/sandbox.mjs \
    scripts/export-web-contracts.py scripts/check-web-read-fixture.py; do
    if [[ ! -f $required ]]; then
      printf 'Web gate required: missing %s; see docs/development.md\n' "$required" >&2
      exit 69
    fi
  done
  if [[ -z $PNPM_BIN ]] || ! command -v node > /dev/null 2>&1; then
    printf 'Web gate required: node and pnpm must be available; see docs/development.md\n' >&2
    exit 69
  fi
}

if [[ $REQUIRE_WEB -eq 1 ]]; then
  require_web
fi
if [[ $WITH_WEB_FUNCTIONAL -eq 1 ]]; then
  if [[ -z ${HFCACHE_WEB_FUNCTIONAL_MANIFEST:-} || $HFCACHE_WEB_FUNCTIONAL_MANIFEST != /* || ! -f scripts/check-web-functional.py ]]; then
    printf 'Web functional gate requires an explicit absolute HFCACHE_WEB_FUNCTIONAL_MANIFEST and scripts/check-web-functional.py; see docs/development.md\n' >&2
    exit 69
  fi
fi

if ! command -v uv > /dev/null 2>&1; then
  printf 'uv is not on PATH; see README.md\n' >&2
  exit 69
fi

step() {
  printf '\n\033[1m==> %s\033[0m\n' "$*"
}

step 'uv lock --check'
uv lock --check

step 'uv sync --locked --extra server --extra mcp'
uv sync --locked --extra server --extra mcp

if [[ $REQUIRE_WEB -eq 1 ]]; then
  step 'authoritative browser contract export drift'
  uv run --locked --extra server --extra mcp python scripts/export-web-contracts.py --check
fi

step 'ruff format --check'
uv run --locked --extra server --extra mcp ruff format --check .

step 'ruff check'
uv run --locked --extra server --extra mcp ruff check .

step 'pyrefly check'
uv run --locked --extra server --extra mcp pyrefly check

step 'documentation alignment'
uv run --locked --extra server --extra mcp python scripts/check-docs.py

step 'pytest'
uv run --locked --extra server --extra mcp pytest

step 'uv build'
uv build

step 'locked base, server and server-plus-MCP wheel installations'
uv run --locked --extra server --extra mcp python scripts/check-installations.py

if [[ $REQUIRE_WEB -eq 1 ]]; then
  require_web
  step 'web frozen install'
  "$PNPM_BIN" --dir web install --frozen-lockfile
  for web_check in check:wire lint typecheck test:strict-fixtures test:auth-sandbox test:functional-metadata test:unit test:component build test:browser test:library-zoom; do
    step "web $web_check"
    "$PNPM_BIN" --dir web run "$web_check"
  done
  step 'real API React read fixture'
  uv run --locked --extra server --extra mcp python scripts/check-web-read-fixture.py
elif [[ -d web ]]; then
  printf '\nNOTE: web/ exists but its gate is OMITTED; use --require-web. This run does not establish web UI acceptance (docs/development.md).\n' >&2
fi

if [[ $WITH_BUILD -eq 1 ]]; then
  step 'wheel install smoke test'
  uv run --locked --extra server --extra mcp pytest -m build
fi

if [[ $WITH_WEB_FUNCTIONAL -eq 1 ]]; then
  step 'final installed shared-Caddy web functional acceptance'
  uv run --locked --extra server --extra mcp python scripts/check-web-functional.py \
    --profile all --manifest "$HFCACHE_WEB_FUNCTIONAL_MANIFEST" --final
fi

printf '\n\033[1;32mall checks passed\033[0m\n'
