# `CHANGELOG.md` beside the annotated tags, and README `Status` stops accreting release notes

- Decision identity: 083.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-28.

## Decision, context, and consequences

The release record was
annotated tags plus a README paragraph that grew a release's worth of
detail each tag plus the `REL` entries here — all true, none browsable
from a repository listing, which starts to matter the moment the
repository has one. `CHANGELOG.md` states in its preamble that the tags
carry the complete notes and it is the summary, so there is one authority
and one convenience rather than two authorities that can drift. README
`Status` keeps the current version and state and points at the changelog
and the operator handoff. The 0.1.0/0.1.1 non-releases are explained in
the preamble because a public reader who meets four version directories
in the deployment doc deserves the explanation the `v0.1.2` tag already
gives.

## Provenance and governing evidence

The source entry first appears in
[c444a5c](https://github.com/wtcross/hfcache/commit/c444a5cc8914c0070e38491fca41e23595506102)
(2026-07-28, `documentation maintenance: CHANGELOG.md, and README status becomes a pointer`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.



Implementation or shipped-artifact evidence: [CHANGELOG.md](../../CHANGELOG.md),
[README.md](../../README.md).

Verification or recorded operational evidence:
[recorded deployment scope](../deployment-status.md).
