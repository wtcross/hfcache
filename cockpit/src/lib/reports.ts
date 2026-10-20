/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Strict REST run pages and historical report payloads (docs/schemas.md §6–7).
 * Historical filename parsing remains a pure compatibility helper.
 */

import type { Envelope } from './envelope.ts';
import { parseSelector } from './command.ts';
import type { RunReadMetadata } from './read-metadata.ts';
import { isArchiveId, ReadMetadataError } from './read-metadata.ts';

const REPORT_NAME = /^(\d{8})T(\d{6})Z-([0-9a-f]{32})\.json$/;
export const REPORT_PAGE_LIMIT = 50;

export interface RunPage { runs: readonly string[]; nextCursor: string | null }
export interface ReportRepository {
    repository_id: string;
    repository_type: 'model' | 'dataset';
    status: string;
    resolved_commit_sha: string | null;
    downloaded_bytes: number;
    reused_bytes: number;
    hashed_bytes: number;
    publication_generation: number | null;
}
export interface RunReport {
    schema_version: 1;
    archive_id: string;
    run_id: string;
    command: string;
    started_at: string;
    completed_at: string;
    config_fingerprint: string;
    invocation_mode: 'systemd' | 'interactive';
    outcome: 'success' | 'success_with_warnings' | 'failed';
    exit_code: number;
    warnings: readonly string[];
    errors: readonly string[];
    repositories?: readonly ReportRepository[];
    totals?: Readonly<Record<string, number>>;
    findings?: readonly Readonly<Record<string, unknown>>[];
}

