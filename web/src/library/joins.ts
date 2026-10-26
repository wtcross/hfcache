/** INV-018/021: catalog evidence is joined by authority and exact identity, never position. */
import { canonicalHex, repositorySegments } from "../api/identity";
import type { ApiScope } from "../api/identity";
import type { ReadResponse } from "../api/types";
import { sameApiScope } from "../state/authority";
import type {
    CatalogEntry,
    CatalogSearchPayload,
    RepositoriesPayload,
    RepositoryPayload,
    RepositoryStatusPayload,
    RevisionPayload,
    RevisionsPayload,
    StatusPayload,
} from "../wire/generated";

export interface ScopedLibraryRead<T> {
    readonly scope: ApiScope;
    readonly response: ReadResponse<T>;
}
export interface LibraryEnrichments {
    readonly inventory?: ScopedLibraryRead<RepositoriesPayload>;
    readonly status?: ScopedLibraryRead<StatusPayload>;
    readonly revisions?: ScopedLibraryRead<RevisionsPayload>;
}
export interface LibraryRow {
    readonly key: string;
    readonly entry: CatalogEntry;
    readonly inventory: RepositoryPayload | null;
    readonly status: RepositoryStatusPayload | null;
    /** Exact inventory current pair; null never means zero bytes or verified absence. */
    readonly currentRevision: RevisionPayload | null;
    /** Exact representative pair and generation; it can be a different retained revision. */
    readonly representativeRevision: RevisionPayload | null;
    readonly enrichment: "complete" | "partial" | "changed" | "unavailable";
}
export class LibraryJoinError extends Error {
    constructor(
        readonly reason: "authority" | "duplicate" | "bounds" | "identity",
    ) {
        super("Library metadata could not be joined safely.");
        this.name = "LibraryJoinError";
    }
}
const MAX_JOIN_ROWS = 10_000;
type RepositoryIdentity = Pick<
    CatalogEntry,
    "repository_type" | "repository_id"
>;

export function libraryRepositoryKey(row: RepositoryIdentity): string {
    try {
        repositorySegments(row.repository_type, row.repository_id);
    } catch {
        throw new LibraryJoinError("identity");
    }
    return row.repository_type + ":" + row.repository_id;
}
function publicationKey(
    row: RepositoryIdentity & {
        readonly commit_sha: string;
        readonly publication_id: string;
    },
): string {
    if (
        !canonicalHex(row.commit_sha, 40) ||
        !canonicalHex(row.publication_id, 32)
    )
        throw new LibraryJoinError("identity");
    return (
        libraryRepositoryKey(row) +
        ":" +
        row.commit_sha +
        ":" +
        row.publication_id
    );
}
function inventoryKey(row: RepositoryPayload): string {
    if (
        (row.current_commit_sha === null) !==
        (row.current_publication_id === null)
    )
        throw new LibraryJoinError("identity");
    if (row.current_commit_sha !== null && row.current_publication_id !== null)
        publicationKey({
            ...row,
            commit_sha: row.current_commit_sha,
            publication_id: row.current_publication_id,
        });
    return libraryRepositoryKey(row);
}
function statusKey(row: RepositoryStatusPayload): string {
    if (
        (row.current_commit_sha === null) !==
        (row.current_publication_generation === null)
    )
        throw new LibraryJoinError("identity");
    return libraryRepositoryKey(row);
}
function index<T>(
    rows: readonly T[],
    key: (row: T) => string,
): ReadonlyMap<string, T> {
    if (rows.length > MAX_JOIN_ROWS) throw new LibraryJoinError("bounds");
    const output = new Map<string, T>();
    for (const row of rows) {
        const id = key(row);
        if (output.has(id)) throw new LibraryJoinError("duplicate");
        output.set(id, row);
    }
    return output;
}
function authority<T>(read: ScopedLibraryRead<T>): boolean {
    return (
        read.scope.archiveId !== null &&
        read.response.config_fingerprint !== null &&
        read.response.archive_id === read.scope.archiveId &&
        (read.scope.configFingerprint === null ||
            read.response.config_fingerprint === read.scope.configFingerprint)
    );
}
function compatible<T>(
    catalog: ScopedLibraryRead<CatalogSearchPayload>,
    read: ScopedLibraryRead<T>,
): boolean {
    return (
        sameApiScope(catalog.scope, read.scope) &&
        authority(read) &&
        read.response.archive_id === catalog.response.archive_id &&
        read.response.config_fingerprint === catalog.response.config_fingerprint
    );
}

