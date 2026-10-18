# Repository names are canonical, type-aware external links

- Decision identity: 101.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-08-30.

## Decision, context, and consequences

A model name links to `https://huggingface.co/<owner>/<name>` and
a dataset name to `https://huggingface.co/datasets/<owner>/<name>`; encoding
each identifier segment keeps the generated path structural. The page opens
the destination in a new tab with `noopener noreferrer`, preserving the
Cockpit view and carrying neither an opener relationship, a referrer, nor a
Hub credential (`CP-08`). **Rejected:** linking the current commit instead,
because the parent row represents the repository and its expansion already
presents every retained revision; making one revision the navigation target
would misstate that scope.

## Provenance and governing evidence

The source entry first appears in
[f56cec2](https://github.com/wtcross/hfcache/commit/f56cec20d3a152821701b4bb1c1fc31870830535)
(2026-08-30, `Cockpit integration: link repository rows to Hugging Face`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents: [docs/cockpit.md](../cockpit.md).

Implementation or shipped-artifact evidence:
[cockpit/src/lib/repository.ts](../../cockpit/src/lib/repository.ts),
[cockpit/src/archive.tsx](../../cockpit/src/archive.tsx).

Relevant verification:
[cockpit/test/repository.test.ts](../../cockpit/test/repository.test.ts).
