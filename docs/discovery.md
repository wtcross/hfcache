# Tags and local discovery

Configuration tags, Cockpit authoring, curation identity and supplemental record
storage, static declarations, GGUF headers and scoped AWQ/GPTQ variants are
supported, including sync/repair capture and the typed offline refresh service.
REST/client and MCP discovery support below remain proposed; this contract alone
does not make those commands available. Existing inventory and the nine existing MCP tools keep their
current behavior until the corresponding interfaces are implemented.

## Operator tags

Repositories have one optional direct `tags` list. Tags organize models and
datasets; they do not grant access, select files, change retention or schedule
downloads. There are no categories, groups, expected variants, hierarchy or
separate editable annotation store. Upstream declarations and technical metadata
remain separate from operator tags.

The shared normalizer accepts a list or tuple of at most 64 strings before
deduplication, each at most 128 raw characters. Trim outer ASCII spaces, lowercase
ASCII letters and require `[a-z0-9][a-z0-9._:/-]{0,63}`. Reject invalid values
without echoing their contents. Sort and deduplicate canonical values. Colons and
slashes have no path, wildcard or inheritance meaning. Omitted and empty lists
are equivalent. Never put credentials in tags.

Current validated configuration supplies tags, including empty lists, for enabled
and disabled repositories. Unmanaged retained repositories use only an actual
last writer-observed snapshot (`tag_origin=last_observed`), or expose empty tags
with `tag_origin=unknown`. Current configuration has `tag_origin=configured`.
Expose nullable `tag_observed_at`; historical observations are never current
configuration. Removing an entry before capture cannot create historical labels.
A surviving snapshot cannot resurrect a purged repository.

The existing operational policy fingerprint excludes tags and keeps its original
canonical representation. A separate curation fingerprint hashes a schema-1
canonical representation of all configured `(type, id, normalized tags)` entries,
including empty and disabled entries, sorted by identity. Candidate installation
continues to compare complete candidate and base bytes, never policy hashes alone.
There is no remote configuration installation or tag-edit API.

## Durable supplemental records

The approved extension is beneath `published/metadata/`:

```text
tags/<type>/<namespace>/<name>.json
observations/<type>/<namespace>/<name>/<sha>/<publication_id>.json
```

Type path components use the existing plural `models`/`datasets` grammar. Only
central layout builders and validated identities may construct these paths.
`RepositoryTagSnapshot` schema 1 records kind, archive UUID, repository type/ID,
canonical tags, observation time, curation fingerprint and
`source=installed_config`. It is authoritative only for last-observed historical
labels, which must be backed up; they cannot be reconstructed from present config.

`PublicationObservation` schema 1 records kind, archive UUID, repository type/ID,
SHA, publication ID/generation, manifest locator/digest, extractor version/time,
status, selected attributed sources, model variants or dataset declarations and
bounded diagnostics. Sources must belong to the complete authoritative manifest.
Observations are derived interpretations, never publication or integrity evidence.
Existing manifests, references, verification confidence and trees stay unchanged.

Both families require strict fields, bounded strings/collections, deterministic
ordering and independently versioned atomic JSON. Unsupported, malformed or
unsafe existing canonical records refuse replacement and remain preserved.
Selected corrupt records refuse reads; absence means missing coverage. Only
temporary siblings named `<canonical-name>.tmp-<16 lowercase hex digits>` may
be ignored; unknown siblings are refused. No aggregate on-disk index is
introduced. Pruned/purged records may remain inert; automatic garbage collection
is outside this contract.

Each record replacement and approved directory creation is an independent,
idempotent unit under the common local writer lock, initialized archive identity,
storage preflight and unfinished-journal guards. This narrowly excepts these
adjuncts from journal-before-mutation. Use temporary sibling, file fsync, atomic
replace and parent fsync. There is no multi-file atomicity or journal replay.
Crashes can leave mixed observation times, always whole visible records. The
exception does not cover any existing transaction, verification catalog, tree,
manifest, reference, prune, repair or initialization. An existing valid archive
may acquire this namespace through writer work; never rerun initialization.

