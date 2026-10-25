# Configuration and tags

The configuration API in unreleased source can read the installed editable
settings, validate managed edits and prepare a sizing preview. These procedures
use the API; they do not imply that a configuration editor is available in the
web interface. Configuration Apply is not implemented. Validation and preview
never install a file, change tags on disk or start synchronization.

Use the matching installed API/helper release and the separately provisioned
Basic administrator over verified HTTPS. Configuration administration requires
its explicit capability and independent host-policy permission. A REST writer
bearer alone does not grant access to the protected configuration workflow. See
[administrator deployment](deployment.md) and [host permissions](administration.md).

## Read the installed editable settings

1. Send `GET /api/v1/config` on the existing HTTPS endpoint. Include the public
   prefix before `/api/v1` when one is configured. The route accepts no path
   override or query parameters.
2. Retain the returned `base_revision` with the editable data. It identifies the
   complete installed bytes captured for that read, including tags, comments and
   formatting. It is opaque; do not derive it from a policy fingerprint or try to
   interpret it as a document hash.
3. Review `editable`, `editable_fields` and `protected_fields`. The response also
   identifies its schema and configured `archive_id`. These describe installed
   intent, not archive health, writable storage or available Hub credentials.

The editable projection contains all configured repository entries, including
disabled entries, tags and declared dependencies, plus these eleven settings:

| Setting | Accepted value |
| --- | --- |
| `storage.publication_mode` | `"hardlink"` or `"copy"` |
| `storage.minimum_free_space_gib` | Integer from `0` through `1048576` |
| `storage.minimum_free_space_percent` | Integer from `0` through `100` |
| `storage.maximum_revisions` | Integer `3` or `5` |
| `sync.max_workers` | Integer from `1` through `32` |
| `sync.lock_wait_seconds` | Integer from `0` through `86400` |
| `sync.continue_on_repository_error` | Boolean |
| `sync.dependency_policy` | `"warn"` |
| `sync.stale_staging_age_hours` | Integer from `1` through `8760` |
| `verification.lock_wait_seconds` | Integer from `0` through `604800` |
| `repair.retired_instance_grace_hours` | Integer from `168` through `8760` |

The [configuration contract](../configuration.md) explains the operational effect
of each setting. For example, reducing retention does not itself delete retained
revisions, and declaring a dependency does not add it to synchronization scope.

There is no complete TOML or protected-value view in this response. Protected
field descriptions identify what must be maintained outside this workflow:
archive root and UUID; Hub endpoint, token mode, credential name and expected
account; and the required verification algorithm and hashing policy. Server
policy is described as managed outside archive configuration. The configuration
schema is also fixed; server listeners, authentication, credentials and deployment
selectors belong to separate configuration domains. Never turn a hidden value or
a redaction placeholder into a replacement value.

## Prepare a managed edit

Both validation and preview accept the same exclusive body:

```json
{
  "managed": {
    "base_revision": "<base_revision from the configuration read>",
    "edits": []
  }
}
```

Replace the displayed placeholder with the actual token. Keep the same body for
validation and the subsequent preview. Do not add `candidate`, arbitrary TOML,
filesystem paths or JSON pointers. Managed plans derive their own scope; omit
`selectors` or leave it empty. Unknown fields, explicit nulls where values are
required, strings in place of integers and numbers in place of booleans refuse.

Choose edits from the following three forms. A request permits at most 256 edits,
one touch per `(type, id)` repository identity and one `settings-replace`.
An empty edit list is an explicit assessment of unchanged intent; it still
does not install anything.

### Add or replace a repository

An upsert replaces the **complete entry**, rather than merging the supplied
fields with the old entry. For example, this edit describes the complete desired
entry for the named model:

```json
{
  "kind": "repository-upsert",
  "repository": {
    "id": "google-bert/bert-base-uncased",
    "type": "model",
    "revision": "main",
    "enabled": true,
    "tags": ["text", "project:search"],
    "declared_dependencies": []
  }
}
```

Use the repository's actual intended values. `id` and `type` are required;
omitting another field resets it to its normal default: `revision="main"`,
`enabled=true`, `tags=[]`, `declared_dependencies=[]`. To change only tags, copy
the current entry from the editable projection and change its tags while
retaining the other fields. Do the same when disabling an entry or changing its
revision. Model and dataset entries with the same ID are distinct identities.

### Remove a repository from configuration

```json
{
  "kind": "repository-remove",
  "repository_type": "model",
  "repository_id": "google-bert/bert-base-uncased"
}
```

Removal requires an existing configured entry. It removes operator intent only:
archived publications remain and become unmanaged. Do not combine a removal and
an upsert for the same identity in one request.

### Replace selected settings

```json
{
  "kind": "settings-replace",
  "settings": {
    "sync": {"max_workers": 4},
    "storage": {"maximum_revisions": 3}
  }
}
```

This form replaces only the supplied supported settings. The `settings` object
and every supplied nested table must be nonempty. Omitted settings retain their
installed values. The eleven-field table above is the complete editable list;
root, UUID, Hub or credential fields cannot be smuggled into it.

