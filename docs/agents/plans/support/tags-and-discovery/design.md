# Tags and discovery: proposed implementation contract

Status: draft design, created 2026-10-19. The [parent plan](../../2026-10-19-plan-tags-and-discovery.md)
authorizes no implementation until activated. Existing human contracts retain
technical authority; CAT-001 must explicitly amend conflicts before affected code
lands. This document records chosen behavior, not claims of current support.
The [source review](source-review.md) distinguishes current source from proposals.

## 1. Product boundary

Operators assign a small list of tags while configuring a repository for sync.
Tags cover organization, collections, intended use and preferences. There is no
separate category, group, curated use-case or taxonomy system. Tags do not grant
access, choose files, change retention, schedule work or trigger downloads.

Technical metadata describes an exact published revision and its variants.
The discovery service searches the local configured/archive inventory, not the
live Hugging Face Hub. It never executes repository code or loads a model or
dataset. A tag called `q4` or `preferred` is only a label, never technical evidence.

Deliver deterministic filters and simple substring search. Do not add embeddings,
LLM-based classification, ranking services, external search infrastructure,
SQLite/NFS databases, runtime inference libraries, expected-variant declarations,
or an arbitrary extensible operator metadata dictionary. Upstream descriptive
fields are optional, attributed observations, not another editable taxonomy.

## 2. Configuration tags and normalization

Add `tags: tuple[str, ...] = ()` to the strict frozen `RepositoryConfig`, presented
as `tags = [...]` in TOML directly beside `id`, `type`, `revision` and `enabled`.
An absent field and an explicit empty list have the same meaning. Existing
configuration remains valid. Configured empty tags override any old snapshot.

Use one pure shared Python normalizer for config, queries and writer records:

- Strict list/tuple elements must be strings, never coercions. Bound the input
  to 64 entries before deduplication; each raw string is at most 128 characters.
- Trim outer ASCII spaces, lowercase ASCII letters, then require
  `[a-z0-9][a-z0-9._:/-]{0,63}`. Reject empty values, controls, internal whitespace,
  non-ASCII text and values that exceed canonical length 64. Do not silently
  truncate. Explain these choices in the human configuration guide.
- Deduplicate canonical tags and sort byte-wise. Normalization must be idempotent.
  `Coding`, ` coding ` and `coding` become one `coding` value.
- Colons and slashes are ordinary characters. `project:assistant` and `vision/ocr`
  have no hierarchy, wildcard, inheritance or filesystem meaning. Never build a
  pathname from a tag. Matching is exact after normalization.

The Cockpit UI offers existing-tag suggestions and direct entry, explains that
normalization occurs, and preserves tags through add/edit/toggle/delete, form/text
switching, validation, sizing preview, backup and installation. Its normalization
must agree with backend fixtures; the backend remains authoritative.

No separate API for assigning or removing tags is added. Editing still uses the
existing host configuration workflow. Candidate validation may validate tags but
cannot install a configuration or provide authority to contact a new Hub endpoint.
Do not promote the daemon to root or make the root-owned config writable.

## 3. Three different identities, with no silent fingerprint change

1. **Existing policy fingerprint:** preserve `ApplicationConfig.fingerprint()`
   semantics and baseline golden values; tags are excluded. Archive selection,
   storage, retention and Hub authority keep their existing identity. Tag changes
   cannot invalidate integrity evidence or create new publication identities.
2. **Curation fingerprint:** SHA-256 of a versioned canonical representation of
   `(repository_type, repository_id, normalized_tags)` for all configured entries,
   sorted by canonical repository identity. Include empty/disabled entries. No
   credentials, runtime paths or other configuration contents are included.
3. **Catalog response identity:** a digest of the visible, normalized query scope,
   relevant current curation, selected authoritative publication identities,
   observation contents/coverage and result ordering. Search cursors bind this
   digest in addition to existing route/tool, archive and policy identity.

Retain the existing full candidate/base-content comparison in Cockpit and inspect
all callers: a tag-only change must not be mistaken for an unchanged document just
because the policy fingerprint is unchanged. Admission/result policy fingerprints
keep their current role. New catalog identity fields belong in the new catalog
payload, not as undeclared additions to strict existing REST/MCP wrappers.
Sanitize registered secrets before matching, facets and visible-content digesting;
never make secret substitutions discoverable through counts or cursor changes.
This does not make curation a secrets store: tags must never contain credentials,
and any registered secret label is suppressed from searchable/faceted values.