### Sync and repair capture

Production sync captures after all download producers join and retention finishes,
before recording its repository results and report. The exact caller-owned sync
journal may remain open only at `journals_reconciled`; other unfinished journals
refuse supplemental writes. A repair journal waiting at `repair_committed` is
safe only with its canonical, matching pending retirement record and exact
retained replacement manifest. Its grace cleanup remains open. Corrupt journal
schemas, identities and checkpoint order refuse capture.

Capture reads the current validated installed curation once under the same lock,
after the archive work, and projects only tags, source fingerprint and time.
The admitted operational policy, repository selection and credentials remain
unchanged. A source that changes archive authority or cannot be validated does
not fall back to stale tags; technical extraction can still proceed. Removal
before capture creates no historical labels and leaves any prior snapshot intact.
Present empty or disabled entries can replace their tag snapshots.

Retained-SHA sync refreshes observations without a new download, publication ID
or generation. Repair observes its exact replacement and preserves the retired
instance's manifest and observation. Optional capture errors produce `HFWRN011`
and missing or failed coverage; they never roll back or reclassify valid
publication integrity, swallow domain errors or change its successful exit code.
Existing repository statuses retain their archive meaning; a newly published
revision with supplemental warnings uses `completed_with_warnings`.

One invocation shares all extraction ceilings across publications, plus a
4096-record attempt ceiling and 128 MiB aggregate serialized-record ceiling.
Failed attempts count. Curation projection refuses more than 100,000 configured
repositories. Each write checks available capacity for the serialized record
plus a 64 KiB directory allowance. Exhaustion preserves earlier whole records
and reports incomplete capture; near-reserve `HFWRN005` warnings remain visible.
No deferred callbacks, background writers,
dependency downloads or additional pruning are introduced.

### Offline refresh service

Refresh accepts at most 256 raw canonical whole-repository selectors, deduplicated
and sorted by identity; revision suffixes, paths, unknown identities, invalid
revision scopes, non-boolean flags and both outputs disabled refuse. Empty
selection means current configured identities plus repositories with authoritative
retained per-SHA refs. Metadata snapshots and orphan instance directories
cannot create scope. Current revision selection follows the explicit current ref
and its matching retained ref, never the greatest generation.

The service acquires the common guard once, obtains fresh installed curation and
resolves all scope/result bounds before writing. It uses the admitted storage and
archive authority. Unavailable fresh curation refuses without a stale fallback.
Bounded journal checks refuse unfinished or operator-required work; refresh never
applies recovery, repair, prune or cleanup as a side effect. A committed repair's
validated pending retirement remains safe as above. Existing preflight probes
retain their normal behavior.

At most 256 repositories and 512 publications fit one refresh, with a 1 MiB
result budget reserved before mutation. One bounded metadata reader and the
shared invocation extraction/write budgets cover the full operation. Tag-only
refresh can capture disabled or unpublished entries. Unmanaged tags are explicitly
skipped and existing historical snapshots remain intact. Technical work without
a retained publication is explicitly skipped. Each record independently reports
write success or failure; writing an unsupported/failed observation succeeds as
a record while remaining incomplete technical coverage. Partial writes remain
visible with exact publication identity and counts. No successful truncation,
network, credential resolution, payload integrity hashing, configuration write
or separate background work is permitted.

## Static extraction and variants

Only writer-owned post-publication work and explicit offline refresh may read
payload metadata. Use exact manifest-listed ordinary files with no-follow access.
Never execute code, loaders, YAML objects, model libraries or external URLs.
Initial ceilings are 1 MiB per card/JSON file, 64 MiB actual metadata reads and
4096 candidates per publication, structural depth 64 (JSON 32) and retained text
64 KiB, preferring summaries of 2048 characters. Counts, skipped values, seeks,
aliases and aggregate sync work must also be bounded before allocations.

