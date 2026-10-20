/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Validate complete CLI inventory without changing its paginated REST join.
 */
import type { Envelope } from './envelope.ts';
import { parseSelector } from './command.ts';
import type { RepositoryType } from './command.ts';
import { readPayloadError } from './read-results.ts';
import type { ParsedRead } from './read-results.ts';

export interface InventoryRevision {
    readonly commit_sha: string;
    readonly file_count: number;
    readonly publication_generation: number;
    readonly publication_id: string;
    readonly published_at: string;
    readonly total_bytes: number;
    readonly verification_state: 'verified' | 'unverified' | 'failed';
}
export interface InventoryRepository {
    readonly repository_id: string;
    readonly repository_type: RepositoryType;
    readonly enabled: boolean | null;
    readonly managed: boolean;
    readonly current_commit_sha: string | null;
    readonly current_publication_id: string | null;
    readonly retained_revisions: number;
    readonly revisions: readonly InventoryRevision[];
}
export interface InventoryData { readonly repositories: readonly InventoryRepository[] }

const REPOSITORY_FIELDS = ['repository_id', 'repository_type', 'enabled', 'managed',
    'current_commit_sha', 'current_publication_id', 'retained_revisions', 'revisions'];
const REVISION_FIELDS = ['commit_sha', 'file_count', 'publication_generation', 'publication_id',
    'published_at', 'total_bytes', 'verification_state'];
const record = (value: unknown): value is Record<string, unknown> =>
    typeof value === 'object' && value !== null && !Array.isArray(value);
const exact = (value: Record<string, unknown>, fields: readonly string[]): boolean =>
    Object.keys(value).length === fields.length && fields.every(field => Object.prototype.hasOwnProperty.call(value, field));
const count = (value: unknown): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
const sha = (value: unknown): value is string => typeof value === 'string' && /^[a-f0-9]{40}$/.test(value);
const publication = (value: unknown): value is string => typeof value === 'string' && /^[a-f0-9]{32}$/.test(value);

function timestamp(value: unknown): value is string {
    if (typeof value !== 'string' || value.length > 64 ||
        !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/.test(value)) return false;
    const parsed = new Date(value);
    return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 19) === value.slice(0, 19);
}

function revision(value: unknown): value is InventoryRevision {
    return record(value) && exact(value, REVISION_FIELDS) && sha(value.commit_sha) &&
        publication(value.publication_id) && count(value.file_count) && count(value.total_bytes) &&
        count(value.publication_generation) && value.publication_generation > 0 &&
        timestamp(value.published_at) && ['verified', 'unverified', 'failed'].includes(value.verification_state as string);
}

function repository(value: unknown): value is InventoryRepository {
    if (!record(value) || !exact(value, REPOSITORY_FIELDS) ||
        !['model', 'dataset'].includes(value.repository_type as string) || typeof value.repository_id !== 'string' ||
        typeof value.managed !== 'boolean' || !count(value.retained_revisions) ||
        (value.managed ? typeof value.enabled !== 'boolean' : value.enabled !== null) ||
        !Array.isArray(value.revisions) || !value.revisions.every(revision) ||
        value.retained_revisions !== value.revisions.length) return false;
    try {
        if (parseSelector(value.repository_type + ':' + value.repository_id).sha !== undefined) return false;
    } catch { return false }
    const revisions = value.revisions;
    if (new Set(revisions.map(item => item.commit_sha)).size !== revisions.length ||
        new Set(revisions.map(item => item.publication_id)).size !== revisions.length ||
        new Set(revisions.map(item => item.publication_generation)).size !== revisions.length ||
        revisions.some((item, index) => index !== 0 && item.publication_generation <= revisions[index - 1].publication_generation)) return false;
    if (value.current_commit_sha === null || value.current_publication_id === null)
        return value.current_commit_sha === null && value.current_publication_id === null;
    return sha(value.current_commit_sha) && publication(value.current_publication_id) &&
        revisions.some(item => item.commit_sha === value.current_commit_sha && item.publication_id === value.current_publication_id);
}

export function parseInventory(envelope: Envelope): ParsedRead<InventoryData> {
    const partial = envelope.exit_code !== 0;
    const data = envelope.data;
    if (partial && envelope.command === 'list' && record(data) && Object.keys(data).length === 0)
        return { payload: null, error: null, partial: false };
    if (envelope.command !== 'list' || !record(data) || !exact(data, ['repositories']) ||
        !Array.isArray(data.repositories) || !data.repositories.every(repository) ||
        new Set(data.repositories.map(item => item.repository_type + ':' + item.repository_id)).size !== data.repositories.length)
        return { payload: null, error: readPayloadError(), partial: false };
    const repositories = data.repositories.map(item => Object.freeze({
        ...item, revisions: Object.freeze(item.revisions.map(entry => Object.freeze({ ...entry })))
    }));
    return { payload: Object.freeze({ repositories: Object.freeze(repositories) }), error: null, partial };
}