## 4. Current tags and historical tags

Default effective tags are selected by this rule:

| Repository state | Effective tags | Provenance |
| --- | --- | --- |
| Currently configured, enabled or disabled | Fresh validated configured tags, including `[]` | `configured` |
| Unmanaged with retained publication and valid recorded snapshot | Last writer-observed configured tags | `last_observed` |
| Unmanaged without recorded snapshot | Empty exposed list, with unknown historical coverage | `unknown` |
| No current config and no retained publication | Not a discovery result | No phantom entry |

Expose `tag_origin`, `tag_observed_at` (nullable), and relevant curation identity.
`tag_source=current_only` excludes historical labels from tag predicates, the
tag portion of q and tag facet counts, not from explicitly attributed detail.
Unmanaged repositories may still match identity text or technical filters and
remain visible when no tag constraint is supplied. A returned historical label
is always marked historical; it is never relabeled current to satisfy a filter.
Never label a historical snapshot as current configuration. Re-adding a repository
with an empty tag list clears effective labels immediately. Disabling sync keeps
its tags. Purge cannot be undone or defeated by a surviving metadata file.

The writer captures current tags during normal sync metadata work (including
retained-SHA/no-new-publication cases) and explicit refresh. Capture disabled
entries when they are in the refresh scope. REST/MCP reads and config validation
never persist snapshots. Read current curation afresh from the approved installed
source under the writer-owned metadata operation, keeping authority checks intact;
do not replace the command's admitted operational policy or borrow candidate
credentials. Record the actual snapshot observation time and fingerprint.
An edit that was removed before any writer capture cannot be reconstructed:
report the last recorded observation or unknown, never invent persistence.

Historical records are only last-observed snapshots, not a full configuration
history or audit of every keystroke. Back up their authoritative historical-label
content; do not describe it as reconstructible from current configuration.

## 5. Filesystem artifacts and crash model

Proposed namespace, beneath the existing published export:

```text
published/metadata/
  tags/<type>/<namespace>/<name>.json
  observations/<type>/<namespace>/<name>/<commit_sha>/<publication_id>.json
```

Use validated domain identity and centralized `ArchiveLayout` builders, never raw
paths from a request. Paths in records are validated relative locators and must
agree with their exact authoritative references/manifests. Do not nest new files
inside immutable model trees or existing manifest files. No manifest, reference,
sentinel, retention generation or expected digest is rewritten for discovery.

New strict, independently versioned JSON families:

**RepositoryTagSnapshot, schema 1:** kind, archive UUID, repository type/ID,
normalized tags, observed_at, curation fingerprint, source=`installed_config`.
Its only authority is the last recorded curation observation for an unmanaged
repository. It is not a second editable source for currently configured tags.

**PublicationObservation, schema 1:** kind, archive UUID, repository identity,
full SHA, publication ID, publication generation, manifest identity/digest,
extractor version, observation time, extraction status, typed source observations,
model variants or dataset-format/declaration observations, and bounded diagnostics.
Every source locator must be a member of the authoritative complete manifest.
Bind parser output to source identity and manifest digests; do not claim the read
rehashes the full model. An observation is a rebuildable interpretation, not new
integrity evidence or publication authority.

Both use strict types, sorted arrays, bounded strings/collections and safe atomic
JSON storage. A supported previous record can be replaced atomically under the
common writer lock; unsupported versions, malformed existing records and unsafe
paths refuse and preserve evidence. No blind overwrite to make a test pass.
Persist only selected allowed fields, never an entire README/configuration file.

### Explicit contract amendment required

This new namespace and metadata-only writes are not already authorized by the
existing layout and transaction contracts. CAT-001 must record the following
narrow technical decision and update affected invariants/ADRs:

Each auxiliary JSON replacement is its own atomic, idempotent unit under the
common local archive lock, validated initialized archive identity and storage
preflight. There is no cross-file all-or-nothing promise and no new authority to
replay archive journals. Document an explicit exception to journal-before-mutation
for these bounded adjunct records and their approved directory creation only.
This exception does not apply to trees, manifests, references, prune, repair,
initialization, verification catalogs or any existing transaction algorithm.

Use the existing safe write/fsync/replace primitive. Preserve ambiguous temporary
or unsupported files; readers ignore only the documented noncanonical temporary
names and otherwise fail on corruption in selected canonical artifacts. A crash
may leave some snapshots updated and others unchanged, but each visible record
must be whole. Report incomplete coverage, and let a later explicit writer
refresh repair missing *derived observations*, not rewrite unknown history.