The `static-1` declaration parser uses only the standard library. It accepts a
root `README.md` front matter block and manifest-listed `config.json`,
`adapter_config.json`, `dataset_info.json` and `dataset_infos.json`, including
recognized JSON files within subdirectories. YAML support is deliberately limited
to block mappings/sequences, quoted/plain scalars and simple scalar flow lists
(including JSON string lists). Mixed quoted/plain flow lists, anchors, aliases,
merge keys, custom tags, block scalars and complex flow structures are unsupported. All physical lines count
toward a 20,000-line ceiling, and skipped content counts toward a 100,000-token/
node ceiling before containers are allocated. JSON rejects duplicate keys,
nonfinite numbers and invalid Unicode. No looser parser is attempted.

Only task, language, license, base-model and upstream-tag strings are retained.
Dataset configuration, split and feature names come from recognized declaration
contexts; `configs[].data_files[].split` is a declaration even when its path is
external or absent. Filename extensions can suggest formats, excluding recognized
metadata JSON files; payloads are not opened to confirm dataset formats.
Summaries contain at most 64 values per source field and 2048 characters per
value, with a 64 KiB aggregate retained-text ceiling. Sources retain exact path and
manifest-expected digest, without claiming a fresh integrity check. Registered
secret values and recognized credentials are suppressed before retention.

Extraction status is `complete`, `partial`, `unsupported` or `failed`. Missing
optional declarations are not failures. Unsupported/failed fields stay unknown.
An unsupported construct yields `unsupported`, malformed/unsafe input or exhausted
limits yield `failed`, and independent useful observations surviving either yield
`partial`. Diagnostics are fixed classifications without rejected source contents.
The supplemental warning class is `HFWRN011`; warnings do not change integrity or
the successful publication exit classification.

Writer metadata work has an eight-million-step ceiling and 100,000 manifest
members per publication. The byte/candidate ceilings above still apply. Header
access uses unbuffered descriptors: accounting measures returned bytes without
user-space read-ahead into tensor data. Exhaustion is explicit incomplete
coverage; it does not bypass the limits or change publication evidence.
Supplemental extraction failure warns without invalidating a valid publication;
producer work must still join before releasing the lock. Dataset formats and
static split/configuration/feature declarations remain attributed observations,
never inferred physical splits, row counts or external payload completeness.

A model variant identifies one logical member set in one exact publication.
Expose deterministic variant ID, format, encoding, quantization scheme/method,
nullable known bits, role, members/count, known weight bytes, completeness,
evidence grade/sources and diagnostics. Completeness is `complete`, `incomplete`
or `unknown`. Supported complete primary-model variants alone satisfy positive
technical searches. Availability describes retained declared content; it is not a
fresh filesystem/hash check or runtime/hardware compatibility claim.

GGUF is a format. Recognized header mappings establish `ggml` method and exact
scheme; filenames alone cannot prove quantization. F16/F32 are float encodings.
Only explicit agreeing split identity/count/indices within the same publication
form a complete shard set. Ambiguous, contradictory, auxiliary, adapter and
projector candidates remain inspectable without becoming primary-model matches.
AWQ/GPTQ declarations bind to an unambiguous same-directory weight bundle and
validated manifest-contained index members. A declaration/index/LFS pointer alone
does not establish complete weights. Safetensors format is independent of method.

### Supported GGUF interpretation

