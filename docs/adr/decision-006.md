# MIT license, `uv_build` backend

- Decision identity: 006.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.

## Decision, context, and consequences

The original module layout requires a
`LICENSE` file but named no license, and the original packaging contract required `uv build` artifacts
without naming a backend. MIT is the conventional permissive default for an
internal tool and constrains nothing; changing it is a one-file edit with no
code impact. `uv_build` is uv's own PEP 517 backend, needs no extra build
dependency, and supports the `src/` layout natively — consistent with the packaging
requirement to build both sdist and wheel with `uv build`.

## Provenance and governing evidence

The source entry first appears in
[a23a2a4](https://github.com/wtcross/hfcache/commit/a23a2a40ba7bf02031bc9388db891741922e648e)
(2026-07-24, `project bootstrap: initialize uv project and src/ layout`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents:
[LICENSE](../../LICENSE).

Implementation or shipped-artifact evidence:
[pyproject.toml](../../pyproject.toml).

Relevant verification:
[tests/unit/test_package.py](../../tests/unit/test_package.py).