Do not add an aggregate on-disk search index in the first implementation. Bounded
in-memory projection over validated config, references/manifests and observations
is sufficient. This avoids inventing a second transaction across an index and its
sources. Future performance work can add a disposable index only after measurement.

Existing valid archives may gain only this approved supplemental namespace through
writer-owned work after normal preflight. Do not rerun `archive init`, recreate the
sentinel or accept a missing/invalid archive. Preserve all original layout checks
outside this named extension. Unknown entries are not newly acceptable in general.

### Lifecycle, retention and compatibility

Pruned/purged publication observations may remain as inert records in this release;
search always intersects them with the authoritative retained set. Do not add an
automatic metadata garbage collector or use record age as deletion authority.
Make potential growth and explicit later cleanup a documented limitation.
Repair creates a new observation keyed to the new publication ID. It cannot inherit
verification confidence or silently reuse the old instance's observation.

A new directory and new operation kinds may be refused by old binaries even when
old artifact schema versions are unchanged. Test this explicitly; do not declare
backward compatibility by inspecting version numbers alone. Rollback is a guarded
operator procedure: drain the actual executors, preserve metadata/control evidence,
use a reviewed backup/snapshot or explicitly validated compatible layout, restore
a tag-free compatible config, and validate with the target binary. Never delete
new state merely to make an old binary start. No rollback is executed by this plan.

## 6. Writer-owned extraction, never query-time payload reads

Extract during writer-owned post-publication work and offline refresh. Read the
same exact published instance identified by a validated manifest. Do not resolve a
moving Hub branch, fetch a current model card, execute a loader or follow external
URLs. A filename or source declaration is evidence with a named origin, not proof
of functional loadability.

Use safe no-follow, manifest-contained ordinary-file access; bound actual reads,
string/array lengths, nesting, candidate files, header fields and wall/work budgets.
Initial extractor defaults: at most 1 MiB for a card or JSON metadata file,
64 MiB actual header/metadata reads per publication, 4096 candidate artifacts,
64 levels of structural traversal (32 for JSON), and 64 KiB per retained text field.
Prefer much smaller retained summaries (e.g. 2048 characters) where possible.
Use bounded readers and refuse/record unsupported coverage before allocating from
untrusted counts. A limit must cover skipped elements and seeks, not just output.
A long sync must also honor a finite aggregate metadata-work budget; exhaustion
marks unprocessed observation coverage explicitly and cannot bypass producer join.
Do not add new public tuning knobs or runtime dependencies without a recorded need.

For safe YAML, safe loading alone is insufficient: also bound alias expansion,
node count and nesting. Skip unsupported alias/complex structures with a diagnostic.
Do not instantiate repository-defined Python objects or import model libraries.

A parser may produce `complete`, `partial`, `unsupported` or `failed` extraction
status with per-field evidence. A absent optional declaration is not automatically
an error. No unsupported/failed field becomes `false`, unquantized or unavailable
by default. A parser failure is non-fatal to an already valid archive publication,
but must produce a safe warning and honest coverage rather than fabricated success.

### Model/dataset cards and static JSON

Read bounded front matter from manifest-listed README.md and recognized
manifest-listed config files. Selected observations may include task declarations,
languages, license declarations, base-model references and upstream tags. Preserve
field provenance and extracted scalar/list values; do not return arbitrary raw
front matter or descriptions as instructions. Never merge upstream tags into
operator `tags` or expose them as a second editable labeling system.

For datasets, record known file-format candidates and bounded card declarations
for configurations/splits/features when statically present. Do not execute loading
scripts, parse the whole dataset, follow external payload URLs, infer row counts,
or promise declared splits are physically present. Quantization filters do not
apply to dataset results. Broad dataset semantic/schema inference is out of scope.

### GGUF variants

Treat GGUF as a format, not a quantization method. A variant has `format=gguf`,
`quantization_method=ggml` when recognized, a known quantization scheme such as
`Q4_K_M`, and an encoding field able to represent `F16`/`F32` without pretending
they are quantized. Numeric nominal bits may be null for mixed schemes.

