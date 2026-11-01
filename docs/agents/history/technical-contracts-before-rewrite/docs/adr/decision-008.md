> Historical technical reference preserved before consolidation. Current authority is the living contract.

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `b7f84d381a85a9849796f5851e777b9eb0e21f7d079760d4e490ab8821016753`,
original content SHA-256 `19c7f733a526671ebc3ee0e8e8861ef33cf2c334d95bdff524e1b55488987fac`.
Historical proof hashes identify the original artifacts, not this edited record.

# Decision 008: `scripts/` added to the project layout; no CI-provider configuration

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.
- Original work package: `BOOT-007`.
- Source: [decision 8 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §7's tree has nowhere to put the
"provider-neutral quality scripts" `BOOT-007` requires, so `scripts/check.sh`
is added and plan §7 updated in this commit. Deliberately *not* added: any
CI-provider file. The gate is one script that a shell, a git hook, or a
pipeline all invoke identically, so a green pipeline and a green workstation
mean the same thing. A Makefile was considered and rejected — `make` is not
installed on the CentOS Stream 10 writer, and bash is.

## Later history and current interpretation

The original gate covered the Python application. [Decision 88](../../../removed-interface-records.md)
later adds the conditional historical frontend toolchain stage without adding an application
runtime dependency.

## Provenance and governing evidence

The source entry first appears in
[13508db](https://github.com/wtcross/hfcache/commit/13508db16f5446ea223ee8428500522c7d2ab4b4)
(2026-07-24, `BOOT-007: add provider-neutral quality script and build smoke
test`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents:
[docs/agents/workflow.md](../../../../workflow.md).

Implementation or shipped-artifact evidence:
[scripts/check.sh](../../../../../../scripts/check.sh).

Relevant verification:
[tests/system/test_wheel_smoke.py](../../../../../../tests/system/test_wheel_smoke.py).
