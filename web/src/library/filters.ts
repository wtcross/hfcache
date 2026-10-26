/** WEB012: finite Library intent; fragments never become a server shell query. */
import type { CatalogQuery } from "../api/client";
import { routeContracts } from "../wire/generated";
import { normalizeManagedTags } from "../wire/config-semantics";
import { codePointLength, parseWireJson } from "../wire/json";
import { wireRequestObject } from "../wire/runtime";

export const MAX_LIBRARY_FRAGMENT_BYTES = 8192;
export const MAX_LIBRARY_PAGE_SIZE = 100;
export type LibraryFilters = CatalogQuery & {
    readonly scope: "all" | "configured" | "archived";
    readonly revision_scope: "current" | "retained";
    readonly tag_source: "current_or_last_observed" | "current_only";
    readonly limit: number;
};
export type LibraryFilterPatch = {
    readonly [K in keyof CatalogQuery]?: CatalogQuery[K] | undefined;
};
export interface LibraryFilterChange {
    readonly filters: LibraryFilters;
    readonly announcement: string | null;
}
export class LibraryFilterError extends Error {
    constructor(readonly reason: "invalid" | "bounds") {
        super("Library filters are invalid or exceed the supported bounds.");
        this.name = "LibraryFilterError";
    }
}
const KEYS = [
    "type",
    "q",
    "tag_all",
    "tag_any",
    "tag_source",
    "scope",
    "revision_scope",
    "format",
    "quantization",
    "quantization_method",
    "bits",
    "max_variant_bytes",
    "limit",
    "cursor",
] as const;
const MODEL_ONLY = [
    "quantization",
    "quantization_method",
    "bits",
    "max_variant_bytes",
] as const;
const NUMERIC = new Set<string>(["bits", "max_variant_bytes", "limit"]);
const REPEATED = new Set<string>(["tag_all", "tag_any"]);
const bytes = (value: string) => new TextEncoder().encode(value).length;
function invalid(): never {
    throw new LibraryFilterError("invalid");
}
function bounded(value: string): void {
    if (bytes(value) > MAX_LIBRARY_FRAGMENT_BYTES)
        throw new LibraryFilterError("bounds");
}
function safeText(value: unknown): string {
    if (typeof value !== "string") invalid();
    codePointLength(value); // Reject unpaired UTF-16 before URLSearchParams can replace it.
    if (/[\u0000-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069]/u.test(value))
        invalid();
    return value;
}
function queryParameters(
    query: CatalogQuery,
    bookmark: boolean,
): URLSearchParams {
    const parameters = new URLSearchParams();
    for (const name of KEYS) {
        if (bookmark && name === "cursor") continue;
        const value = query[name];
        if (value === undefined) continue;
        for (const member of Array.isArray(value) ? value : [value]) {
            parameters.append(name, String(member));
        }
    }
    return parameters;
}

/** Use the existing generated query grammar, with a smaller displayed-page bound. */
export function normalizeLibraryFilters(input: unknown): LibraryFilters {
    try {
        const source = wireRequestObject(input, [], KEYS);
        const values: Record<string, unknown> = {
            scope: "all",
            revision_scope: "current",
            tag_source: "current_or_last_observed",
            limit: 25,
        };
        for (const name of KEYS) {
            if (!Object.hasOwn(source, name)) continue;
            const value = source[name];
            if (REPEATED.has(name)) {
                const tags = normalizeManagedTags(value);
                if (tags.length > 0) values[name] = Object.freeze(tags);
            } else if (NUMERIC.has(name)) {
                if (typeof value !== "number" || !Number.isSafeInteger(value))
                    invalid();
                values[name] = value;
            } else {
                const text = safeText(value);
                if (
                    (name === "q" ||
                        name === "cursor" ||
                        name === "format" ||
                        name === "quantization" ||
                        name === "quantization_method") &&
                    text === ""
                )
                    continue;
                if (
                    name === "format" ||
                    name === "quantization" ||
                    name === "quantization_method"
                ) {
                    if (
                        /^[A-Za-z0-9][A-Za-z0-9._/-]{0,63}$/u.exec(
                            text,
                        )?.[0] !== text
                    )
                        invalid();
                    values[name] =
                        name === "quantization"
                            ? text.toUpperCase()
                            : text.toLowerCase();
                } else {
                    if (
                        name === "cursor" &&
                        !/^[\u0020-\u007e]{1,256}$/u.test(text)
                    )
                        invalid();
                    values[name] = text;
                }
            }
        }
        if (
            typeof values.limit !== "number" ||
            values.limit > MAX_LIBRARY_PAGE_SIZE
        )
            throw new LibraryFilterError("bounds");
        const modelOnly = MODEL_ONLY.some((name) =>
            Object.hasOwn(values, name),
        );
        if (modelOnly) {
            if (values.type === "dataset") invalid();
            values.type = "model";
        }
        // Integer source lexemes and Unicode are checked by the same wire decoder as ApiClient.
        const query = routeContracts.catalog_search_default.decodeQuery(
            parseWireJson(JSON.stringify(values)),
        );
        bounded(queryParameters(query, false).toString());
        return Object.freeze({
            ...query,
            scope: query.scope ?? "all",
            revision_scope: query.revision_scope ?? "current",
            tag_source: query.tag_source ?? "current_or_last_observed",
            limit: query.limit ?? 25,
        });
    } catch (error) {
        if (error instanceof LibraryFilterError) throw error;
        throw new LibraryFilterError("invalid");
    }
}