/** Only the already decoded, bounded pages supplied by the caller are considered. */
export function joinLibraryRows(
    catalog: ScopedLibraryRead<CatalogSearchPayload>,
    supplements: LibraryEnrichments = {},
): readonly LibraryRow[] {
    if (!authority(catalog)) throw new LibraryJoinError("authority");
    const entries = catalog.response.envelope.data.entries;
    index(entries, libraryRepositoryKey);
    const inventory =
        supplements.inventory !== undefined &&
        compatible(catalog, supplements.inventory)
            ? index(
                  supplements.inventory.response.envelope.data.repositories,
                  inventoryKey,
              )
            : null;
    const statuses =
        supplements.status !== undefined &&
        compatible(catalog, supplements.status)
            ? index(
                  supplements.status.response.envelope.data.repositories,
                  statusKey,
              )
            : null;
    const revisions =
        supplements.revisions !== undefined &&
        compatible(catalog, supplements.revisions)
            ? index(
                  supplements.revisions.response.envelope.data.revisions,
                  publicationKey,
              )
            : null;
    const authorityChanged =
        (supplements.inventory !== undefined && inventory === null) ||
        (supplements.status !== undefined && statuses === null) ||
        (supplements.revisions !== undefined && revisions === null);
    const unavailable =
        supplements.inventory === undefined &&
        supplements.status === undefined &&
        supplements.revisions === undefined;
    return Object.freeze(
        entries.map((entry) => {
            const key = libraryRepositoryKey(entry);
            let item = inventory?.get(key) ?? null;
            let status = statuses?.get(key) ?? null;
            let changed = authorityChanged;
            if (
                item !== null &&
                (item.managed !== entry.configured ||
                    item.enabled !== entry.enabled ||
                    item.retained_revisions > 0 !== entry.archived)
            ) {
                changed = true;
                item = null;
            }
            if (
                status !== null &&
                (status.managed !== entry.configured ||
                    status.enabled !== entry.enabled ||
                    status.retained_revisions > 0 !== entry.archived)
            ) {
                changed = true;
                status = null;
            }
            let currentRevision: RevisionPayload | null = null;
            if (
                item?.current_commit_sha !== null &&
                item?.current_commit_sha !== undefined &&
                item.current_publication_id !== null
            ) {
                currentRevision =
                    revisions?.get(
                        publicationKey({
                            ...entry,
                            commit_sha: item.current_commit_sha,
                            publication_id: item.current_publication_id,
                        }),
                    ) ?? null;
            }
            if (
                item !== null &&
                status !== null &&
                (status.current_commit_sha !== item.current_commit_sha ||
                    (currentRevision !== null &&
                        status.current_publication_generation !==
                            currentRevision.publication_generation))
            ) {
                changed = true;
                // Separate successful reads are not an atomic current-publication snapshot.
                status = null;
                currentRevision = null;
            }
            let representativeRevision: RevisionPayload | null = null;
            const representative = entry.representative_variant;
            if (representative !== null) {
                representativeRevision =
                    revisions?.get(
                        publicationKey({ ...entry, ...representative }),
                    ) ?? null;
                if (
                    representativeRevision !== null &&
                    representativeRevision.publication_generation !==
                        representative.publication_generation
                ) {
                    changed = true;
                    representativeRevision = null;
                }
            }
            const complete =
                item !== null &&
                status !== null &&
                revisions !== null &&
                (item.current_commit_sha === null ||
                    currentRevision !== null) &&
                (representative === null || representativeRevision !== null);
            return Object.freeze({
                key,
                entry,
                inventory: item,
                status,
                currentRevision,
                representativeRevision,
                enrichment: changed
                    ? "changed"
                    : unavailable
                      ? "unavailable"
                      : complete
                        ? "complete"
                        : "partial",
            });
        }),
    );
}