Implement a bounded header reader from a pinned primary specification, rather than
installing a full runtime. Read magic/version/endian marker where applicable,
metadata types, selected values including file type, and validated split metadata.
Unknown versions/enums become unsupported observations, not guessed schemes.
Support the chosen current format version(s) explicitly and test unsupported versions.
Never read tensor bodies merely to support a search. Unknown/missing metadata may
leave a filename-derived candidate, but that cannot satisfy exact quantization
filters as confidently established evidence. Exact schemes come from a documented
known header mapping; do not infer K_M/K_S solely from an individual tensor type.

Combine split files only when their logical identity, scheme and explicit shard
count/indices agree. Require the full unique expected set from the same exact
publication before marking a known shard set complete. Do not combine files solely
because they contain `Q4` in their names. Distinguish primary model, adapter,
projector/auxiliary and unknown roles where supported. An auxiliary projector must
not become a standalone main-model match. Contradictory or ambiguous evidence is
visible and does not satisfy a positive available-model filter.

### AWQ/GPTQ and safetensors variants

Read recognized `quantization_config` fields (method, bits, group size) from scoped
static JSON and recognized weight-index maps. Select configuration and weight
members from the same unambiguous directory/package scope. Never apply one root
quantization declaration to every unrelated weights directory in the repository.
Validate each referenced relative path against the manifest and reject escaping,
missing or duplicated members. Detect obvious LFS-pointer text where appropriate;
an index or declaration alone is not a complete available weight bundle.

`format=safetensors` is independent of `quantization_method=awq` or `gptq`.
A missing quantization declaration means unknown, not guaranteed unquantized.
The claim is that an archived configuration declares this method for an identified
weight set; no tensor-level or runtime compatibility validation is implied.
Preserve that evidence grade in responses. Do not import Transformers, PyTorch,
AutoAWQ, GPTQ runtimes or dataset execution libraries for metadata extraction.

## 7. Variant model and positive availability

A model variant is keyed by archive/repository/SHA/publication plus a deterministic
variant ID derived from its canonical logical member set and extractor identity.
Expose format, encoding/scheme/method/bits, role, member paths and member count,
known total weight bytes, completeness (`complete`, `incomplete`, `unknown`),
evidence source/grade and safe diagnostics. Paths remain metadata, not download URLs.

All technical predicates must match **the same variant in the same publication**.
Do not flatten quantizations into a repository-wide union and then separately test
size or format. `max_variant_bytes` measures the variant's identified weight files,
not repository bytes, download space, RAM/VRAM or inference memory. No hardware-fit
claim is supported. A recognized complete weight set is not a runnable-model proof.

Positive technical model searches consider supported primary-model variants with
known member completeness and sufficiently attributed scheme/method evidence.
Incomplete/unknown/auxiliary candidates remain visible through detail/variant
inspection with their status, but do not satisfy an available main-model search.
A retained reference and manifest establish archive publication membership; queries
must not hash/stat every payload file. Availability means declared retained archive
content, not a fresh filesystem or integrity verification. Keep existing exact
publication verification confidence separate and honest.

## 8. Search contract

One transport-neutral `CatalogQuery` and query service own filtering/projection.
Do not give the read service a writer, credential resolver, Hub adapter or arbitrary
path callback. All catalog queries are bounded, lock-free and network-free.

| Field | Behavior |
| --- | --- |
| `repository_type` | Optional `model` or `dataset`; omission searches both |
| `q` | Optional bounded 256-character case-insensitive literal substring of repository ID and effective tags; no regex, fuzzy or semantic interpretation |
| `tags_all` | All normalized exact tags must match; empty is no constraint |
| `tags_any` | At least one normalized exact tag must match; empty is no constraint |
| `tag_source` | `current_or_last_observed` default, or `current_only`; provenance remains exposed |
| `scope` | `archived` default, `configured`, or `all` |
| `revision_scope` | `current` default, or `retained` |
| `format` | Optional normalized recognized-format identifier; no inference from tags |
| `quantization` | Optional canonical GGUF scheme identifier, e.g. `Q4_K_M` |
| `quantization_method` | Optional canonical method identifier, e.g. `awq`, `gptq`, `ggml` |
| `bits` | Optional strict positive integer at most 64, matched only when documented as known |
| `max_variant_bytes` | Optional strict nonnegative integer within the project's byte-count range |
| `limit`, `cursor` | Existing bounded pagination conventions and resource budgets |

Different fields combine with AND. `tags_all` and `tags_any` may both be supplied:
all conditions must hold. Query tags use the same canonicalization as configured
tags. Valid unknown tag/format/scheme values return zero known matches, not fuzzy
substitutions; invalid syntax is a validation error. A model-only technical filter
with omitted type constrains results to models; explicit `dataset` plus a model-only
filter refuses rather than silently ignoring it. Dataset format filters refer to
observed dataset file formats, not model variants.

