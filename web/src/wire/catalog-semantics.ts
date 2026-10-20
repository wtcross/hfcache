/** Audited catalog model rules; derived metadata never becomes archive authority. */
import { WireError } from "./json";
import { isRecord } from "./runtime";

type Atom = string | number;
type Row = Record<string, unknown>;

function requireEvidence(condition: boolean): void {
    if (!condition) throw new WireError("semantic");
}

function fullMatch(pattern: RegExp, value: string): boolean {
    return pattern.exec(value)?.[0] === value;
}

function row(value: unknown): Row {
    if (!isRecord(value)) throw new WireError("semantic");
    return value;
}

function field(value: unknown, key: string): unknown {
    const descriptor = Object.getOwnPropertyDescriptor(row(value), key);
    if (
        descriptor === undefined ||
        descriptor.get !== undefined ||
        descriptor.set !== undefined
    )
        throw new WireError("semantic");
    const result: unknown = descriptor.value;
    return result;
}

function isList(value: unknown): value is readonly unknown[] {
    return Array.isArray(value);
}

function list(value: unknown): readonly unknown[] {
    if (!isList(value)) throw new WireError("semantic");
    return value;
}

function text(value: unknown): string {
    if (typeof value !== "string") throw new WireError("semantic");
    return value;
}

function integer(value: unknown): number {
    if (typeof value !== "number" || !Number.isSafeInteger(value))
        throw new WireError("semantic");
    return value;
}

function count(value: unknown, key: string): bigint {
    return BigInt(integer(field(value, key)));
}

/** Python compares Unicode code points, including non-BMP path components. */
export function compareCatalogText(left: string, right: string): number {
    const a = left[Symbol.iterator]();
    const b = right[Symbol.iterator]();
    for (;;) {
        const first = a.next();
        const second = b.next();
        if (first.done === true) return second.done === true ? 0 : -1;
        if (second.done === true) return 1;
        const x = first.value.codePointAt(0);
        const y = second.value.codePointAt(0);
        if (x === undefined || y === undefined) throw new WireError("semantic");
        if (x !== y) return x < y ? -1 : 1;
    }
}

function compareTuple(left: readonly Atom[], right: readonly Atom[]): number {
    requireEvidence(left.length === right.length);
    for (let index = 0; index < left.length; index++) {
        const a = left[index];
        const b = right[index];
        if (typeof a === "string" && typeof b === "string") {
            const compared = compareCatalogText(a, b);
            if (compared !== 0) return compared;
        } else if (typeof a === "number" && typeof b === "number") {
            if (a !== b) return a < b ? -1 : 1;
        } else throw new WireError("semantic");
    }
    return 0;
}

function ordered(keys: readonly (readonly Atom[])[]): void {
    let previous: readonly Atom[] | undefined;
    for (const key of keys) {
        if (previous !== undefined)
            requireEvidence(compareTuple(previous, key) < 0);
        previous = key;
    }
}

function orderedText(value: unknown): readonly string[] {
    const values = list(value).map(text);
    ordered(values.map((item) => [item]));
    return values;
}

function distinct(keys: readonly (readonly Atom[])[]): void {
    const seen = new Set<string>();
    for (const key of keys) {
        const encoded = JSON.stringify(key);
        requireEvidence(!seen.has(encoded));
        seen.add(encoded);
    }
}

function canonicalTags(value: unknown): void {
    const values = orderedText(value);
    requireEvidence(values.length <= 64);
    for (const tag of values)
        requireEvidence(fullMatch(/^[a-z0-9][a-z0-9._:/-]{0,63}$/u, tag));
}

function identifier(value: unknown): void {
    requireEvidence(
        fullMatch(/^[A-Za-z0-9][A-Za-z0-9._/-]{0,63}$/u, text(value)),
    );
}

function sourceKeys(value: unknown): readonly (readonly Atom[])[] {
    return list(value).map((source) => [
        text(field(source, "path")),
        text(field(source, "field")),
        text(field(source, "evidence")),
    ]);
}

function coverage(value: unknown): void {
    requireEvidence(
        count(value, "tags_known") + count(value, "tags_unknown") ===
            count(value, "repositories"),
    );
    const publications = [
        "usable",
        "partial",
        "unsupported",
        "failed",
        "missing",
    ]
        .map((key) => count(value, key))
        .reduce((sum, item) => sum + item, 0n);
    requireEvidence(publications === count(value, "publications"));
}