export const DEFAULT_LIBRARY_FILTERS = normalizeLibraryFilters({});

/** Only filter intent is bookmarked. Opaque page cursors belong to one read chain. */
export function parseLibraryFragment(fragment: string): LibraryFilters {
    try {
        safeText(fragment);
        bounded(fragment);
        const input = fragment.startsWith("#") ? fragment.slice(1) : fragment;
        const values: Record<string, unknown> = {};
        const repeated = new Map<string, string[]>();
        if (input !== "")
            for (const field of input.split("&")) {
                const separator = field.indexOf("=");
                if (separator < 1) invalid();
                const name = decodeURIComponent(
                    field.slice(0, separator).replaceAll("+", " "),
                );
                const value = decodeURIComponent(
                    field.slice(separator + 1).replaceAll("+", " "),
                );
                if (!KEYS.some((key) => key === name) || name === "cursor")
                    invalid();
                if (REPEATED.has(name)) {
                    const tags = repeated.get(name) ?? [];
                    tags.push(value);
                    repeated.set(name, tags);
                    values[name] = tags;
                } else {
                    if (Object.hasOwn(values, name)) invalid();
                    if (NUMERIC.has(name)) {
                        if (/^(?:0|[1-9][0-9]*)$/u.exec(value)?.[0] !== value)
                            invalid();
                        const number = Number(value);
                        if (!Number.isSafeInteger(number)) invalid();
                        values[name] = number;
                    } else values[name] = value;
                }
            }
        return normalizeLibraryFilters(values);
    } catch (error) {
        if (error instanceof LibraryFilterError) throw error;
        throw new LibraryFilterError("invalid");
    }
}

export function libraryFragment(filters: CatalogQuery): string {
    const encoded = queryParameters(
        normalizeLibraryFilters(filters),
        true,
    ).toString();
    bounded("#" + encoded);
    return "#" + encoded;
}

export function updateLibraryFilters(
    current: CatalogQuery,
    patch: LibraryFilterPatch,
): LibraryFilterChange {
    const before = normalizeLibraryFilters(current);
    let delta: Record<string, unknown>;
    try {
        delta = wireRequestObject(patch, [], KEYS);
    } catch {
        return invalid();
    }
    let candidate: Record<string, unknown> = {};
    for (const name of KEYS) {
        const value = Object.hasOwn(delta, name) ? delta[name] : before[name];
        if (value !== undefined) candidate[name] = value;
    }
    let announcement: string | null = null;
    if (delta.type === "dataset") {
        if (MODEL_ONLY.some((name) => Object.hasOwn(candidate, name)))
            announcement =
                "Model-only variant filters were cleared for datasets.";
        candidate = Object.fromEntries(
            Object.entries(candidate).filter(
                ([name]) => !MODEL_ONLY.some((field) => field === name),
            ),
        );
    }
    let filters = normalizeLibraryFilters(candidate);
    if (libraryFragment(before) !== libraryFragment(filters)) {
        filters = normalizeLibraryFilters({ ...filters, cursor: "" });
    }
    return Object.freeze({ filters, announcement });
}

export function setLibraryType(
    current: CatalogQuery,
    type: "model" | "dataset" | undefined,
): LibraryFilterChange {
    return updateLibraryFilters(current, { type });
}
