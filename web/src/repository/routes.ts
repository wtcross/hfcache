/** WEB013: presentation-only repository routes and exact-pair bookmarks (INV-018/021). */
import {
    canonicalHex,
    publicationIdentity,
    repositorySegments,
} from "../api/identity";
import type { ExactPublication } from "../api/identity";
import { uriPath } from "../api/url-paths";
import { codePointLength } from "../wire/json";
import { wireObject } from "../wire/runtime";
import { canonicalUiPrefix } from "../wire/ui-semantics";

export interface RepositoryTarget {
    readonly repositoryType: "model" | "dataset";
    readonly repositoryId: string;
}
export interface PublicationPair {
    readonly commitSha: string;
    readonly publicationId: string;
}
export const REPOSITORY_TABS = [
    "overview",
    "details",
    "files",
    "revisions",
    "integrity",
    "activity",
] as const;
export type RepositoryTab = (typeof REPOSITORY_TABS)[number];
export interface RepositoryView {
    readonly pair: PublicationPair | null;
    readonly tab: RepositoryTab;
}
export const MAX_REPOSITORY_FRAGMENT_BYTES = 8192;
const MAX_REPOSITORY_PATH_BYTES = 4096;
export class RepositoryRouteError extends Error {
    constructor(readonly reason: "invalid" | "bounds") {
        super(
            "The repository address is invalid or exceeds the supported bounds.",
        );
        this.name = "RepositoryRouteError";
    }
}
function invalid(): never {
    throw new RepositoryRouteError("invalid");
}
function bounded(value: string, maximum: number): void {
    if (typeof value !== "string") invalid();
    codePointLength(value);
    if (new TextEncoder().encode(value).length > maximum)
        throw new RepositoryRouteError("bounds");
}
function base(value: string): string {
    bounded(value, MAX_REPOSITORY_PATH_BYTES);
    if (!value.endsWith("/ui/")) invalid();
    const prefix = decodeURIComponent(value.slice(0, -4));
    canonicalUiPrefix(prefix);
    if (uriPath(prefix + "/ui/") !== value) invalid();
    return value;
}
function targetValue(input: unknown): RepositoryTarget {
    const target = wireObject(input, ["repositoryType", "repositoryId"]);
    if (
        (target.repositoryType !== "model" &&
            target.repositoryType !== "dataset") ||
        typeof target.repositoryId !== "string"
    )
        invalid();
    repositorySegments(target.repositoryType, target.repositoryId);
    return Object.freeze({
        repositoryType: target.repositoryType,
        repositoryId: target.repositoryId,
    });
}
function pairValue(input: unknown): PublicationPair {
    const pair = wireObject(input, ["commitSha", "publicationId"]);
    if (
        typeof pair.commitSha !== "string" ||
        typeof pair.publicationId !== "string" ||
        !canonicalHex(pair.commitSha, 40) ||
        !canonicalHex(pair.publicationId, 32)
    )
        invalid();
    return Object.freeze({
        commitSha: pair.commitSha,
        publicationId: pair.publicationId,
    });
}
export function isRepositoryTab(value: unknown): value is RepositoryTab {
    return REPOSITORY_TABS.some((tab) => tab === value);
}

/** A noncanonical path is not recognized; decoding cannot turn a slash into an ID. */
export function parseRepositoryRoute(
    pathname: string,
    basePath: string,
): RepositoryTarget | null {
    try {
        bounded(pathname, MAX_REPOSITORY_PATH_BYTES);
        const prefix = base(basePath);
        if (!pathname.startsWith(prefix)) return null;
        const parts = pathname.slice(prefix.length).split("/");
        const [collection, type, namespace, name] = parts;
        if (
            parts.length !== 4 ||
            collection !== "repositories" ||
            (type !== "model" && type !== "dataset") ||
            namespace === undefined ||
            name === undefined
        )
            return null;
        const target = targetValue({
            repositoryType: type,
            repositoryId: namespace + "/" + name,
        });
        return repositoryPath(target, prefix) === pathname ? target : null;
    } catch {
        return null;
    }
}

export function repositoryPath(
    target: RepositoryTarget,
    basePath: string,
): string {
    try {
        const checked = targetValue(target);
        const prefix = base(basePath);
        const path =
            prefix +
            "repositories/" +
            checked.repositoryType +
            "/" +
            checked.repositoryId;
        bounded(path, MAX_REPOSITORY_PATH_BYTES);
        // Validate/encode through the same trusted path grammar used for API navigation.
        if (uriPath(decodeURIComponent(path)) !== path) invalid();
        return path;
    } catch (error) {
        if (error instanceof RepositoryRouteError) throw error;
        throw new RepositoryRouteError("invalid");
    }
}

/** Both identifiers are required together; a SHA alone must never select a repair replacement. */
export function parseRepositoryFragment(fragment: string): RepositoryView {
    try {
        bounded(fragment, MAX_REPOSITORY_FRAGMENT_BYTES);
        const input = fragment.startsWith("#") ? fragment.slice(1) : fragment;
        const fields: Record<string, string> = {};
        if (input !== "")
            for (const entry of input.split("&")) {
                const separator = entry.indexOf("=");
                if (separator < 1) invalid();
                const name = decodeURIComponent(
                    entry.slice(0, separator).replaceAll("+", " "),
                );
                const value = decodeURIComponent(
                    entry.slice(separator + 1).replaceAll("+", " "),
                );
                if (
                    !["commit_sha", "publication_id", "tab"].includes(name) ||
                    Object.hasOwn(fields, name)
                )
                    invalid();
                fields[name] = value;
            }
        if (
            (fields.commit_sha === undefined) !==
            (fields.publication_id === undefined)
        )
            invalid();
        const tab = fields.tab ?? "overview";
        if (!isRepositoryTab(tab)) invalid();
        const pair =
            fields.commit_sha === undefined
                ? null
                : pairValue({
                      commitSha: fields.commit_sha,
                      publicationId: fields.publication_id,
                  });
        return Object.freeze({ pair, tab });
    } catch (error) {
        if (error instanceof RepositoryRouteError) throw error;
        throw new RepositoryRouteError("invalid");
    }
}

export function repositoryFragment(view: RepositoryView): string {
    try {
        const fields = wireObject(view, ["pair", "tab"]);
        if (!isRepositoryTab(fields.tab)) invalid();
        const pair = fields.pair === null ? null : pairValue(fields.pair);
        const query = new URLSearchParams();
        if (pair !== null) {
            query.set("commit_sha", pair.commitSha);
            query.set("publication_id", pair.publicationId);
        }
        query.set("tab", fields.tab);
        return "#" + query.toString();
    } catch (error) {
        if (error instanceof RepositoryRouteError) throw error;
        throw new RepositoryRouteError("invalid");
    }
}

/** Shared constructor keeps current resolution and an explicitly selected pair distinct. */
export function exactPublication(
    target: RepositoryTarget,
    pair: PublicationPair,
): ExactPublication {
    try {
        const value = Object.freeze({
            ...targetValue(target),
            ...pairValue(pair),
        });
        publicationIdentity(value);
        return value;
    } catch (error) {
        if (error instanceof RepositoryRouteError) throw error;
        throw new RepositoryRouteError("invalid");
    }
}
