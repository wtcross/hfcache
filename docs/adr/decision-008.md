# Use one provider-neutral executable quality gate

- Decision identity: 008.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.

## Context, decision and consequences

A shell script gives workstation, hook and pipeline callers the same lock,
format/lint/type/test/build checks without coupling the project to a CI provider.
Bash is an explicit host prerequisite; making the Python gate depend on make was
rejected. The conditional Cockpit stage separately needs its actual build toolchain;
a loud skip cannot count as plugin validation. The gate remains `scripts/check.sh`,
with an explicit isolated wheel-install smoke option.

## Provenance and governing evidence

The source entry first appears in
[13508db](https://github.com/wtcross/hfcache/commit/13508db16f5446ea223ee8428500522c7d2ab4b4)
(2026-07-24, `project bootstrap: add provider-neutral quality script and build smoke
test`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.



Implementation or shipped-artifact evidence:
[scripts/check.sh](../../scripts/check.sh).

Relevant verification:
[tests/system/test_wheel_smoke.py](../../tests/system/test_wheel_smoke.py).
