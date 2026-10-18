# Decision 067: The consumer helper is `examples/copy-revision.py`, and it may not import `hfcache`

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.
- Original work package: `OPS-007`.
- Source: [decision 67 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §6.3 requires "a small shell/Python
example that copies the tree and verifies it against the referenced manifest"
and §33 requires that a downstream system can do exactly that, but plan §7's
layout gave the example no home: `examples/` listed only `config.toml`. §7 is
amended in this commit to list it.

Where it went. `scripts/` was the other candidate and is wrong: everything in
it — `check.sh`, `install-release.sh`, `check-hardening.sh` — is run by the
*operator* on the writer, against a deployment. This is run by someone else,
on a machine that has no deployment. `examples/` also ships in
`RELEASE_CONTENT`, so the helper reaches `/opt/hfcache/current/examples/` and
an operator has something to hand to a consumer.

The constraint that shaped it: **standard library only**. The tempting
alternative was to reuse `hfcache.verification`, which already hashes a tree
against a manifest and is far better tested than anything written here. It was
rejected because it inverts the dependency the archive exists to avoid. A
consumer is a machine that mounts one read-only NFS export; requiring it to
install this project — and therefore `huggingface_hub`, `pydantic`, `hf_xet`,
and a Python 3.14 that CentOS Stream 10 does not ship — to *read a directory*
would make the archive harder to consume than the Hub it is caching. The cost
is a second implementation of the verification loop, and it is paid knowingly:
the helper duplicates roughly forty lines of hashing and path checking.

That duplication is also a mild benefit, and it is why the helper was proven
against damage rather than only against success. It is an independent reading
of the same manifest: it was run on a throwaway tree with a byte flipped, a
file removed, and a file added, and it caught all three. If it and the
application ever disagree about a published revision, that disagreement is
information — one of them is wrong, and the manifest says which.

Exit codes are the helper's own (`0`/`1`/`2`) and deliberately not §11.2's.
It is not this application, it does not run on this host, and borrowing
`40` for "digest mismatch" would imply a shared taxonomy that does not exist.

## Provenance and governing evidence

The source entry first appears in
[53afd69](https://github.com/wtcross/hfcache/commit/53afd6901631f1e7237ecdf2d190561d406ee127)
(2026-07-27, `OPS-007: consumer copy-and-verify helper and docs/consumers.md`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/consumers.md](../consumers.md).

Implementation or shipped-artifact evidence:
[examples/copy-revision.py](../../examples/copy-revision.py).

Recorded operational verification: [OPS-007 and decision 67 in the tracker](../agents/progress.md#decisions). The source decision records independent damage drills for changed, missing, and extra files; there is no claim here that the later model-store script tests verify this original helper.