## Normalize tags before reviewing a change

Tags are operator curation, not access controls, download filters or retention
rules. The backend trims outer ASCII spaces, lowercases ASCII letters,
deduplicates and sorts byte-wise. For example:

```text
["Coding", " coding ", "project:assistant", "vision/ocr"]
→ ["coding", "project:assistant", "vision/ocr"]
```

At most 64 raw tags are accepted, each at most 128 characters before
normalization. A canonical tag must match `[a-z0-9][a-z0-9._:/-]{0,63}`.
Nonstrings, empty tags, controls, internal whitespace and non-ASCII text refuse;
limits apply before duplicates are removed. Only outer ASCII spaces are
trimmed, so tabs and nonbreaking spaces are invalid. Colons and slashes have no
hierarchy, wildcard or filesystem meaning. Disabled entries retain their tags.
Keep secrets out of labels. See [tags and local discovery](../discovery.md).

## Validate, then preview sizing

1. Send the managed body to `POST /api/v1/config/validate` with
   `Content-Type: application/json`. Basic requests also require the exact
   configured HTTPS `Origin` and `X-Hfcache-Request: 1`; use the same authentication
   as the read. Do not put a password or token in a URL or request body.
2. Review the synchronous result. Successful managed validation reports
   `schema_version`, `archive_id`, `base_revision`, `candidate_revision`,
   `required_selectors` and `valid: true`. The candidate revision is another
   opaque identity, not downloadable TOML. Validation checks the reconstructed
   configuration and preserved authority; it contacts no Hub, creates no
   operation receipt and estimates no download size.
3. To assess the exact intended change, save a new nonsecret `Idempotency-Key`
   before sending the same body to `POST /api/v1/plans`, with the same JSON and
   Basic request headers. Retain the returned original operation ID and links.
   HTTP 202 acknowledges durable admission, not a completed or successful plan.
4. Observe that original operation and its result. A managed assessment binds
   `base_revision`, `candidate_revision` and `required_selectors` to the operation;
   check `complete` and the sizing result as well as the terminal outcome.
   A result response with HTTP 200 alone does not establish successful execution.

The server derives required sizing scope from enabled repositories that are
newly added, newly enabled or revision-retargeted. Nonempty scope requires
independent Hub permission and complete sizing for that scope. A caller cannot
select a smaller subset. Planning reads Hub metadata; it does not download
payloads, synchronize repositories or install configuration.

Tags, settings, removals and changes confined to disabled entries can leave the
required scope empty. The plan then contacts no Hub and returns an explicit
complete assessment with empty `required_selectors` and `sizing: null`. Successful
validation alone is not that assessment. A sizing result is an estimate, not a
reservation of space or authorization to apply.

The existing installed `{}` and literal `{"candidate": "..."}` validation and
planning forms remain separate and keep their existing responses and authority
rules. Do not mix them with `managed`. See the
[managed API form](../api.md#managed-configuration-form) for the wire contract.

## Handle stale bases and interrupted previews

Any change to installed bytes invalidates the old `base_revision`, including a
tag-only edit or a change to comments, whitespace or table order. On a stale-base
conflict, read the installed configuration again, compare its editable values
with your intended changes, and build a new edit request from the new revision.
Do not replace the token on an old draft without reviewing that comparison.
Queue waiting also rechecks the base, permission and protected authority before
Hub work.

Managed reconstruction preserves protected **values**, but canonicalizes the
whole TOML document into a fixed table and repository-array layout with a final
newline. Comments, spacing and original formatting are discarded in the private
candidate, including for an otherwise unchanged assessment. The candidate stays
server-side, is limited to 1 MiB of UTF-8, and is never installed by these calls.
The editable projection is therefore unsuitable as a byte-for-byte backup.

If the preview acknowledgement or connection is lost, preserve its original key
and any known operation ID. Recover with
`GET /api/v1/operations/lookup` using that key in `Idempotency-Key`, or use the
original operation's status/result links. Lookup uses the same administrator
identity. Never submit a replacement preview to discover whether the first ran;
a missing result or expired receipt does not prove nonexecution. See
[reconnect after lost acknowledgement](../api.md#reconnect-after-lost-acknowledgement).

## Apply and protected changes

There is no configuration Apply endpoint in the current implementation. A valid
candidate, complete preview or enabled permission does not install it. Retain
the original assessment for observation; it is evidence, not transferable
authorization for a later write.

Changing archive root/UUID or Hub/credential authority requires a privileged
operator's configuration and deployment procedure. Full literal candidates can
be syntax-valid while incompatible with installed authority; they cannot enter
credential-bearing planning until the operator installs compatible authority.
Preserve the original configuration and credential sources, validate the intended
document with the selected release, and follow the normal reviewed provisioning
and restart procedure. Root/UUID changes require an API restart; server listeners
and authentication are also restart-only. Do not bypass this with an editable
placeholder, alternate path, relaxed permission or automatic replay. See
[candidate authority](../configuration.md#12-candidate-authority-validation-and-planning)
and [deployment profiles](../deployment-centos-stream-10.md).
