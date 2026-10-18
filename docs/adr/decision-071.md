# Install native wheels from the locked staged source tree

- Decision identity: 071.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.

## Context, decision and consequences

Native `uv sync --frozen --no-dev --no-editable` builds and installs a wheel from
the staged release sources, with normal dist-info/RECORD and no editable source
path. That differs from installing an arbitrary file already present in `dist/`.
The latter may belong to another checkout and would decouple running code from
the adjacent release tree. A fresh pip resolution would also discard the locked
closure; frozen sync preserves it.

Keep native staged-source installation and independently smoke-test the built
wheel in a clean environment. Rootless releases instead bind their authenticated
wheel/hashed closure/image identities through the protected release manifest;
the two profiles are separate installation mechanisms.

## Provenance and governing evidence

The source entry first appears in
[de3398f](https://github.com/wtcross/hfcache/commit/de3398f6e01d22727acb2b0f324429d0e080ba56)
(2026-07-27, `release preparation: install release candidate 0.1.2, and answer the wheel
question`). The decision retains its rationale, alternatives and consequences.

Current governing documents:
[docs/deployment-centos-stream-10.md](../deployment-centos-stream-10.md).

Implementation or shipped-artifact evidence:
[scripts/install-release.sh](../../scripts/install-release.sh),
[uv.lock](../../uv.lock).

Relevant verification:
[tests/system/test_wheel_smoke.py](../../tests/system/test_wheel_smoke.py).
