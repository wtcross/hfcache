/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Independent, closed presentation schemas for the existing REST-backed reads.
 * A parsed partial payload never changes the original Envelope classification.
 */
import type { Envelope } from './envelope.ts';
import { BoundaryError } from './failure.ts';
import { parseSelector } from './command.ts';

export interface ParsedRead<T> { payload: T | null; error: BoundaryError | null; partial: boolean }
export function readPayloadError(): BoundaryError {
    return new BoundaryError({ problem: 'protocol-error' }, { stage: 'api-read', reason: 'invalid-envelope', hostMutationUncertain: false });
}

const record = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value);
const exact = (value: Record<string, unknown>, fields: readonly string[]): boolean =>
    Object.keys(value).length === fields.length && fields.every(field => Object.prototype.hasOwnProperty.call(value, field));
// eslint-disable-next-line no-control-regex
const PRINTABLE = /^[^\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]+$/;
const text = (value: unknown, limit = 4096): value is string => typeof value === 'string' && value.length > 0 &&
    value.length <= limit && PRINTABLE.test(value);
const count = (value: unknown): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);
const sha = (value: unknown): value is string => typeof value === 'string' && /^[0-9a-f]{40}$/.test(value);
const timestamp = (value: unknown): value is string => text(value, 64) &&
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/.test(value) && Number.isFinite(Date.parse(value)) &&
    new Date(value).toISOString()
            .slice(0, 19) === value.slice(0, 19);
const uuid = (value: unknown): value is string => typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(value);
// The CLI already joins paginated reads; its terminal byte bound is the limit.
// An invented row limit here would discard legitimate complete inventories.
const array = (value: unknown): value is unknown[] => Array.isArray(value);

export interface StatusVerification {
    degraded: boolean;
    outstanding_failures: number;
    last_full_verification: {
        completed_at: string; started_at: string; duration_seconds: number; outcome: 'clean' | 'failed';
        report: string; throughput_bytes_per_second: number; unique_bytes: number; unique_objects: number;
    } | null;
}
export interface StatusFinding { area: string; path: string; age_hours: number; stale: boolean; transaction_id: string }
interface ArchiveBase { archive_id: string; root: string; verification: StatusVerification }
export type StatusArchive = ArchiveBase & ({ reachable: false } | {
    reachable: true; available_bytes: number; available_gib: number; reserve_bytes: number; headroom_bytes: number;
    total_bytes: number; quarantined_bytes: number; unfinished_transactions: number; deferred_cleanup: number;
    findings: readonly StatusFinding[]; unknown_entries: readonly string[];
});
export interface StatusRepository {
    repository_id: string; repository_type: 'model' | 'dataset'; managed: boolean; enabled: boolean | null;
    requested_revision: string | null; current_commit_sha: string | null; current_publication_generation: number | null;
    retained_revisions: number; retained_generations: readonly number[]; last_run_status: string | null;
    upstream_state: 'unknown'; verification_state: 'verified' | 'unverified' | 'failed';
}
export interface StatusData { archive?: StatusArchive; repositories?: readonly StatusRepository[] }

