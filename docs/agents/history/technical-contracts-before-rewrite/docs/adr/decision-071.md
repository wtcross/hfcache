> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 071: The release is deployed from a wheel already; it is not deployed from `dist/`, and it should not be

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.
- Original work package: `REL-001`.
- Source: [decision 71 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §28 and the
Phase 8 checklist both assert that `install-release.sh` "stages a source tree
and runs `uv sync`", so no deployed release has been installed from the built
artifact. The first half is right and the conclusion does not follow.

What is actually installed. `uv sync --frozen --no-dev --no-editable` builds
a wheel *from the staged release tree* and installs that wheel. The evidence
is in the deployed venv: `hfcache-0.1.2.dist-info/` carries a `WHEEL` file
reading `Generator: uv`, `Root-Is-Purelib: true`, `Tag: py3-none-any`, plus a
`RECORD`. There is no `.pth` file, no editable install, and `src/` is not on
`sys.path`. `--no-editable` is the flag that makes this so, and it has been
there since `HOST-004`. The application on the writer is a wheel.

What is true is narrower: the deployed wheel is not the file in `dist/`. It is
an equivalent wheel built at deploy time from the same sources. Changing that
was considered and rejected on two grounds. `dist/` is a build directory whose
contents can come from a different checkout than the tree being staged — it
is `.gitignore`d and was last rewritten by a test run — so installing from it
would let the deployed code diverge from the release tree sitting beside it,
which is a new failure mode bought with no new guarantee. And `uv pip
install`ing a wheel resolves its dependencies fresh; `uv sync --frozen` is
what applies `uv.lock` exactly, and the lock is the entire reproducibility
story. Trading a lockfile for a filename is a bad trade.

So the mechanism is retained, `docs/deployment-centos-stream-10.md` §§13–14
keep their exercised output because nothing about the procedure changed, and
the built artifact keeps being smoke-tested into a clean virtual environment
by `tests/system/test_wheel_smoke.py` under `-m build` — which is the fallback
the work package itself names for this outcome.

The plan text is left as it stands rather than corrected in place: it
described a real gap in good faith, and this entry is the answer to it.

## Later history and current interpretation

This records why the installer uses a frozen, non-editable install from the
staged source tree. Historical release numbers are evidence of that drill, not
instructions to deploy those versions.

## Provenance and governing evidence

The source entry first appears in
[de3398f](https://github.com/wtcross/hfcache/commit/de3398f6e01d22727acb2b0f324429d0e080ba56)
(2026-07-27, `REL-001: install release candidate 0.1.2, and answer the wheel
question`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents:
[docs/agents/release.md](../../../../release.md),
[docs/deployment-centos-stream-10.md](../../../../../deployment-centos-stream-10.md).

Implementation or shipped-artifact evidence:
[scripts/install-release.sh](../../../../../../scripts/install-release.sh),
[uv.lock](../../../../../../uv.lock).

Relevant verification:
[tests/system/test_wheel_smoke.py](../../../../../../tests/system/test_wheel_smoke.py).
