# Reconstruct bounded managed configuration privately from exact installed bytes

- Decision identity: 153.
- Status: Accepted design.
- Date: 2026-10-25.
- Introducing change: this commit.
- Amends the read/prepare portion of [decision141](decision-141.md) and
  [decision150](decision-150.md); guarded application remains separate.

## Context and decision

The administrator needs an editable configuration without receiving protected
Hub/credential fields or replacing them with redaction placeholders. Operational
fingerprints exclude tags and comments and cannot detect all concurrent edits.
Use the existing independently provisioned HMAC key and full-byte revision.
The existing fixed, peer-authenticated helper captures the configuration once;
both its editable projection and revision describe that same capture. Reads and
preparation create no lock, candidate, backup, outcome or archive object.
For this non-persisting preparation, descriptor-pinned reads and bracketed exact
byte/metadata revalidation establish the snapshot without taking or creating a
configuration lock. A concurrent change refuses or yields an earlier valid base
that future preparation/application must recheck. This narrowly amends the lock
wording in decision141 for read-only preview; persistent staging and installation
still require the original configuration lock and never hold it over Hub work.

GET configuration returns independent schema1 with `archive_id`, `base_revision`,
`editable`, `editable_fields` and `protected_fields`. The editable projection has
the eleven documented settings and complete repository entries, including tags
and declared dependencies. Metadata identifies the supported fields and gives
fixed safe descriptions of protected fields; it contains no protected values.
The API requires explicit configuration-read capability and independent policy.
For a configuration read it sends its immutable lifespan archive ID/root in the
existing private `config-read` operation, with both comparison selectors present.
The helper uses the same fresh protected snapshot and preserves the API's
check order: supported/guarded status and nonnull binding, configuration
permission, then nonnull profile and exact archive equality. Only after every
check may it return the existing projection. Unproved status or an otherwise
valid mismatched tuple is unavailable; denied permission is denied even when
the expected tuple also mismatches. Legacy empty-body private reads remain
supported. This removes only the redundant preceding API status exchange,
without changing either peer reauthentication, configuration revalidation,
deadlines, capacity, filesystem rights or public DTOs.

Managed validation and planning accept the documented exclusive `{managed:
{base_revision, edits}}` form. There are at most256 edits, one touch per repository
and at most one nonempty settings replacement. An upsert replaces the complete
entry using the existing defaults; removal requires an existing entry and removes
configuration only. Empty edits remain an explicit non-installing assessment.
Unknown/mixed/coercive forms, selectors on managed plans and authority changes
refuse. Existing installed/literal forms keep their canonical bytes and responses.

The fixed read-only `config-prepare` operation accepts only the managed form.
It compares the opaque base with fresh captured bytes, applies the closed edits
privately and returns a bounded private candidate, editable projection,
`candidate_revision` and `required_selectors`. The candidate revision is another
domain-separated HMAC over base identity and exact reconstructed bytes; neither
public response discloses a full-document hash or raw candidate. A stale base is
a classified conflict. The API independently validates the returned candidate
against its existing configuration models and all six pinned authority fields.
Private candidate text never enters a generic receipt, event or public result.

Reconstruction uses one bounded standard-library renderer for the closed schema1
vocabulary: fixed tables, repository table arrays, booleans, bounded integers,
strings and string arrays. Parse the complete base with `tomllib`, preserve all
protected values, validate the closed schema, then serialize canonical UTF-8
TOML with fixed ordering, escaped basic strings and a final newline. Comments and
formatting are discarded deliberately. Every append is charged against the1MiB
candidate ceiling; private encoded replies independently obey the2MiB frame
ceiling. No source-text substitution, browser TOML writer or generic arbitrary
TOML editing is introduced. Round-trip tests use the independent standard TOML
parser and existing application validator, including quoting and byte expansion.

Planning derives exactly newly added, newly enabled or revision-retargeted enabled
repositories. Empty scope needs no Hub access but still produces an explicit
successful bound assessment. Nonempty scope requires independent Hub permission
and complete sizing through existing services. Release all helper/config/API
admission locks before Hub work. Recheck base, permission and protected authority
after queue waiting. The independent managed assessment binds base/candidate,
required scope and sizing completeness to the original durable plan operation;
it is evidence, never a permission token. Observation uses that original handle.

## Rationale and alternatives

The configuration schema has a finite scalar/table vocabulary, so a small closed
renderer avoids installing another runtime into the standard-library-only host
helper. It is not a general TOML writer. A maintained general or round-trip writer
would be appropriate if the accepted vocabulary expands; it would need an explicit
dependency/packaging decision. Regex edits, client replacement documents and
timestamped rendering cannot preserve exact identity or hidden fields reliably.

## Consequences and evidence

Validation/preview never installs anything, and old candidate clients retain
their behavior. Canonical formatting is an explicit operator-visible tradeoff.
Full-byte changes, including tags/comments, invalidate existing edits. Apply,
durable private preparation/outcomes and crash reconciliation remain the later
guarded application obligation. No permission, dependency, host effect opcode,
archive format or automatic replay is added here. Required unit, actual Unix/API,
same-Caddy installed functional and human-documentation evidence accompanies
implementation; this design alone establishes no acceptance.

## Guarded application amendment (2026-10-25)

[Decision154](decision-154.md) defines the narrow configuration writer, shared
legacy guard, durable private outcomes and original-handle read-only observation.
It supersedes earlier assumptions of a wholly read-only helper for this fixed
operation; all unrelated authority and original reasoning remain.

## Structured editor composition clarification (2026-10-26)

The browser composes these existing read/validate/preview contracts into one
RAM-only editable draft, supported JSON view and local intent diff. It never
receives protected values or serializes TOML. Complete repository entries and
the eleven supported settings keep their existing defaults and strict bounds.
Every edit or concurrent full-byte change invalidates validation and assessment;
compare/reload/re-edit is explicit, with no silent tag merge or base-token swap.
Configuration-read/write affordances use their respective grants and protected
policy, without host-read as an extra gate. This adds no endpoint, schema,
dependency or new authority. See [editing procedures](../web-ui/configuration-and-tags.md).

## Manual draft replacement clarification (2026-11-02)

Manual installed-configuration reload requires an explicit accessible decision
for prepared or raw unsaved edits, bound to the reviewed draft/auth generation.
Cancellation preserves readiness and issues no read. Confirmation retires
validation/preview readiness but retains the original base, prepared intent and
mounted raw editor through pending and failed same-authority reads. Only a fully
decoded, scope-checked success replaces all three together, including same-base
responses. This prevents failed reads from losing admitted work without storing
drafts, merging edits or attaching a new base to old intent. Authentication loss,
disposal and newer generations fence stale decisions/responses. Original preview/
application handles and unknown-effect blocks survive independently; configuration
reads establish no protected outcome. Internal post-Apply reload retains its newer-
draft safeguard. See [configuration guidance](../web-ui/configuration-and-tags.md#compare-concurrent-changes-without-losing-intent).
