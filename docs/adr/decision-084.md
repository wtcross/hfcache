# Placeholders replace environment specifics, records included

- Decision identity: 084.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-28.

## Decision, context, and consequences

The repository is public; the deployment's
hostnames, addresses, and provisioned identifiers are the environment's
business, not the repository's. Two rules shaped the scrub. **Same-shape
placeholders**, so every document keeps its meaning: RFC 2606 names under
the same labels (`hfcachewriter.lab.example.com`, `nas.lab.example.com`),
RFC 5737's `192.0.2.0/24` with last octets preserved — the writer stays
`.90` everywhere, so the export allow-list narrative still reads — and
the all-zeros UUID `examples/config.toml` already established as
"replace me". **Records are scrubbed too**: the recorded environment inventory and historical handoff items are historical
records, but what they record — that a value was confirmed, provisioned
once, excluded from an allow list — survives substitution intact, and a
public record is exactly where the real values must not sit. What
deliberately stays: the `wtcross` GitHub identity, author email, and
license copyright (published on purpose), the `tank/huggingface-archive`
dataset path (TrueNAS's default pool name, generic), and hash or random
log samples (a config fingerprint, run ids) that identify nothing. The
real values now live only where they operate: `/etc/hfcache/config.toml`,
the sentinel, the NAS, and local git remote configuration. Git history
before `a0bcee4f3facf69c12f3f3d61f70a50417b5c2be` still carries the originals; removing those is a history
rewrite with new object ids throughout, which this decision does not
perform and which, if wanted, is its own recorded step.

## Later history and current interpretation

The source below uses the repository's existing placeholders. The ADR backfill
preserves that public-record policy and does not restore private values from
earlier Git history.

## Provenance and governing evidence

The source entry first appears in
[a0bcee4](https://github.com/wtcross/hfcache/commit/a0bcee4f3facf69c12f3f3d61f70a50417b5c2be)
(2026-07-28, `documentation maintenance: scrub environment specifics into placeholders`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current public-record policy: this decision. Security boundaries are defined
in [security](../security.md).

Implementation or shipped-artifact evidence:
[examples/config.toml](../../examples/config.toml),
[README.md](../../README.md).

Verification or recorded operational evidence:
[recorded deployment scope](../deployment-status.md).
