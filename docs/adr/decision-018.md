# Decision 018: Durable files are indented; the `--json` envelope is not

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `CFG-004`.
- Source: [decision 18 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

`docs/schemas.md` §1 named the separators `(",", ": ")` but no
indentation. That pair is exactly what `json.dumps` uses *when indentation is
on* — the compact spelling would be `(",", ":")` — and every worked example in
the document is 2-space indented, so indentation was intended and unstated.
Now stated. The envelope stays unindented, which is not an inconsistency but
the distinction that matters: a durable file is read and diffed by an operator
during an incident, while the envelope is one machine-read line on a pipe.
`docs/cli.md` §4 already listed only the three rules that carry over — sorted
keys, UTF-8, trailing newline — so no change was needed there. Both paths call
`models.serialize`, so §11's "one shared function" is literal rather than
aspirational.

## Provenance and governing evidence

The source entry first appears in
[2133496](https://github.com/wtcross/hfcache/commit/21334967781eef8ee37600ed63fad4e42e404180)
(2026-07-25, `CFG-004: implement the durable manifest and report models`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/schemas.md](../schemas.md),
[docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/models.py](../../src/hfcache/models.py),
[src/hfcache/reporting.py](../../src/hfcache/reporting.py).

Relevant verification:
[tests/unit/test_models.py](../../tests/unit/test_models.py).