`configured` includes enabled and disabled entries before their first sync;
`archived` includes managed and unmanaged repositories with retained publications;
`all` is the identity-deduplicated union. Snapshot-only metadata cannot add a row.
`current` means the explicit current reference, not greatest timestamp/generation.
`retained` means only currently retained references, never pruned or superseded
repair instances. Exact detail selectors require both SHA and publication ID or
neither, and never substitute a new current when the requested instance disappears.

Repository search emits one hit per canonical identity, ordered byte-wise by
(type, ID), with tags/origin, configured/disabled/archived state, coverage summary,
`matching_variant_count` and at most one deterministic `representative_variant`.
Choose that representative from the full sorted matching publication/variant set;
label it as a representative, not the entire match collection. A separate paged
variant endpoint/tool enumerates all variants. Dataset results carry their typed
observed-format/declaration summary and no fictional model fields.

Use typed schema-1 catalog payloads inside existing `ServiceResult`/Envelope and
REST/MCP read wrappers. Payloads carry catalog identity, coverage, exact total
known matches and entries as applicable. Do not add fields to old inventory
responses or change old tool semantics just to expose catalog data.

### Coverage is not a disguised empty result

Coverage describes the entire scoped candidate set, not just a returned page:
known/unknown tag observations, eligible publication counts and technical states
(missing, usable, partial, unsupported, failed). Report which coverage matters to
the requested filters. A supported observation may legitimately describe no known
variant; an absent observation means not indexed, not no variant exists.

Technical queries may return known positive matches with explicit incomplete
coverage and warnings. The documented `total_matches` counts confirmed matches in
known metadata only. A zero-match response with missing coverage must explicitly
say it is not proof of absence. MCP descriptions and CLI output preserve this
qualification. Strict source corruption/identity mismatch/unsupported durable
schema refuses the selected read; do not silently treat it as missing metadata.
Exhausted scan/read/serialization budgets fail, never return a truncated success.

### Facets

`facet` selects exactly one of `tag`, `format`, `quantization_method`, or
`quantization` per request. Apply the same full query scope/filters before counting,
then count distinct matching repositories per value, not files/shards/revisions.
Technical facets derive values from the actual eligible matching variants, not an
unrelated variant in a matched repository. Tag facets use effective operator tags,
never imported upstream tags. Return counts in deterministic value order with
pagination and the same coverage/catalog identity. No disjunctive/self-excluding
facet semantics or hierarchy is implied in the first release.

### Pagination and races

Cursors bind normalized filter sets, route/tool, repository/exact instance scope,
installed policy identity and complete selected visible row/source content,
including current curation and coverage changes. Reordered duplicate tags do not
change scope. Tag-only edits, current-reference changes, repair, prune, enrichment
and relevant visible coverage changes invalidate continuation. Use the existing
classified stale-cursor behavior; never silently skip or restart a walk.

A query need not provide a global archive snapshot. Within its bounded collection,
validate the same authoritative identities used to construct positive matches.
A publication that disappears before a following exact read produces the existing
explicit refusal. Sanitize before digesting, enforce shared worker/queue/wire limits,
and avoid rescanning payloads even on an uncached query. Small page size must not
bypass aggregate scan limits.

## 9. REST contract, then the API-backed client/CLI

Proposed paths are relative to the existing `/api/v1` and public-prefix handling:

| Route | Authority and behavior |
| --- | --- |
| `GET /catalog/search` | REST reader/writer; one page of repository hits |
| `GET /catalog/facets` | REST reader/writer; one selected paged facet |
| `GET /catalog/repositories/{type}/{namespace}/{name}` | REST reader/writer; bounded detail without an unbounded nested variant collection |
| `GET /catalog/repositories/{type}/{namespace}/{name}/variants` | REST reader/writer; model-only paged variants; optional exact SHA/publication pair |
| `POST /catalog/refreshes` | REST writer only; keyed, serialized offline metadata operation |

REST search maps `type` to `repository_type`, repeated `tag_all`/`tag_any` to
`tags_all`/`tags_any`, and uses the other field names above. Reject unknown keys,
repeated scalar parameters, nonempty GET bodies, permissive numeric coercion,
path/URL input and over-budget requests just like the existing routes.
The detail/variant routes use already validated repository path components.
Detail may accept only the explicitly documented scope/exact identity parameters.
A detail record with zero published revisions is valid for a configured repository.

