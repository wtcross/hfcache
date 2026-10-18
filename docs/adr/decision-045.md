# An empty tree listing is reported; an entry with no path is refused

- Decision identity: 045.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.

## Decision, context, and consequences

`HFHUB008` is "repository tree metadata missing or
incomplete", and two conditions could claim it. A revision containing no
files is *not* one: it is a truthful answer to what the metadata call asked,
`plan` reports it as `0 files`, and whether an empty revision is worth
publishing — and consuming a retention slot — is a decision for the package
that publishes one, not for the call that reads the metadata.

A file entry with no path is the other, and it is refused. The listing is
what the sync transaction contract calls the exact repository path set, and every later
step joins those names onto a filesystem path; an empty one would arrive at
that join looking like a legitimate name for the tree's own root. The
previous code coerced it to `""` and carried on. This is narrower than the
path grammar in `hfcache.paths`, deliberately: the grammar answers "is this
name safe to join", and this answers "did the response contain a name at
all", which is a question about the library's shape and belongs at the seam.

## Provenance and governing evidence

The source entry first appears in
[e7561d1](https://github.com/wtcross/hfcache/commit/e7561d152b0bf6e9f0bb724366f433eee4f7f7ff)
(2026-07-26, `Hub access: retrieve the repository tree and cost a download without
one`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md),
[docs/security.md](../security.md).

Implementation or shipped-artifact evidence:
[src/hfcache/hub.py](../../src/hfcache/hub.py).

Relevant verification: [tests/unit/test_hub.py](../../tests/unit/test_hub.py).
