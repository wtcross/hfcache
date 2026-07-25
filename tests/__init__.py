"""Test support package.

Only `tests/` and `tests/fixtures/` are packages. The suite directories —
`unit`, `integration`, `system` — deliberately stay namespace directories under
`--import-mode=importlib`, so a test module's name never depends on where it
sits. This package exists so shared fixture builders have one importable name
that both the runtime and the type checker agree on.
"""