function record(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function exact(value: Record<string, unknown>, fields: readonly string[]): boolean {
    return Object.keys(value).length === fields.length && fields.every(field => Object.prototype.hasOwnProperty.call(value, field));
}
const count = (value: unknown): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
const timestamp = (value: unknown): value is string => typeof value === 'string' && value.length <= 64 &&
    /^\d{4}-\d{2}-\d{2}T/.test(value) && Number.isFinite(Date.parse(value));
const codes = (value: unknown): value is string[] => Array.isArray(value) && value.every(code =>
    typeof code === 'string' && /^HF[A-Z0-9]+\d{3}$/.test(code));
const REPORT_FIELDS = ['schema_version', 'application_version', 'archive_id', 'command', 'completed_at',
    'config_fingerprint', 'errors', 'exit_code', 'hostname', 'huggingface_hub_version', 'invocation_mode',
    'outcome', 'python_version', 'run_id', 'started_at', 'warnings'];
const REPOSITORY_FIELDS = ['downloaded_bytes', 'duration_seconds', 'errors', 'file_count', 'hashed_bytes',
    'publication_generation', 'publication_id', 'pruned', 'repository_id', 'repository_type', 'requested_revision',
    'resolved_commit_sha', 'reused_bytes', 'status', 'warnings'];
const TOTAL_FIELDS = ['downloaded_bytes', 'hashed_bytes', 'published_bytes', 'pruned_logical_bytes', 'reused_bytes', 'xet_cache_peak_bytes'];
const sha = (value: unknown): value is string => typeof value === 'string' && /^[0-9a-f]{40}$/.test(value);

function namedRepository(value: Record<string, unknown>): boolean {
    if (typeof value.repository_id !== 'string' || !['model', 'dataset'].includes(value.repository_type as string)) return false;
    try { parseSelector(value.repository_type + ':' + value.repository_id); return true } catch { return false }
}

function finding(value: unknown): boolean {
    if (!record(value) || !exact(value, ['commit_sha', 'expected', 'kind', 'observed', 'path', 'publication_id', 'repository_id', 'repository_type']) ||
        !namedRepository(value) || (value.commit_sha !== null && !sha(value.commit_sha)) ||
        !['missing', 'extra', 'size_mismatch', 'digest_mismatch', 'not_regular', 'unreadable', 'ref_invalid', 'manifest_invalid'].includes(value.kind as string) ||
        !['expected', 'observed', 'path'].every(field => value[field] === null || typeof value[field] === 'string') ||
        (value.publication_id !== null && (typeof value.publication_id !== 'string' || !isRunId(value.publication_id)))) return false;
    return value.commit_sha !== null || (value.kind === 'ref_invalid' && value.publication_id === null && value.path === null);
}

export function parseRunPage(envelope: Envelope, metadata: Readonly<RunReadMetadata>, expected?: Readonly<RunReadMetadata>): RunPage {
    if (envelope.exit_code !== 0 || envelope.command !== 'runs' || metadata.command !== 'runs' ||
        metadata.run_id !== envelope.run_id || (expected !== undefined &&
            (metadata.archive_id !== expected.archive_id || metadata.config_fingerprint !== expected.config_fingerprint)) ||
        !record(envelope.data) || !exact(envelope.data, ['runs']) || !Array.isArray(envelope.data.runs) ||
        envelope.data.runs.length > REPORT_PAGE_LIMIT || !envelope.data.runs.every(id => typeof id === 'string' && isRunId(id)) ||
        new Set(envelope.data.runs).size !== envelope.data.runs.length ||
        (metadata.next_cursor !== null && envelope.data.runs.length === 0))
        throw new ReadMetadataError();
    return Object.freeze({ runs: Object.freeze([...envelope.data.runs]) as readonly string[], nextCursor: metadata.next_cursor });
}

function repository(value: unknown): value is ReportRepository {
    if (!record(value) || !exact(value, REPOSITORY_FIELDS) || !namedRepository(value))
        return false;
    return ['skipped', 'ref_moved_to_retained_revision', 'published', 'completed_with_warnings', 'failed', 'disabled'].includes(value.status as string) &&
        (value.resolved_commit_sha === null || sha(value.resolved_commit_sha)) &&
        ['downloaded_bytes', 'reused_bytes', 'hashed_bytes', 'file_count'].every(field => count(value[field])) &&
        (value.publication_generation === null || (count(value.publication_generation) && value.publication_generation > 0)) &&
        typeof value.duration_seconds === 'number' && Number.isFinite(value.duration_seconds) && value.duration_seconds >= 0 &&
        typeof value.requested_revision === 'string' && codes(value.errors) && codes(value.warnings) &&
        (value.publication_id === null || (typeof value.publication_id === 'string' && isRunId(value.publication_id))) &&
        (value.pruned === null || (record(value.pruned) && exact(value.pruned, ['commit_sha', 'logical_bytes', 'publication_generation']) &&
            sha(value.pruned.commit_sha) && count(value.pruned.logical_bytes) && count(value.pruned.publication_generation) && value.pruned.publication_generation > 0)) &&
        (value.status !== 'published' || value.publication_id !== null) &&
        (value.status !== 'failed' || value.errors.length > 0) &&
        (value.status !== 'completed_with_warnings' || value.warnings.length > 0);
}

export function parseRunReport(envelope: Envelope, metadata: Readonly<RunReadMetadata>, runId: string,
    expectedArchive?: string): Readonly<RunReport> {
    const report = record(envelope.data) ? envelope.data.report : null;
    if (envelope.exit_code !== 0 || envelope.command !== 'runs read' || metadata.command !== 'runs read' ||
        metadata.run_id !== envelope.run_id || envelope.run_id !== runId || metadata.next_cursor !== null ||
        (expectedArchive !== undefined && metadata.archive_id !== expectedArchive) || !record(envelope.data) ||
        !exact(envelope.data, ['report']) || !record(report) || report.schema_version !== 1 ||
        report.run_id !== runId || report.archive_id !== metadata.archive_id || !isArchiveId(report.archive_id) ||
        typeof report.config_fingerprint !== 'string' || !/^[0-9a-f]{64}$/.test(report.config_fingerprint) ||
        typeof report.command !== 'string' || report.command.length === 0 || report.command.length > 128 ||
        !timestamp(report.started_at) || !timestamp(report.completed_at) || Date.parse(report.completed_at) < Date.parse(report.started_at) ||
        !['systemd', 'interactive'].includes(report.invocation_mode as string) ||
        ![0, 10, 20, 30, 40, 50].includes(report.exit_code as number) ||
        !['success', 'success_with_warnings', 'failed'].includes(report.outcome as string) ||
        !codes(report.warnings) || !codes(report.errors) ||
        (report.exit_code === 0) !== (report.outcome !== 'failed') ||
        (report.outcome !== 'failed' && ((report.outcome === 'success_with_warnings') !== (report.warnings.length > 0))) ||
        !['application_version', 'hostname', 'huggingface_hub_version', 'python_version'].every(field => typeof report[field] === 'string'))
        throw new ReadMetadataError();
    if ('repositories' in report && (!Array.isArray(report.repositories) || !report.repositories.every(repository)))
        throw new ReadMetadataError();
    if ('totals' in report && (!record(report.totals) || !exact(report.totals, TOTAL_FIELDS) || !Object.values(report.totals).every(count)))
        throw new ReadMetadataError();
    if ('findings' in report && (!Array.isArray(report.findings) || !report.findings.every(finding)))
        throw new ReadMetadataError();
    if (report.command.startsWith('verify ')) {
        if (!exact(report, [...REPORT_FIELDS, 'findings', 'mode', 'scope', 'throughput_bytes_per_second', 'verification_outcome']) ||
            !Array.isArray(report.findings) || !['new', 'full', 'revision'].includes(report.mode as string) ||
            report.command !== 'verify --' + report.mode || !record(report.scope) || !Object.values(report.scope).every(count) ||
            !exact(report.scope, ['repositories', 'revisions', 'unique_bytes_read', 'unique_objects_read']) ||
            typeof report.throughput_bytes_per_second !== 'number' || !Number.isFinite(report.throughput_bytes_per_second) ||
            report.throughput_bytes_per_second < 0 || !['clean', 'failed'].includes(report.verification_outcome as string) ||
            (report.verification_outcome === 'failed') !== (report.findings.length > 0))
            throw new ReadMetadataError();
    } else if (report.command.startsWith('recover')) {
        if (!exact(report, [...REPORT_FIELDS, 'remediations']) || !Array.isArray(report.remediations) ||
            !report.remediations.every(value => record(value) && exact(value, ['evidence', 'outcome', 'reason', 'remedy', 'transaction_id']) &&
                record(value.evidence) && ['applied', 'blocked', 'pending'].includes(value.outcome as string) &&
                typeof value.reason === 'string' && typeof value.remedy === 'string' && typeof value.transaction_id === 'string'))
            throw new ReadMetadataError();
    } else if (!exact(report, [...REPORT_FIELDS, 'repositories', 'totals']) || !Array.isArray(report.repositories) || !record(report.totals)) {
        throw new ReadMetadataError();
    }
    return report as unknown as Readonly<RunReport>;
}

export interface ReportName {
    file: string;
    startedAt: Date | null;
    runId: string | null;
}

export function isReportName(file: string): boolean {
    return REPORT_NAME.test(file);
}

export function parseReportName(file: string): ReportName {
    const match = REPORT_NAME.exec(file);
    if (match === null)
        return { file, startedAt: null, runId: null };
    const day = match[1];
    const time = match[2];
    const iso = `${day.slice(0, 4)}-${day.slice(4, 6)}-${day.slice(6, 8)}` +
        `T${time.slice(0, 2)}:${time.slice(2, 4)}:${time.slice(4, 6)}Z`;
    const startedAt = new Date(iso);
    return {
        file,
        startedAt: Number.isNaN(startedAt.getTime()) ? null : startedAt,
        runId: match[3],
    };
}

export function isRunId(text: string): boolean {
    return /^[0-9a-f]{32}$/.test(text);
}