function entry(value: unknown): void {
    const formats = orderedText(field(value, "dataset_formats"));
    requireEvidence(
        formats.every(
            (item) =>
                item ===
                item.replace(/[A-Z]/gu, (character) => character.toLowerCase()),
        ),
    );
    const configured = field(value, "configured");
    const origin = field(value, "tag_origin");
    const representative = field(value, "representative_variant");
    const matching = count(value, "matching_variant_count");
    requireEvidence(configured === (field(value, "enabled") !== null));
    requireEvidence((origin === "configured") === configured);
    if (origin === "unknown")
        requireEvidence(
            list(field(value, "tags")).length === 0 &&
                field(value, "tag_observed_at") === null &&
                field(value, "curation_fingerprint") === null,
        );
    if (field(value, "repository_type") === "dataset")
        requireEvidence(matching === 0n && representative === null);
    else requireEvidence(formats.length === 0);
    if (representative !== null) requireEvidence(matching !== 0n);
    if (field(value, "archived") === false)
        requireEvidence(matching === 0n && representative === null);
}

function variant(value: unknown): void {
    const members = list(field(value, "members"));
    ordered(members.map((member) => [text(field(member, "path"))]));
    orderedText(field(value, "source_paths"));
    orderedText(field(value, "diagnostics"));
    const total = field(value, "total_bytes");
    if (total !== null)
        requireEvidence(
            BigInt(integer(total)) ===
                members.reduce<bigint>(
                    (sum, member) => sum + count(member, "size_bytes"),
                    0n,
                ),
        );
    if (field(value, "completeness") === "complete")
        requireEvidence(total !== null);
}

function search(value: unknown): void {
    const entries = list(field(value, "entries"));
    ordered(
        entries.map((item) => [
            text(field(item, "repository_type")),
            text(field(item, "repository_id")),
        ]),
    );
    const total = count(value, "total_matches");
    requireEvidence(
        BigInt(entries.length) <= total &&
            total <= count(field(value, "coverage"), "repositories"),
    );
}

function facets(value: unknown): void {
    const entries = list(field(value, "entries"));
    const values = orderedText(entries.map((item) => field(item, "value")));
    const facet = field(value, "facet");
    requireEvidence(BigInt(entries.length) <= count(value, "total_matches"));
    for (const item of entries)
        requireEvidence(
            count(item, "repository_count") <=
                count(field(value, "coverage"), "repositories"),
        );
    for (const item of values) {
        if (facet === "tag") canonicalTags([item]);
        else {
            identifier(item);
            const canonical =
                facet === "quantization"
                    ? item.toUpperCase()
                    : item.toLowerCase();
            requireEvidence(item === canonical);
        }
    }
}

function publicationRefresh(value: unknown): void {
    const observed = [
        "observation_status",
        "observed_at",
        "manifest_digest",
    ].map((key) => field(value, key));
    const error = field(value, "error_code");
    if (field(value, "write_status") === "written")
        requireEvidence(
            observed.every((item) => item !== null) && error === null,
        );
    else
        requireEvidence(
            observed.every((item) => item === null) && error !== null,
        );
}

function repositoryRefresh(value: unknown): void {
    const warnings = orderedText(field(value, "warnings"));
    const errors = orderedText(field(value, "errors"));
    const publications = list(field(value, "publications"));
    const status = field(value, "technical_status");
    const skipped =
        status === "not_requested" || status === "skipped_unpublished";
    if (skipped) requireEvidence(publications.length === 0);
    ordered(
        publications.map((item) => [
            integer(field(item, "publication_generation")),
            text(field(item, "commit_sha")),
        ]),
    );
    if (!skipped) {
        requireEvidence(publications.length > 0);
        const allComplete = publications.every(
            (item) => field(item, "observation_status") === "complete",
        );
        const anyWritten = publications.some(
            (item) => field(item, "write_status") === "written",
        );
        requireEvidence(
            status ===
                (allComplete
                    ? "complete"
                    : anyWritten
                      ? "incomplete"
                      : "failed"),
        );
    }
    for (const publication of publications) {
        const code = field(publication, "error_code");
        if (code !== null) requireEvidence(errors.includes(text(code)));
    }
    if (field(value, "tag_status") === "failed")
        requireEvidence(errors.length > 0);
    if (errors.length > 0 || status === "incomplete" || status === "failed")
        requireEvidence(warnings.includes("HFWRN011"));
}

