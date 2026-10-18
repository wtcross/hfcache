# Consumer revision creation and serving promotion have separate ownership boundaries

- Decision identity: 099.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-08-24.

## Decision, context, and consequences

The locked `vllm` identity owns only `<model>/revisions/`, where every `copy-revision.py` invocation receives a new non-existent destination; root owns the model root and therefore the eventual `current` pointer changed only after manifest verification. This makes targeting a live serving path unavailable to the copy identity, which matters because the reference helper deliberately removes an existing destination before promotion. The 100 GiB figure is an existing-model-plus-available capacity check, not a claimed filesystem reservation: deployments needing isolation use a dedicated filesystem or quota. **Rejected:** making the whole model root writable by `vllm`, because a serving process could replace its own promotion pointer; preallocating a 100 GiB reserve file, because it consumes the capacity intended for model copies and requires a second unsafe shrink/replenish protocol.

## Provenance and governing evidence

The source entry first appears in
[0309edb](https://github.com/wtcross/hfcache/commit/0309edb5b3397204c69deee3dc860ac0f867d675)
(2026-08-24, `operational tooling: add consumer model-store setup`). The decision text above
preserves the complete reasoning in the current historical log, including its
recorded alternatives and consequences.

Current governing documents: [docs/consumers.md](../consumers.md).

Implementation or shipped-artifact evidence:
[scripts/setup-hfcache-consumer-model-store.sh](../../scripts/setup-hfcache-consumer-model-store.sh),
[examples/copy-revision.py](../../examples/copy-revision.py).

Relevant verification:
[tests/unit/test_consumer_model_store_script.py](../../tests/unit/test_consumer_model_store_script.py).