function verification(value: unknown): value is StatusVerification {
    if (!record(value) || !exact(value, ['degraded', 'outstanding_failures', 'last_full_verification']) ||
        typeof value.degraded !== 'boolean' || !count(value.outstanding_failures) || value.degraded !== (value.outstanding_failures > 0)) return false;
    const last = value.last_full_verification;
    return last === null || (record(last) && exact(last, ['completed_at', 'started_at', 'duration_seconds', 'outcome', 'report',
        'throughput_bytes_per_second', 'unique_bytes', 'unique_objects']) && timestamp(last.completed_at) && timestamp(last.started_at) &&
        Date.parse(last.completed_at) >= Date.parse(last.started_at) && finite(last.duration_seconds) && last.duration_seconds >= 0 &&
        ['clean', 'failed'].includes(last.outcome as string) && text(last.report) && /^runs\//.test(last.report) &&
        finite(last.throughput_bytes_per_second) && last.throughput_bytes_per_second >= 0 && count(last.unique_bytes) && count(last.unique_objects));
}
function finding(value: unknown): value is StatusFinding {
    return record(value) && exact(value, ['area', 'path', 'age_hours', 'stale', 'transaction_id']) &&
        ['.store/staging', '.store/trash', '.store/quarantine', '.store/repair'].includes(value.area as string) &&
        text(value.path) && value.path === value.area + '/' + value.transaction_id &&
        typeof value.transaction_id === 'string' && /^[0-9a-f]{32}$/.test(value.transaction_id) &&
        finite(value.age_hours) && typeof value.stale === 'boolean';
}
function archive(value: unknown): value is StatusArchive {
    const base = ['archive_id', 'root', 'reachable', 'verification'];
    if (!record(value) || !uuid(value.archive_id) || !text(value.root) || !value.root.startsWith('/') || !verification(value.verification)) return false;
    if (value.reachable === false) return exact(value, base);
    return value.reachable === true && exact(value, [...base, 'available_bytes', 'available_gib', 'reserve_bytes', 'headroom_bytes',
        'total_bytes', 'quarantined_bytes', 'unfinished_transactions', 'deferred_cleanup', 'findings', 'unknown_entries']) &&
        ['available_bytes', 'reserve_bytes', 'total_bytes', 'quarantined_bytes', 'unfinished_transactions', 'deferred_cleanup'].every(field => count(value[field])) &&
        finite(value.available_gib) && value.available_gib >= 0 && finite(value.headroom_bytes) &&
        value.headroom_bytes === (value.available_bytes as number) - (value.reserve_bytes as number) &&
        array(value.findings) && value.findings.every(finding) && array(value.unknown_entries) && value.unknown_entries.every(item => text(item));
}
function repository(value: unknown): value is StatusRepository {
    if (!record(value) || !exact(value, ['repository_id', 'repository_type', 'managed', 'enabled', 'requested_revision',
        'current_commit_sha', 'current_publication_generation', 'retained_revisions', 'retained_generations', 'last_run_status', 'upstream_state', 'verification_state']) ||
        !['model', 'dataset'].includes(value.repository_type as string) || !text(value.repository_id, 256)) return false;
    try { if (parseSelector(value.repository_type + ':' + value.repository_id).sha !== undefined) return false; } catch { return false }
    return typeof value.managed === 'boolean' &&
        (value.managed ? typeof value.enabled === 'boolean' && text(value.requested_revision, 1024) : value.enabled === null && value.requested_revision === null) &&
        (value.current_commit_sha === null ? value.current_publication_generation === null : sha(value.current_commit_sha) && count(value.current_publication_generation) && value.current_publication_generation > 0) &&
        count(value.retained_revisions) && array(value.retained_generations) && value.retained_generations.every(item => count(item) && item > 0) &&
        value.retained_revisions === value.retained_generations.length && new Set(value.retained_generations).size === value.retained_generations.length &&
        (value.last_run_status === null || ['skipped', 'ref_moved_to_retained_revision', 'published', 'completed_with_warnings', 'failed', 'disabled'].includes(value.last_run_status as string)) &&
        value.upstream_state === 'unknown' && ['verified', 'unverified', 'failed'].includes(value.verification_state as string);
}
function parsed<T>(envelope: Envelope, command: string, validate: (data: Record<string, unknown>, success: boolean) => boolean): ParsedRead<T> {
    const partial = envelope.exit_code !== 0;
    if (envelope.command !== command || !record(envelope.data) || !validate(envelope.data, !partial))
        return { payload: null, error: readPayloadError(), partial };
    return { payload: Object.keys(envelope.data).length === 0 ? null : envelope.data as T, error: null, partial };
}
export function parseStatus(envelope: Envelope): ParsedRead<StatusData> {
    return parsed(envelope, 'status', (data, success) => {
        if (Object.keys(data).some(key => !['archive', 'repositories'].includes(key)) ||
            (success && !exact(data, ['archive', 'repositories']))) return false;
        if (data.archive !== undefined && !archive(data.archive)) return false;
        if (data.repositories !== undefined && (!array(data.repositories) || !data.repositories.every(repository) ||
            new Set(data.repositories.map(row => row.repository_type + ':' + row.repository_id)).size !== data.repositories.length)) return false;
        return true;
    });
}

export interface VersionData { application?: string; python?: string; huggingface_hub?: string; transfer_backend?: string }
export function parseVersion(envelope: Envelope): ParsedRead<VersionData> {
    const fields = ['application', 'python', 'huggingface_hub', 'transfer_backend'];
    return parsed(envelope, 'version', (data, success) => (success ? exact(data, fields) : Object.keys(data).every(key => fields.includes(key))) &&
        Object.entries(data).every(([field, value]) => text(value, 128) && (field === 'transfer_backend'
            ? /^(http|xet [A-Za-z0-9][A-Za-z0-9.+_-]{0,100})$/.test(value)
            : /^[A-Za-z0-9][A-Za-z0-9.+_ -]{0,127}$/.test(value))));
}
export const DOCTOR_CHECK_NAMES = ['configuration', 'archive_root', 'mount_point', 'filesystem_type', 'mount_writable', 'sentinel',
    'directory_writability', 'staging_filesystem', 'hardlink_capability', 'atomic_directory_rename', 'reference_replacement', 'free_space',
    'credential', 'hub_endpoint', 'hub_dns', 'hub_tls', 'hub_identity'] as const;
export interface DoctorCheck { name: typeof DOCTOR_CHECK_NAMES[number]; outcome: 'pass' | 'fail' | 'skipped'; detail: string }
export interface DoctorData { checks: readonly DoctorCheck[] }
export function parseDoctor(envelope: Envelope): ParsedRead<DoctorData> {
    return parsed(envelope, 'doctor', (data, success) => {
        if (!success && Object.keys(data).length === 0) return true;
        if (!exact(data, ['checks']) || !Array.isArray(data.checks) || data.checks.length < 1 || data.checks.length > DOCTOR_CHECK_NAMES.length) return false;
        // The current service emits all seventeen entries, including explicit
        // skips for checks it could not run. A successful subset is incomplete.
        if (success && data.checks.length !== DOCTOR_CHECK_NAMES.length) return false;
        let previous = -1;
        for (const check of data.checks) {
            if (!record(check) || !exact(check, ['name', 'outcome', 'detail']) || !['pass', 'fail', 'skipped'].includes(check.outcome as string) || !text(check.detail)) return false;
            const index = DOCTOR_CHECK_NAMES.indexOf(check.name as DoctorCheck['name']);
            if (index <= previous || (success && check.outcome === 'fail')) return false;
            previous = index;
        }
        return true;
    });
}