function refresh(value: unknown): void {
    const rows = list(field(value, "repositories"));
    ordered(
        rows.map((item) => [
            text(field(item, "repository_type")),
            text(field(item, "repository_id")),
        ]),
    );
    const tags = field(value, "tags");
    const technical = field(value, "technical");
    requireEvidence(tags === true || technical === true);
    let snapshots = 0n;
    let observations = 0n;
    let failed = 0n;
    let incomplete = 0n;
    let skipped = 0n;
    let problems = false;
    for (const item of rows) {
        const tagStatus = field(item, "tag_status");
        const technicalStatus = field(item, "technical_status");
        if (tagStatus === "captured") snapshots++;
        if (tagStatus === "failed") failed++;
        if (technicalStatus === "skipped_unpublished") skipped++;
        if (
            list(field(item, "warnings")).length > 0 ||
            list(field(item, "errors")).length > 0
        )
            problems = true;
        requireEvidence((tags === false) === (tagStatus === "not_requested"));
        requireEvidence(
            (technical === false) === (technicalStatus === "not_requested"),
        );
        for (const publication of list(field(item, "publications"))) {
            if (field(publication, "write_status") === "written")
                observations++;
            if (field(publication, "write_status") === "failed") failed++;
            if (field(publication, "observation_status") !== "complete")
                incomplete++;
        }
    }
    const counts = field(value, "counts");
    for (const [key, expected] of [
        ["repositories", BigInt(rows.length)],
        ["snapshots_written", snapshots],
        ["observations_written", observations],
        ["records_failed", failed],
        ["technical_incomplete", incomplete],
        ["technical_skipped", skipped],
    ] satisfies readonly (readonly [string, bigint])[])
        requireEvidence(count(counts, key) === expected);
    const state = !problems
        ? "complete"
        : snapshots + observations > 0n
          ? "partial"
          : "failed";
    requireEvidence(field(value, "state") === state);
}

export const catalogSemanticIds: readonly string[] = Object.freeze([
    "hfcache.catalog_models._identifier",
    "hfcache.catalog_models.ModelVariant.coherent",
    "hfcache.catalog_models.SourceObservation.ordered",
    "hfcache.catalog_query_models._canonical_tags",
    "hfcache.catalog_query_models.CatalogPayload._version",
    "hfcache.catalog_query_models.CatalogCoverage._coherent",
    "hfcache.catalog_query_models.CatalogEntry._coherent",
    "hfcache.catalog_query_models.CatalogSearchPayload._coherent",
    "hfcache.catalog_query_models.CatalogFacetValue._safe_value",
    "hfcache.catalog_query_models.CatalogFacetPayload._coherent",
    "hfcache.catalog_query_models.CatalogDetailPayload._coherent",
    "hfcache.catalog_query_models.ObservationSummary._ordered",
    "hfcache.catalog_query_models.CatalogVariantsPayload._coherent",
    "hfcache.catalog_refresh_models.PublicationRefresh._coherent",
    "hfcache.catalog_refresh_models.RepositoryRefresh._coherent",
    "hfcache.catalog_refresh_models.CatalogRefreshResult._strict_version",
    "hfcache.catalog_refresh_models.CatalogRefreshResult._coherent",
]);

/** Called only at the audited phase, around generated structural reconstruction. */
export function applyCatalogSemantic(id: string, value: unknown): unknown {
    switch (id) {
        case "hfcache.catalog_models._identifier":
            identifier(value);
            break;
        case "hfcache.catalog_models.ModelVariant.coherent":
            variant(value);
            break;
        case "hfcache.catalog_models.SourceObservation.ordered":
            orderedText(field(value, "values"));
            break;
        case "hfcache.catalog_query_models._canonical_tags":
            canonicalTags(value);
            break;
        case "hfcache.catalog_query_models.CatalogPayload._version":
        case "hfcache.catalog_refresh_models.CatalogRefreshResult._strict_version":
            requireEvidence(integer(value) === 1);
            break;
        case "hfcache.catalog_query_models.CatalogCoverage._coherent":
            coverage(value);
            break;
        case "hfcache.catalog_query_models.CatalogEntry._coherent":
            entry(value);
            break;
        case "hfcache.catalog_query_models.CatalogSearchPayload._coherent":
            search(value);
            break;
        case "hfcache.catalog_query_models.CatalogFacetValue._safe_value":
            requireEvidence(
                fullMatch(/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,63}$/u, text(value)),
            );
            break;
        case "hfcache.catalog_query_models.CatalogFacetPayload._coherent":
            facets(value);
            break;
        case "hfcache.catalog_query_models.CatalogDetailPayload._coherent":
            distinct(
                list(field(value, "observations")).map((item) => [
                    text(field(item, "commit_sha")),
                    text(field(item, "publication_id")),
                ]),
            );
            break;
        case "hfcache.catalog_query_models.ObservationSummary._ordered":
            ordered(sourceKeys(field(value, "sources")));
            orderedText(field(value, "dataset_formats"));
            orderedText(field(value, "diagnostics"));
            break;
        case "hfcache.catalog_query_models.CatalogVariantsPayload._coherent": {
            const entries = list(field(value, "entries"));
            distinct(
                entries.map((item) => [
                    text(field(item, "commit_sha")),
                    text(field(item, "publication_id")),
                    text(field(field(item, "variant"), "variant_id")),
                ]),
            );
            requireEvidence(
                BigInt(entries.length) <= count(value, "total_matches"),
            );
            break;
        }
        case "hfcache.catalog_refresh_models.PublicationRefresh._coherent":
            publicationRefresh(value);
            break;
        case "hfcache.catalog_refresh_models.RepositoryRefresh._coherent":
            repositoryRefresh(value);
            break;
        case "hfcache.catalog_refresh_models.CatalogRefreshResult._coherent":
            refresh(value);
            break;
        default:
            throw new WireError("semantic");
    }
    return value;
}

