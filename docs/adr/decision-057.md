# Decision 057: The `--config` and `--token-file` options do not check readability at parse time

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `HOST-004`.
- Source: [decision 57 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Found the moment
`/etc/hfcache/config.toml` was installed at its documented `0640
root:hfcache` (plan §21.2): every command run as an ordinary account began
exiting `2` from typer's argument parser — including `hfcache version` and
`hfcache --help`, which never open the file.

Typer's `Path` parameter type defaults to `readable=True`, and with
`exists=False` that means a path which does not exist passes while one that
exists but is unreadable fails. `ExitCode` reserves `1` and `2` for a
malformed command line "so a scheduler must be able to tell a malformed
command line from an application outcome" — and a configuration file this
identity cannot read is an application outcome. `load_config` already
reported it correctly as `HFCFG001` at exit `10`, naming the path; the
parser never let it get that far.

Both options now pass `readable=False`, so the access decision belongs to
the code that has an error taxonomy for it. `--token-file` gets the same
treatment for the same reason: `HFARG005` at exit `10`, reported by shape and
never by content. The mode on the configuration file is deliberately
unchanged — it is the contract, and the fix is that the application reports
it properly rather than that more identities can read it.

## Provenance and governing evidence

The source entry first appears in
[41690bd](https://github.com/wtcross/hfcache/commit/41690bd7cd5da5231e74e504489f1eba60dc945b)
(2026-07-26, `SYNC-004: discard a committed transaction's staging area`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

The named work package's implementation commit is
[88eb3f0](https://github.com/wtcross/hfcache/commit/88eb3f0772b6a02cf8c11b0d11a75d545dcfcd56).
The source-entry introduction and implementation are recorded separately rather
than inferred to be the same commit.

Current governing documents: [docs/cli.md](../../docs/cli.md),
[docs/configuration.md](../../docs/configuration.md).

Implementation or shipped-artifact evidence:
[src/hfcache/cli.py](../../src/hfcache/cli.py).

Relevant verification: [tests/unit/test_cli.py](../../tests/unit/test_cli.py).
