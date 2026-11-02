# OPS-025: Bind the preserved rootless account home without moving its store

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Production web migration](../2026-11-01-plan-production-web-migration.md) |
| Depends on | [REL-016](rel-016-web-release-source.md), committed `bcfd7d3` |

## Scope and acceptance

The actual protected `hfcache` passwd home and running Podman store are under
`/var/lib/hfcache/container-home`; the new host helper only accepts
`/var/lib/hfcache`. Preserve the existing account, store, images, credentials,
locks and operation/configuration history. Support exactly those two homes for
the rootless helper, selected through an optional closed `account_home` field in
protected deployment evidence. Omission keeps the previous default. Native
behavior remains unchanged and rejects this rootless field.

Bind and recheck UID/GID/home before and after observation; derive all engine
environment, user override and persistent lock paths from that single protected
choice. Refuse mismatches, unsafe aliases or missing selected evidence without
searching another store. Preserve both fixed secret masks and all existing
SELinux, namespace, capability, peer, lock, budget and argv constraints. No public
path selector, new dependency, account/store migration or permission grant.

This additive protected host-index field requires actual previous-reader evidence
and rollback documentation. Runtime, archive, API-operation, configuration-outcome
and SELinux-receipt formats stay unchanged. Podman 6.0.2 on this actual host has
the exact three supported stock configuration hashes; its actual confined
installed acceptance remains OPS-024 work, with no package update or source
check weakening.

## Contracts, invariants, and ADRs

Review `docs/agents/technical-record-policy.md`, INV-020 and configuration/security
invariants INV-001–003, `docs/host-administration.md`, and decisions 150, 151 and
159. Add decision 162 and its progress entry; amend affected records, the register
and formal host-index contract in this package. The reviewed unapplied proposal
is `.scratch/ops024-home-compatibility/proposal.patch`, SHA256
`7b2e34d203124d44857ab8c900c188af4a9b9638ae6ec9dad7cbdc312bf16b85`.
Independent review found no remaining critical source issue; tests are still
required. Drafting alone established no implementation or installed acceptance.

## Validation

- Focused3 passes 857 host account/engine/lock/runtime/peer/policy/preparer/
  launcher/guard/SELinux/render/drain tests in 34.51 seconds; outer exit 0 in
  40.575 seconds. Format, lint, whole-project types and host Python 3.12
  compilation of all four modified packaged sources pass. Private empty
  read-only NFS shadow and login UID/GID 1000 are proved before execution.
  `.scratch/ops025-validation/focused3-result.json` and its shadow receipt
  retain actual results. Earlier failures remain retained; corrections address
  test imports, fixture isolation and typing/style, with no guard weakening.
- Actual previous/current parser drill passes 16 observations on owned synthetic
  host indexes under independent NFS shadow. Committed `f7d1246` reader hash
  `15be8ca2eb4aaf3cdad3143bfe668059b6dc57efad0b124f822c3c5280e4e727`
  accepts legacy inputs and refuses the added field. Current reader hash
  `8766df32e3c9141bb729cdc1fdaee3ac2b21b22804a596cb8a0b7921db67d96f`
  accepts both exact rootless homes while refusing aliases/coercion/native extras.
  Released source `1c68501` and its actual `b88ffd0f…6503` wheel have no helper
  reader: unavailable, not a successful read. Inputs and both reader bodies are
  retained unchanged under `/var/tmp/hfcache-ops025-account-home-format1`;
  result SHA256 `9c2e7cbfcb4404f53343fb864a8403d2b5636d8ea9070852f9528c8551b92178`.
  No archive format changes or archive I/O occur in this local authority drill.
- Full `scripts/check.sh --require-web --with-build` passes as the login
  builder with private empty read-only `/srv/hfcache` shadow: inner exit 0 in
  1,625.620 seconds; outer exit 0 in 1,626.500 seconds. All 1,233 staged/tracked
  inputs, including the new test/ADR/task files, retain their bytes and names.
  Passed 9,590 backend tests (52 opt-in deselected), 4,051 combined web and
  16 wheel tests, three locked installation profiles, 175 wire definitions,
  documentation 213/29, full build, two owned Chromium checks and real API React
  read fixture. Coverage is 95.02% lines/90.13% branches; no required web skips.
  Log SHA256 `bd5d8d30e1a41318b9eea5ed81a959d02d72f826dc224d9435eada845d5d7d71`;
  inner result `1ed76027dd564522e4a98593eb7121b25cc201cddeae53becb2e91bf19111602`;
  outer result `7b902e6a433996a030cace62815e5f7c7b5def757e184087ed2c3dc012be89bf`.
  Results, logs and wrappers stay under `.scratch/ops025-validation`; successful
  generated TMP remains preserved until a separately reviewed retirement.

## Execution notes and handoff

The independently reviewed proposal is applied only after this record's
activation. No production mutation belongs to this task. A single earlier
diagnostic with the default home created an explained unused local store; retain
it separately and never select, merge or clean it as part of migration.
Current configuration/candidates and all original stores/handles match the
verified root-private OPS-024 backup. The intentionally disabled guard setting
is preserved by default; the migration switch will still use temporary original
lock protection and continuous NFS-ro/writer masks.

## Completion evidence

2026-11-01, OPS-025, this commit: bounded account-home implementation and native
preservation, meaningful focused/full gates, host Python 3.12 compatibility,
actual previous-reader drill, technical-record review and human contracts are
complete. Decision 162 amends decisions 150/151/159 and INV-020 in this package.
No dependency, runtime/archive/operation/outcome/receipt format, permission,
namespace or capability expansion. The protected host-index widening and strict
old-reader refusal are explicit. OPS-024 now owns clean immutable construction
and actual enforcing installed acceptance on the unchanged production account
and store. No production service, archive, credential, selector, calendar, tag or
remote-publication action occurs in this source package.