export interface CatalogReadContext {
    readonly command: string;
    readonly repositoryType?: "model" | "dataset";
    readonly repositoryId?: string;
    readonly commitSha?: string;
    readonly publicationId?: string;
    readonly facet?: string;
}

/** Extra read/request rules in client_catalog.py, after wrapper/payload decoding. */
export function validateCatalogRead(
    response: unknown,
    context: CatalogReadContext,
): void {
    const envelope = field(response, "envelope");
    const cursor = field(response, "next_cursor");
    requireEvidence(
        field(response, "archive_id") !== null &&
            field(response, "config_fingerprint") !== null,
    );
    requireEvidence(field(envelope, "command") === context.command);
    if (cursor !== null) {
        const token = text(cursor);
        requireEvidence(
            token.length > 0 &&
                token.length <= 256 &&
                /^[\x00-\x7f]*$/u.test(token),
        );
        // The browser never has the server's private exact-secret registry.
        // Known secret shapes are refused; opaque cursors remain undisplayed.
        requireEvidence(
            !/(?:hf_[A-Za-z0-9]{8,}|bearer\s+\S+|https?:\/\/\S*[?&](?:x-amz-|x-goog-|sig=|signature=|token=))/iu.test(
                token,
            ),
        );
    }
    if (integer(field(envelope, "exit_code")) !== 0) {
        requireEvidence(cursor === null);
        return;
    }
    const payload = field(envelope, "data");
    const scoped = field(payload, "coverage");
    const missing = [
        "tags_unknown",
        "partial",
        "unsupported",
        "failed",
        "missing",
    ]
        .map((key) => count(scoped, key))
        .reduce((sum, item) => sum + item, 0n);
    const incomplete = field(scoped, "incomplete");
    if (missing > 0n) requireEvidence(incomplete === true);
    const warned = list(field(envelope, "warnings")).some(
        (item) => field(item, "code") === "HFWRN011",
    );
    requireEvidence(incomplete === warned);
    requireEvidence(
        (context.commitSha === undefined) ===
            (context.publicationId === undefined),
    );
    if (context.command === "catalog.detail") {
        requireEvidence(cursor === null);
        const selected = field(payload, "entry");
        if (context.repositoryType !== undefined)
            requireEvidence(
                field(selected, "repository_type") === context.repositoryType,
            );
        if (context.repositoryId !== undefined)
            requireEvidence(
                field(selected, "repository_id") === context.repositoryId,
            );
    }
    if (context.command === "catalog.facets") {
        if (context.facet !== undefined)
            requireEvidence(field(payload, "facet") === context.facet);
        for (const item of list(field(payload, "entries")))
            requireEvidence(count(item, "repository_count") > 0n);
    }
    if (
        context.command === "catalog.search" &&
        context.repositoryType !== undefined
    )
        for (const item of list(field(payload, "entries")))
            requireEvidence(
                field(item, "repository_type") === context.repositoryType,
            );
    if (context.commitSha !== undefined) {
        const observations =
            context.command === "catalog.detail"
                ? field(payload, "observations")
                : field(payload, "entries");
        for (const item of list(observations))
            requireEvidence(
                field(item, "commit_sha") === context.commitSha &&
                    field(item, "publication_id") === context.publicationId,
            );
    }
}

/** A stored failed refresh may retain precise progress; empty success is invalid. */
export function validateCatalogRefresh(response: unknown): void {
    const envelope = field(response, "envelope");
    requireEvidence(
        field(envelope, "command") === "catalog refresh" &&
            field(response, "next_cursor") === null,
    );
    const payload = row(field(envelope, "data"));
    if (Object.keys(payload).length === 0)
        requireEvidence(integer(field(envelope, "exit_code")) !== 0);
    else
        requireEvidence(
            field(payload, "archive_id") === field(response, "archive_id"),
        );
}
