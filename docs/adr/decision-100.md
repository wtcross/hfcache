# Decision 100: Serving consumes the verified ordinary-file tree through read-only container mounts

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-08-24.
- Original work package: `OPS-010`.
- Source: [decision 100 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The image, model directory, and YAML configuration are explicit inputs because vLLM, CUDA, and model-specific settings belong to the consumer deployment rather than the archive contract. The launcher resolves both host paths, mounts the model and config privately SELinux-labelled and read-only, and supplies the mounted model path positionally to an explicit `vllm serve`; it does not repeat manifest verification already completed by the copy helper. Podman is preferred on this CentOS-family deployment, with Docker selectable for consumer portability, and the wrapper stays foreground so signals and the serving exit status retain their ordinary meanings. **Rejected:** installing or pinning vLLM on the host, which would add deployment-specific runtime dependencies to hfcache; disabling SELinux labelling for bind-mount access, which would weaken the host boundary; and silently taking a model identifier from YAML, which could serve something other than the verified directory the operator named.

## Provenance and governing evidence

The source entry first appears in
[827e9b2](https://github.com/wtcross/hfcache/commit/827e9b2c3271bf25e4543ec4fce41316e09c9257)
(2026-08-24, `OPS-010: add verified-model vLLM launcher`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents: [docs/consumers.md](../../docs/consumers.md).

Implementation or shipped-artifact evidence:
[scripts/consumer-serve-hfcache-model.sh](../../scripts/consumer-serve-hfcache-model.sh).

Relevant verification:
[tests/unit/test_consumer_serve_script.py](../../tests/unit/test_consumer_serve_script.py).
