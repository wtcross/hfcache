# Render archived Markdown through a bounded closed React pipeline

- Decision identity:155.
- Status:Accepted.
- Date:2026-10-26.
- Record introduced: `1ca6287fbe0b873acf01678da6d18a2da34690a9`.

## Context and decision

Verified archived cards need useful formatting without moving payload, network,
script or application-navigation authority into upstream content. Select exact
browser-asset dependencies `react-markdown`10.1.0, `remark-gfm`4.0.1 and
`rehype-sanitize`6.0.0, with a frozen audited closure and complete license notices.
Node remains build/test tooling; the shared API/UI runtime stays pinned UBI10micro.
The audited frozen set contains373 packages,108 in the browser dependency
closure (including type declarations that are optimized out). All production
closure licenses are MIT except `@ungap/structured-clone`1.4.0 under ISC. Its
installed ISC copyright/permission text is retained verbatim with the MIT and
existing LGPL/Unicode notices. Any other non-MIT production identity still
requires explicit notice review.

Lazy-load CommonMark/GFM rendering. Disable raw HTML/MDX and use a final explicit
sanitizer allowlist plus closed React components. No source properties are spread
onto elements. Admit prose, lists, quotes, headings, inert code, bounded tables
and safe links. Media are labelled inert placeholders; no images/fonts/scripts,
forms, SVG, embedded frames, remote plugins or raw HTML insertion are enabled.
GFM tasks and footnotes degrade to inert content or pinned upstream navigation.

Before synchronous parsing, bound input to64KiB UTF-8,2048 lines,4096 characters
per line, nesting8,4096 structural delimiters,128 headings/fences,16KiB per code
block and256 table cells. A finite post-parse walk additionally caps4096 AST
nodes, depth24,128 headings and256 cells. Measure adversarial admission/parse
fixtures; parser failure or exhaustion stays local and leaves original operation
recovery/navigation available. Refuse rendering explicitly; never silently raise
capture/API limits or truncate verified source into successful full content.

Link policy rejects control/entity/encoded unsafe schemes, network paths,
userinfo, backslashes and ambiguous targets. HTTP(S) navigation is explicit and
uses noopener/noreferrer/no-referrer. Relative and fragment references resolve
only under the selected model/dataset's immutable upstream commit, never the
management origin or application selection fragment. Root-relative references
remain repository-root-relative; dot segments cannot escape that root. Generate
heading IDs from validated publication identity and ordinal, never source IDs.

The source view shows only exact verified sanitized presentation bytes, escaped
as React text under the existing1MiB card boundary. It identifies derivative
content and source/presentation digests separately. Capture already removes YAML
front matter; rendering does not strip a legitimate leading horizontal rule or
mutate source under its presentation digest. Missing/unsafe/unsupported/failed
capture and renderer refusal remain distinct; no view triggers recapture.

## Rationale and alternatives

A reviewed CommonMark/GFM parser and final sanitizer avoid a handwritten Markdown
interpreter while retaining an explicit application policy. Default library
schemas or URL transforms alone do not establish this boundary. Raw HTML,
rehype-raw/MDX, syntax execution, automatic media and proxy fetching would widen
untrusted content authority. Post-parse limits or promise timeouts alone cannot
bound a synchronous parser, so conservative pre-admission precedes it. A worker
is unnecessary unless actual measurements show these finite bounds insufficient.

## Consequences and relationships

The frontend dependency/license inventory and notices expand; backend packaging,
wire/card schemas, capture grammar, original operation handles and authentication
remain unchanged. Large or pathological valid cards may offer sanitized source
instead of formatted content. Upstream claims and README source checks never
establish payload integrity. Unit/component, real API and three-engine installed
DOM/network/CSP acceptance remain required before completion.

Amends [142](decision-142.md), [143](decision-143.md), [FW-03/04](fw-01.md),
[security](../security.md#browser-administration-design) and
[README cards](../web-ui/readme-cards.md). Primary versioned documentation:
[React Markdown](https://github.com/remarkjs/react-markdown/blob/10.1.0/readme.md),
[GFM](https://github.com/remarkjs/remark-gfm/blob/4.0.1/readme.md) and
[sanitizer](https://github.com/rehypejs/rehype-sanitize/blob/6.0.0/readme.md).
Implementation, dependency and adversarial acceptance require their own
executable evidence; this decision alone claims no passing acceptance.

## Recovery navigation compatibility clarification (2026-10-26)

The owned WebKit27.2 profile reports an inline-style attempt when a native
`select` is constructed, including a neutral empty element under the same CSP.
Text inputs, textareas, options and ordinary elements do not reproduce that
behavior. Recovery handle and legacy-class choices therefore use labelled
constant-enum radio groups. This changes presentation only; current state,
original handles, namespace separation, readiness and operation observation
retain their existing contracts. CSP is not relaxed to accommodate controls.
