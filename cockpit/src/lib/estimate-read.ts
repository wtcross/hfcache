/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Presentation of the existing metadata-only verification estimate.
 */
import type { Envelope } from './envelope.ts';
import { readPayloadError } from './read-results.ts';
import type { ParsedRead } from './read-results.ts';

export interface EstimateData {
    mode: 'estimate';
    repositories: number;
    revisions: number;
    unique_objects: number;
    unique_bytes: number;
    unreadable_objects: number;
    measured_throughput_bytes_per_second: number | null;
    estimated_duration_seconds: number | null;
    storage_maintenance: 'undetectable';
}
const FIELDS = ['mode', 'repositories', 'revisions', 'unique_objects', 'unique_bytes', 'unreadable_objects',
    'measured_throughput_bytes_per_second', 'estimated_duration_seconds', 'storage_maintenance'];
const count = (value: unknown): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
const rate = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value) && value >= 0;

export function parseEstimate(envelope: Envelope | null): ParsedRead<Readonly<EstimateData>> {
    if (envelope === null) return { payload: null, error: null, partial: false };
    const partial = envelope.exit_code !== 0;
    if (typeof envelope.data !== 'object' || envelope.data === null || Array.isArray(envelope.data))
        return { payload: null, error: readPayloadError(), partial };
    const data = envelope.data as Record<string, unknown>;
    if (partial && Object.keys(data).length === 0) return { payload: null, error: null, partial };
    if (envelope.command !== 'verify --estimate' || Object.keys(data).length !== FIELDS.length ||
        !FIELDS.every(field => Object.prototype.hasOwnProperty.call(data, field)) || data.mode !== 'estimate' ||
        !['repositories', 'revisions', 'unique_objects', 'unique_bytes', 'unreadable_objects'].every(field => count(data[field])) ||
        (data.measured_throughput_bytes_per_second !== null && !rate(data.measured_throughput_bytes_per_second)) ||
        (data.estimated_duration_seconds !== null && !rate(data.estimated_duration_seconds)) || data.storage_maintenance !== 'undetectable')
        return { payload: null, error: readPayloadError(), partial };
    const throughput = data.measured_throughput_bytes_per_second as number | null;
    const duration = data.estimated_duration_seconds as number | null;
    const expected = throughput === null || throughput === 0 ? null : (data.unique_bytes as number) / throughput;
    if (expected === null
        ? duration !== null
        : duration === null || !Number.isFinite(expected) ||
        Math.abs(expected - duration) > Number.EPSILON * Math.max(1, expected) * 4)
        return { payload: null, error: readPayloadError(), partial };
    return { payload: Object.freeze({ ...data }) as unknown as Readonly<EstimateData>, error: null, partial };
}
