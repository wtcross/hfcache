# Plugin CLI invocations run in transient units that import the deployment's encrypted Hub credential

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

- Decision identity: 092.

- Original decision date: 2026-07-30.

## Decision, context, and consequences

## Later history and current interpretation

The anonymous fallback for an absent imported credential applies to `optional`
policy. [Decision 98](decision-098.md) adds `required`, under which the
application refuses missing credentials. Transient-unit lifetime supersedes
[decision 89](decision-089.md)'s tab-cancellation behavior.

## Provenance and governing evidence

## 2026-10-18 historical API integration amendment

The credential-delivery mechanism remains systemd, but its authority changes:
transient API clients import only `hfcache.api`, use fixed client TOML/socket and
omit ordinary archive config/Hub environment. Hub `hf-token` stays daemon-only;
there is no anonymous fallback for missing API credentials. Browser/argv/environment
bearers remain forbidden. Closing/stopping a client loses observation, never
cancels accepted execution or proves recovery safe. This supersedes the Hub-import
and direct-execution implications above; see [decision 122](decision-122.md).

## Pipe-only confirmation amendment (2026-10-20)

[Decision139](decision-139.md) applies the historical stdout pipe requirement
to exact installed confirmation after reproducing an enforcing PID1 file-write
denial. Current API-only credentials and the fixed rootless launcher remain
those of decisions122/127; the earlier encrypted Hub-import design is not revived.

The pre-removal record remains in Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`; removed interface-only
instructions and source evidence are historical, not current operating steps.
