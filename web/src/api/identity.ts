import { WireError } from "../wire/json";
import { pythonIsPrintable } from "../wire/unicode";

export interface ApiScope {
    readonly origin: string;
    readonly publicPrefix: string;
    readonly authorityEpoch: string;
    readonly subject: string;
    readonly credentialClass: "rest-reader" | "rest-writer";
    readonly instanceId: string | null;
    readonly archiveId: string | null;
    readonly configFingerprint: string | null;
}

function fullMatch(value: string, pattern: RegExp): boolean {
    return pattern.exec(value)?.[0] === value;
}

export function canonicalHex(value: string, length: number): boolean {
    return value.length === length && fullMatch(value, /[0-9a-f]+/u);
}

export function canonicalArchiveId(value: string): boolean {
    return (
        value.length === 36 &&
        fullMatch(
            value,
            /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/u,
        )
    );
}

export function createApiScope(scope: ApiScope): ApiScope {
    const origin = new URL(scope.origin);
    if (
        origin.origin !== scope.origin ||
        !["https:", "http:"].includes(origin.protocol) ||
        origin.username !== "" ||
        origin.password !== ""
    )
        throw new WireError("schema");
    if (
        scope.publicPrefix !== "" &&
        (!scope.publicPrefix.startsWith("/") ||
            scope.publicPrefix.startsWith("//") ||
            scope.publicPrefix.endsWith("/") ||
            !pythonIsPrintable(scope.publicPrefix) ||
            /[ ?#\\%]/u.test(scope.publicPrefix) ||
            scope.publicPrefix
                .slice(scope.publicPrefix.startsWith("//") ? 2 : 1)
                .split("/")
                .some((part) => part === "" || part === "." || part === ".."))
    )
        throw new WireError("schema");
    for (const value of [scope.authorityEpoch, scope.subject])
        if (
            value.length === 0 ||
            value.length > 256 ||
            /[\u0000-\u0020\u007f]/u.test(value)
        )
            throw new WireError("schema");
    if (
        !["rest-reader", "rest-writer"].includes(scope.credentialClass) ||
        (scope.instanceId !== null && !canonicalHex(scope.instanceId, 32)) ||
        (scope.archiveId !== null && !canonicalArchiveId(scope.archiveId)) ||
        (scope.configFingerprint !== null &&
            !canonicalHex(scope.configFingerprint, 64))
    )
        throw new WireError("schema");
    return Object.freeze({
        origin: scope.origin,
        publicPrefix: scope.publicPrefix,
        authorityEpoch: scope.authorityEpoch,
        subject: scope.subject,
        credentialClass: scope.credentialClass,
        instanceId: scope.instanceId,
        archiveId: scope.archiveId,
        configFingerprint: scope.configFingerprint,
    });
}

export interface ExactPublication {
    readonly repositoryType: "model" | "dataset";
    readonly repositoryId: string;
    readonly commitSha: string;
    readonly publicationId: string;
}

export function repositorySegments(
    type: string,
    identifier: string,
): readonly [string, string] {
    const segments = identifier.split("/");
    const namespace = segments[0],
        name = segments[1];
    if (
        !["model", "dataset"].includes(type) ||
        segments.length !== 2 ||
        namespace === undefined ||
        name === undefined ||
        [namespace, name].some(
            (part) =>
                part.length > 96 ||
                !fullMatch(part, /[A-Za-z0-9][A-Za-z0-9._-]*/u),
        )
    )
        throw new WireError("schema");
    return [namespace, name];
}

export function publicationIdentity(publication: ExactPublication): string {
    repositorySegments(publication.repositoryType, publication.repositoryId);
    if (
        !canonicalHex(publication.commitSha, 40) ||
        !canonicalHex(publication.publicationId, 32)
    )
        throw new WireError("schema");
    return JSON.stringify([
        publication.repositoryType,
        publication.repositoryId,
        publication.commitSha,
        publication.publicationId,
    ]);
}

/** Includes authority changes and exact publication identity; stores no credential. */
export function queryIdentity(
    scope: ApiScope,
    route: string,
    query: readonly (readonly [string, string])[] = [],
    publication?: ExactPublication,
): string {
    return JSON.stringify([
        scope.origin,
        scope.publicPrefix,
        scope.authorityEpoch,
        scope.subject,
        scope.credentialClass,
        scope.instanceId,
        scope.archiveId,
        scope.configFingerprint,
        route,
        query,
        publication === undefined ? null : publicationIdentity(publication),
    ]);
}
