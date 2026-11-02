# Find models and datasets in the Library

The Library in unreleased source reads the existing local catalog and inventory
APIs through the authenticated HTTPS interface. It does not search the live Hub,
download content, refresh observations or change configuration. Check
[interface availability](README.md) before using an installed release.
[Repository details](repository-details.md) provide exact-publication evidence
and bounded README display. [Configuration and tag editing](configuration-and-tags.md)
is a separate explicit workflow; filtering never stages an edit. Use
[Operations](operations.md#choose-a-job-and-its-effects) to review and submit a
job deliberately.

The current [desktop source-fixture screenshot](images/library-source-fixture-after-1440x1000.png)
and [mobile source-fixture screenshot](images/library-source-fixture-after-390x844.png)
show the built source interface at 1440×1000 and 390×844 CSS pixels. The fixed
synthetic fixture loads25 rows,50 known matches and incomplete technical coverage;
these are illustrative owned fixtures, not installed or production measurements.
Matching [desktop before](images/library-source-fixture-before-1440x1000.png) and
[mobile before](images/library-source-fixture-before-390x844.png) captures preserve
the earlier layout on that same default fixture. Search and the first repository
identity now fit in both initial viewports with filters collapsed.

The earlier [desktop](images/library-desktop.png) and
[mobile](images/library-mobile.png) screenshots remain historical build0.2.20
images from an isolated deployment with real Caddy/API and simulated storage
metadata. They are not relabelled as the current layout.

Search, repository type/scope, known matches and results lead the Library.
**Filters and page size**, **Scope and coverage** and **Operator tags** use
labelled disclosures.
Open a disclosure with Enter or Space on its summary; closing it keeps its form
values and makes no request. A compact **Applied** summary describes the
submitted query even when technical filters are closed. Unsubmitted form edits
are marked separately; they do not describe the loaded result scope. **Clear
filters** resets both the query and form deliberately.

Hidden fields remain part of **Apply filters**. If a hidden value is invalid,
Apply opens its group and focuses the field or associated error so it can be
corrected. Closing a group returns keyboard focus to its summary when needed.
Changing disclosure state never changes bookmarks, selections or query meaning.

## Choose the scope before searching

Open **Library** and select **All repositories**, **Models** or **Datasets**. A model and a
dataset can have the same repository ID; their types remain separate identities.
Choose the repository and publication scopes that answer your question:

| Scope | Included evidence |
| --- | --- |
| All repositories | The union of currently configured identities and authoritative archived identities, without duplicate rows for an identity. This is the Library default. |
| Configured | Current configuration entries, including disabled repositories and repositories with no publication yet. Configuration is intent, not proof that bytes exist. |
| Archived | Repositories retained by authoritative archive metadata, including unmanaged repositories removed from current configuration. A leftover tag snapshot alone cannot create a row. |
| Current publications | Technical predicates use each repository's authoritative current publication. This is the default publication scope. |
| Retained publications | Technical predicates can match any publication still retained by authoritative revision references. A match need not describe the current publication. |

Configured, enabled and archived are independent facts. A configured disabled
repository may already be archived; an unpublished configured repository has no
retained publication; an unmanaged archived repository has no current enabled
setting. Selecting a scope neither enables synchronization nor changes retention.

## Search IDs and operator tags

Enter text in **Find repositories**. Search is a case-insensitive, literal
substring of repository IDs and the eligible operator tags. It is not a regular
expression, README full-text search, an upstream tag search or a Hub lookup.
Whitespace remains literal; the browser does not silently trim or reinterpret
your text. Search is bounded to 256 Unicode code points, and the server retains
its authoritative case-folding rules. Invalid Unicode, control characters and
directional override/isolate controls are visibly refused.

Changing between **All repositories**, **Models** and **Datasets** keeps the text
currently entered in **Find repositories**, including text still waiting for the
search debounce. Clearing that text before changing type removes the search
predicate.

Exact tag filters use the shared configuration normalizer: trim outer ASCII
spaces, lowercase ASCII letters, sort and deduplicate. At most 64 raw tag values
are accepted, each at most 128 raw characters; canonical tags use
`[a-z0-9][a-z0-9._:/-]{0,63}`. Colons and slashes are ordinary label characters,
without hierarchy or wildcard meaning. Never enter credentials in search or tags.

- **Require all tags** requires every selected tag.
- **Match any tags** requires at least one selected tag.
- When both sets are supplied, both conditions apply. Other filters also combine
  with AND; matching a tag cannot bypass a technical predicate.

For example, the synthetic labels `team:research`, `task:chat` and `task:vision`
can express “all of `team:research`, and any of `task:chat` or `task:vision`.”
Enter each group as comma-separated tags, then choose **Apply filters**.
**Clear filters** resets the filters; **Refresh library** repeats the current
bounded reads. These names illustrate grammar only; they are not records or
counts from an installed archive.

Current configuration supplies tags for configured repositories, including a
known empty list and disabled entries. **Last observed** labels come only from
an actual prior writer snapshot for an unmanaged retained repository. Their
timestamp is historical, not proof of the current configuration. **Unknown**
means no authoritative label source is available; an empty display is not proof
that the repository never had tags.

The default tag source includes current tags or last-observed tags as appropriate.
Current-only filtering excludes historical labels from tag predicates, search
text and tag facets. It does not turn a historical observation into current
curation or remove its provenance. Tags grant no access and prove no integrity.

Use **Edit tags** on a configured repository's detail page to open the current
configuration intent in Administration, not to rewrite the selected publication.
Read installed configuration explicitly and choose **Edit requested repository**;
navigation itself does not fetch or prefill configuration from catalog facts. For an unmanaged
repository, historical tags remain read-only; **Reconfigure repository** opens an
explicit complete configuration entry. Disabling or removing configuration does
not remove archived rows. A later Library read reflects current tags and
curation identity; it does not rewrite an earlier writer-observed snapshot.

## Combine technical filters

Format applies to both types. Quantization scheme, quantization method, bits and
maximum logical variant bytes apply only to models. Selecting **Datasets**
deliberately clears those model-only predicates and announces the change; it
does not send an invalid dataset query. Dataset formats remain static observed
declarations, without inferred row counts, physical splits or model fields.
With no explicit repository type, a model-only predicate selects models rather
than applying model fields to datasets.

All model technical predicates must match **one supported complete primary
variant in one publication**. A format on one variant cannot combine with bits
or a quantization scheme from another. Adapter, projector, auxiliary, incomplete
and unknown variants do not become positive primary-model matches. An eligible
variant describes retained content, not a fresh hash check or hardware suitability.

GGUF and safetensors are formats; quantization method and scheme are separate
facts. Bits must be an integer from 1 through 64. A maximum size is a nonnegative
logical byte count, represented exactly; unsupported large integers refuse
rather than round. A syntactically valid but unknown filter identifier produces
zero known matches, without inventing a supported-value list or a GPU-fit claim.

The table can show one deterministic representative of the eligible matching
variants and their known count. That representative is not a complete variants
listing and, with retained scope, need not be the current publication. Current
publication inventory and exact qualified variant evidence stay separately
attributed when they differ.

## Read counts, sizes and coverage together

**Known matching repositories** counts matches across the selected query, not
just the loaded page. Coverage describes the candidate repository/publication
scope before search and technical predicates narrow it. Loaded rows describe
only the current page. Do not use one of these counts as another's denominator.

The coverage disclosure distinguishes usable, partial, unsupported, failed and
missing observations. Its collapsed state retains a visible incomplete-coverage
warning, including zero known matches. Unknown tag coverage is separate. Zero known matches under
incomplete coverage is not proof of absence; inspect the visible coverage and
`HFWRN011` warning. Even 0 publications / 0 usable observations does not mean 100%
technical coverage. Unavailable, malformed or refused reads never become a
successful empty table.

Inventory/status data joins rows by authenticated authority, repository type and
ID. Logical byte/file counts attach only to their exact SHA/publication pair.
An independently read current publication can move while a retained catalog
representative remains valid; the interface must not attach the newer pair's
bytes or integrity to the older one. These reads are not one atomic global
snapshot. Missing supplemental metadata does not erase authoritative inventory.

File and variant sizes are logical sizes from declared metadata. They are not
physical disk usage, space savings, transfer requirements, RAM or GPU memory.
Hardlinks can make sums of logical sizes count shared storage repeatedly. The
Library does not invent archive-wide disk usage or global active-job totals from
one loaded page or browser recovery registry.

## Page and bookmark a bounded read

Choose 25, 50 or 100 in **Rows per page**. The interface requests bounded pages
rather than silently collecting every match. Facet counts describe distinct matching
repositories for each value under the full current query; they do not count
shards or unrelated variants. Facet lists show their loaded extent separately
from their total values. Use **Load more tags** when more tag facet values are
available. Each action replaces the displayed facet page rather than building an unlimited
combined list. Related inventory/status/revision reads cover only the loaded
repository selectors; their own bounded pages can leave enrichment unknown.

Changing filters or page size resets affected continuations. A stale cursor can
follow a tag-only edit even when the operational configuration fingerprint is
unchanged. The old page chain is discarded, with one automatic restart from the
first page per refresh attempt and a visible explanation. A second stale response
remains failed. At most 32 main-page positions are retained; reaching that page
limit is explicit. Repeated drift or exhausted scan/read/retention limits remains an
explicit refusal; it never triggers an unlimited read walk. Reducing page size
alone cannot guarantee that the entire scoped catalog scan fits its budget.
Narrow type, scope or predicates when appropriate.

Filters are stored in a bounded URL fragment after `#`, because the existing
authenticated shell does not accept query strings. For example, this synthetic
bookmark selects configured models whose ID or eligible tags contain `owned`:

```text
https://archive.example/ui/library#type=model&scope=configured&q=owned
```

Use the deployed public prefix when present. The fragment remains in the browser;
actual catalog API requests retain their normal supported query parameters.
Fragments and their encoded API queries each fit 8 KiB. Unknown, duplicated
scalar, malformed or oversized filter fields are visibly refused. Only tag-all
and tag-any fields may repeat. Continuation cursors are temporary page state and
are refused in filter fragments, rather than treated as durable bookmark
identity. Back/forward or reloading a valid filter bookmark repeats reads only.

If the connection, authentication or API instance changes, follow
[reconnect guidance](operations.md#reconnect-without-replay). Superseded requests
and private session data are invalidated; old counts must not appear current
after a failed refresh. For classified errors, incomplete zero results or stale
pages, see [Library troubleshooting](troubleshooting.md#library-search-and-pages).