The reader accepts version 3 little-endian headers. Big-endian files, other
versions, unknown/removed/guessed enums and unsupported tensor types remain
inspectable candidates. Pinned primary references are the
[GGUF structure](https://github.com/ggml-org/ggml/blob/6af560d55df03ad92116e3c0a697779584477e85/docs/gguf.md),
[file-type and tensor-size enums](https://github.com/ggml-org/llama.cpp/blob/412a363c655b479279d3050d0d1c67a5733697b4/gguf-py/gguf/constants.py)
and [split writer](https://github.com/ggml-org/llama.cpp/blob/8f97d82da33b5f4262a87b9c4208298378b8a165/tools/gguf-split/gguf-split.cpp).
No executor or GGUF package is imported.

| `general.file_type` values | Encoding/scheme in corresponding order |
| --- | --- |
| 0, 1 | F32, F16 (float encodings; no quantization method/scheme) |
| 2, 3, 7, 8, 9 | Q4_0, Q4_1, Q8_0, Q5_0, Q5_1 |
| 10–18 | Q2_K, Q3_K_S, Q3_K_M, Q3_K_L, Q4_K_S, Q4_K_M, Q5_K_S, Q5_K_M, Q6_K |
| 19–24 | IQ2_XXS, IQ2_XS, Q2_K_S, IQ3_XS, IQ3_XXS, IQ1_S |
| 25–31 | IQ4_NL, IQ3_S, IQ3_M, IQ2_S, IQ2_M, IQ4_XS, IQ1_M |
| 32 | BF16 (float encoding; no quantization method/scheme) |

Known quantized mappings use method `ggml`. Nominal bits are 4/5/8 for the
corresponding simple Q schemes and 16/32 for float encodings; mixed K/IQ schemes
retain unknown bits. Tensor types support offset arithmetic and negative
contradiction checks, never inference of an exact majority scheme. A quantized
declaration with only float/integer tensors, or a float declaration containing
quantized tensors, cannot become a complete positive variant. Declared float
encodings require the corresponding tensor kind; F32 permits only F32, while F16/
BF16 may also include F32 tensors.

Every metadata key is a bounded ASCII hierarchical name; duplicate keys fail.
Headers cap metadata/tensor counts at 100,000, array elements at 1,048,576,
nesting at 64 and individual strings at 64 KiB (keys 256 bytes, tensor names
64 bytes, retained identities 2048 characters). Ignored arrays/strings consume
the shared work/byte budget; no array is allocated from an unchecked count.
Alignment must be a multiple of eight at most 65,536. Tensor dimension products,
aligned offsets, nonoverlapping extents and file bounds are checked from header
data; neither padding nor tensor bytes are read.

Split grouping requires the exact publication, directory and entire canonical
filename prefix before `-00001-of-00002.gguf`. Every member must explicitly agree
on zero-based `split.no`, positive `split.count`, and `split.tensors.count`, with
the complete unique index range, matching filename ordinals and total tensor
count. Duplicate tensor names across shards refuse completeness. Shard zero
owns model/scheme declarations; later shards may omit them, but present values
must agree. An empty tensor table in shard zero is valid for a complete nonempty
set. Missing shard zero, conflicting/missing metadata or different directories/
prefixes cannot be combined. Source attribution identifies the declaring shard.

Primary role requires a recognized model architecture and model/default type.
Explicit adapter/projector/imatrix headers and LoRA tensor names suppress primary
role. Conservative `mmproj`, `mtp-`, adapter/LoRA and canonical `-LoRA`/`-vocab`
filename hints only downgrade role. Unknown roles stay visible with incomplete
coverage; zero-tensor standalone files are not primary weight sets. Completeness
describes the retained declared member set and header bounds, never tensor
integrity, model loadability or runtime compatibility.

### Supported scoped weight declarations

The supported producer schema is an explicit `quantization_config` object in a
same-directory `config.json`, with literal `quant_method=awq` or `gptq`, strict
integer `bits` and optional `group_size`. The primary pins are
[Transformers configuration](https://github.com/huggingface/transformers/blob/0bc252863a4e5c0e709893664cc57369ebcd7353/src/transformers/utils/quantization_config.py)
and [index resolution](https://github.com/huggingface/transformers/blob/f4410762062c274fb53471e551e62b377df44cc1/src/transformers/utils/hub.py).
The initial AWQ subset requires explicit 4-bit declarations; GPTQ accepts explicit
2/3/4/8 bits. Missing/invalid/unsupported widths stay unknown; runtime defaults are
never filled in. Group sizes are positive integers or `-1` (per-column, represented
as null with `per_column_group_size`). An absent group stays null with
`group_size_unknown`. Dynamic per-layer layouts are unsupported.

Format is independent: `safetensors` or `pytorch_bin`, method `awq`/`gptq`, nullable
scheme/encoding and declared nominal bits. Missing quantization declarations
never establish unquantized weights. A primary role requires a recognized static
model type; adapter configuration/names and projector/sidecar names only downgrade
role. No runtime class is imported or instantiated.

One directory may bind one canonical singleton (`model.safetensors`,
`pytorch_model.bin`, or attributed adapter equivalents) or one recognized
`model.safetensors.index.json`/`pytorch_model.bin.index.json`. An index must have a
nonempty `weight_map`; repeated filename values across tensor keys are normal and
count once. Duplicate JSON keys, aliases/escaping/nested paths, known optimizer/
training artifacts, absent members and mixed formats refuse completeness. Members
must be canonical same-directory manifest names. Named shard ordinals/counts must
form the complete set. Shards without an authoritative index remain candidates.
Multiple alternatives/index formats/extra weights in one directory are ambiguous;
a malformed index never falls back to an available singleton. Independently
configured subdirectories remain separate; root declarations never apply to child
weights. Bytes total the identified members once, including their headers.

Git-LFS pointers, empty/truncated/unsafe members and contradictory headers are
not available sets. Safetensors reads only its bounded length-prefixed JSON header
using the [pinned format](https://github.com/huggingface/safetensors/blob/62e4d8b86063a6e5f8967547fa09a09f67420e2a/README.md#format):
known byte-sized float/integer/bool dtypes, bounded shapes and overflow-safe
products, exact nonoverlapping offsets and full declared data coverage. Header
bytes stop before tensor content. A declared quantized set requires some nonempty integer
storage in those headers; float-only storage is insufficient. Unknown dtypes and
oversized headers remain unsupported. Binary members use only an eight-byte
ZIP/pickle-container sniff (or bounded LFS-prefix detection) and a conservative
128-byte minimum; no archive or pickle deserialization occurs. These checks
establish bounded static declarations and members, never tensor correctness or
functional compatibility.

Standalone legacy `quantize_config.json`/`quant_config.json`, including sidecars
beside a nested declaration, are unsupported pending an explicit producer-schema
extractor. Custom unindexed basenames, nested index members and other layouts
remain attributed candidates. A quantization config without weights records
missing coverage; an ordinary config without optional weight candidates is not
an extraction failure. Work/source/member limits apply across every scope.

## Queries, coverage and pages

One bounded transport-neutral read service owns exact predicates and projections.
Reads are lock-free, write-free, network-free and never open payload files, hash,
refresh, resolve credentials or instantiate a writer/Hub capability.

| Field | Meaning |
| --- | --- |
| `repository_type` | Optional model/dataset; omitted searches both |
| `q` | At most 256 characters, case-insensitive literal substring of ID/tags |
| `tags_all`, `tags_any` | Shared-normalized exact sets; empty adds no constraint |
| `tag_source` | `current_or_last_observed` default, or `current_only` |
| `scope` | `archived` default, `configured` or identity-deduplicated `all` |
| `revision_scope` | Explicit `current` default or authoritative `retained` refs |
| `format` | Exact normalized format identifier |
| `quantization`, `quantization_method` | Exact scheme/method identifiers |
| `bits` | Strict integer 1–64 |
| `max_variant_bytes` | Strict nonnegative bounded logical weight bytes |
| `limit`, `cursor` | Bounded pages with existing stale-cursor refusal |

Fields combine with AND; every technical predicate must match the same variant
in the same publication. Unknown valid values yield zero known matches. Explicit
dataset plus model-only filters refuses; omitted type with such filters selects
models. Dataset format filters use observed dataset formats. `current_only`
excludes historical labels from predicates, tag text and facets, preserving
attributed detail. Configured scope includes disabled/unpublished entries;
snapshot-only records never add entries.

Return one repository hit sorted by `(type, id)`, state, tags/provenance,
coverage, exact `matching_variant_count` and at most one deterministic
representative variant. Page the full variant set separately. Exact detail uses
both SHA and publication ID or neither; vanished identity never falls back.
Dataset summaries do not invent model fields.

Schema-1 catalog payloads inside existing Envelope/read wrappers carry catalog
identity, entire scoped coverage, exact known total and paged entries. Coverage
counts known/unknown tags and eligible publications by missing/usable/partial/
unsupported/failed technical state. Incomplete coverage explicitly qualifies
zero known matches: it is not proof of absence. Exhausted scan/read/wire budgets
refuse instead of truncating success. Sanitize registered secrets before matching,
counting and digesting; hidden substitutions cannot influence cursor identity.

Facets select one of `tag`, `format`, `quantization_method`, `quantization`. Apply
the full query, then count distinct matching repositories per value from eligible
matching variants, never unrelated variants/shards/revisions. Sort values and page.
Cursors bind normalized scope, route/tool, exact selectors, archive/policy identity,
visible curation, authoritative refs, observations, coverage and ordering. Relevant
edits/repair/prune/enrichment refuse continuation. No global snapshot is promised.

The read projection withholds opaque curation fingerprints (`null`): historical
fingerprints can encode labels outside the visible projection. Catalog identity
instead hashes visible policy, labels and exact publication summaries. Secret-bearing
labels, source values and paths are suppressed before predicates and counts; a
variant with suppressed membership is omitted as a whole. Nullable sensitive
technical values become unknown. Such suppression qualifies coverage as partial.
Unknown extractor versions cannot establish positive technical matches. The
representative is the first eligible match ordered by generation, SHA, publication
ID and variant ID. Explicit SHA/publication detail selects that exact retained
instance regardless of the default current scope; both selectors are required.
Queries share finite metadata budgets and a 32 MiB visible projection ceiling,
including rows beyond the requested page. Oversized detail refuses rather than
silently dropping observations.

## Transport and refresh boundary

Planned REST reads are `/catalog/search`, `/catalog/facets`,
`/catalog/repositories/{type}/{namespace}/{name}` and its `/variants` child under
`/api/v1`. REST maps repeated `tag_all`/`tag_any` and `type` to shared fields.
Retain strict unknown/repeated scalar/body/numeric/path rejection, authentication,
finite response budgets and existing wrappers. Readers/writers may read.

Writer-only `POST /catalog/refreshes` uses existing keyed serialized operations,
receipts and exact result observation. Strict body fields are whole-repository
`selectors=[]`, `revision_scope=retained`, `tags=true`, `technical=true`, with at
least one boolean true. Empty selection means configured/retained union; unknown
selectors refuse. Fresh scope and installed curation are checked after lock wait
without replacing admitted operational authority. Unpublished technical work is
explicitly skipped; tag-only capture is valid. Refresh never downloads, verifies,
repairs, installs config or increases integrity confidence. A new capture needs a
new key; replaying a key observes the original operation.

The independent client and CLI expose search, tag facets, catalog detail/variants
and writer refresh through REST, preserving JSON evidence, qualified human output,
complete bounded collection and uncertain-operation handles. No local fallback.
After these interfaces are accepted, exactly five additional read-only MCP tools
are planned: `search_models`, `search_datasets`, `get_catalog_entry`,
`list_model_variants`, `get_catalog_facets`. Existing nine tools remain unchanged.
No MCP refresh/mutation, resources, prompts or generic dispatcher is authorized.
The narrow app-owned async read capability and separate credential classes remain;
authorization covers the entire archive, never per-tag ACLs.

## Compatibility and operation

Old tag-free configurations and old evidence formats remain supported. New tags,
metadata directories and operation kinds can be refused by older binaries despite
unchanged old schema versions. Compatibility must be observed with actual target
binaries and disposable fixtures. Rollback requires executor drain, preserved
metadata/control evidence, a reviewed backup/snapshot or validated compatible
layout, tag-free target-compatible config and validation with the target binary.
Never delete new state to force old startup. No automatic metadata cleanup or
production rollout follows from feature implementation.