Refresh body: `selectors=[]`, `revision_scope="retained"`, `tags=true`,
`technical=true`, with at least one of the last two booleans true. Selectors are
bounded canonical whole-repository identities, not arbitrary paths or revision
suffixes. Empty selection means configured-plus-retained union. Unknown selectors
refuse. Tag-only refresh of a configured not-yet-published entry is valid. Technical
refresh skips unarchived entries with an explicit status; it never downloads them.

Refresh uses installed authority, normal writer lock/preflight/recovery guards,
existing keyed operation receipts/events/result observation and fresh scope checks
after waiting. It never contacts the Hub, copies models, verifies tensor hashes,
changes configuration, initiates repair or increases integrity confidence. No
background task facility separate from the existing operation lane is introduced.
Use a new idempotency key for a new refresh after tag changes; reuse of an existing
key observes the originally admitted operation, never silently captures new intent.
Command/result kinds and stored operation compatibility must be assessed explicitly.

Add typed base-client methods and proposed CLI commands:

```text
hfcache search [--type model|dataset] [--tag TAG ...] [--any-tag TAG ...]
               [--format FORMAT] [--quantization SCHEME]
               [--quantization-method METHOD] [--bits N]
               [--scope archived|configured|all] [--revision-scope current|retained]
hfcache tags [--scope ...] [--type ...]
hfcache catalog show TYPE:ID
hfcache catalog variants TYPE:ID [--revision-scope ...]
hfcache catalog refresh [TYPE:ID ...] [--tags-only | --technical-only]
```

Use current global JSON/quiet/client credential conventions and operation
observation/detach/idempotency behavior; do not invent conflicting flag meanings.
Expose the remaining query fields in help or document their explicit SDK-only
status consistently. `search` defaults match REST. `tags` requests the tag facet.
CLI collection is complete or explicitly fails on a client budget/race; it never
falls back to direct local archive access. No model bytes travel through these APIs.

## 10. MCP contract, after REST/client completion

Register exactly five additional names at this baseline:

| New tool | Scope |
| --- | --- |
| `search_models` | Shared catalog query with type fixed to model |
| `search_datasets` | Shared catalog query with type fixed to dataset; no quantization arguments |
| `get_catalog_entry` | Validated model/dataset identity; same detail semantics |
| `list_model_variants` | Exact model identity, same pagination/optional exact publication pair |
| `get_catalog_facets` | One named facet and typed shared filters |

Nine existing names plus five new names equals fourteen. Update the explicit
allowlist, descriptions, protocol, adapter, import/capability guards, snapshots,
capabilities and all human references to the nine-tool count in the same package.
If the live checkout gained unrelated tools after review, preserve their authorized
contract and record the reconciled exact set; do not delete or expose extra names
merely to reach fourteen.

Keep the narrow app-owned async metadata read adapter. Tools receive no request,
app, credential, Hub client, writer helper or refresh method. They are explicitly
read-only, non-destructive, idempotent and closed-world, but actual capability
separation—not annotations—enforces that. No `catalog_refresh`, tag mutation,
config install, download, verification or arbitrary tool dispatcher is added.
MCP/REST bearer classes remain distinct and authorization covers the whole archive.
Retain stateless transport, finite responses, fixed sanitized failures and shared
resource limits. No resources/prompts/OAuth/task system is introduced by this plan.

## 11. Documentation and versioning

Create a human `docs/discovery.md` for tagging, model/dataset examples, searches,
coverage/provenance, exact variants, refresh and failure interpretation. Update
existing config/API/client/CLI/MCP/server/Cockpit/operations/schema/security/consumer
contracts in the same package that changes behavior. Update architecture,
invariants and affected technical ADRs explicitly, including the auxiliary-file
transaction exception, durable schema/rollback and MCP allowlist amendment.

Human docs describe the supported product, not CAT task progress. Do not put work
package IDs, active plan pointers or links into `docs/agents/` in human guides.
Keep implementation evidence only under `docs/agents/`. Preserve changelog and
release-note conventions without tagging or deploying a release.

All old examples without tags, original inventory operations and existing MCP
tools remain supported. Test base reader, REST server and server+MCP installation
profiles. No silent dependency upgrade, optional-framework import in the base
reader, archive format rewrite, storage fallback or production acceptance claim.
