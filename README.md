# hfcache

Archive complete revisions of public Hugging Face model and dataset repositories
on long-term storage, and publish them as immutable trees that downstream systems
can copy and verify.

`hfcache` resolves a configured branch or tag to an immutable commit SHA,
downloads the complete repository snapshot at that SHA through the official
`huggingface_hub` client, SHA-256 verifies every newly introduced object, and
atomically publishes an ordinary-file tree. Consumers mount a server-enforced
read-only NFS export, read one small JSON reference, and copy the exact immutable
tree it names.

A revision is either completely published and verifiable, or it is not visible to
consumers at all.

## What it does

- **Immutable revisions.** Every download is pinned to a resolved 40-character
  commit SHA. Branch and tag names are resolved once per run, never trusted mid-flight.
- **Repository-complete.** Every file in the upstream repository at that SHA. No
  include or exclude filters exist, by design.
- **Verified before publication.** Newly introduced unique content is read and
  hashed locally. Upstream-supplied digests are comparison values, never substitutes.
- **Bounded retention.** Five unique revisions per repository. A sixth successful
  publication prunes the oldest eligible one; the current revision is never pruned.
- **Never destructive on error.** Upstream `403`, `404`, deletion, or removal from
  configuration preserves every local revision. Where a failure can leave more or
  less data, it leaves more.
- **Crash-safe.** Every mutation is a single atomic filesystem operation followed
  by a durable checkpoint. Every state a crash can leave has one correct resolution.
- **Content is data, never code.** Nothing from a repository is executed,
  imported, unpickled, or given `trust_remote_code`.

## Status

Under active implementation. `docs/progress.md` is the authoritative work-package
tracker; `docs/plan.md` is the accepted implementation plan.

## Documentation

| Document | Contents |
| --- | --- |
| [`docs/architecture.md`](docs/architecture.md) | Architecture decisions, filesystem layout and invariants, transaction and crash-recovery boundaries |
| [`docs/configuration.md`](docs/configuration.md) | Every configuration key, its constraints, and credential handling |
| [`docs/schemas.md`](docs/schemas.md) | Durable JSON formats: manifests, references, catalog, reports, journals |
| [`docs/cli.md`](docs/cli.md) | Command surface, JSON output, exit codes, error taxonomy |
| [`docs/security.md`](docs/security.md) | Assets, trust boundaries, threats, and the control enforcing each |
| [`docs/plan.md`](docs/plan.md) | The accepted implementation plan |
| [`docs/progress.md`](docs/progress.md) | Work-package tracker and operator handoff |

## Development

Requires [uv](https://docs.astral.sh/uv/) and CPython 3.14.

```bash
uv sync                      # create the locked development environment
uv run hfcache --help
```

Quality gates, all of which must pass from a clean checkout:

```bash
uv lock --check
uv run ruff format --check .
uv run ruff check .
uv run pyrefly check
uv run pytest
uv build
```

## License

MIT. See [`LICENSE`](LICENSE).
