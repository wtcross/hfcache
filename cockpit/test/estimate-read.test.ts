/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseEstimate } from '../src/lib/estimate-read.ts';
import type { Envelope } from '../src/lib/envelope.ts';

const payload = () => ({
    mode: 'estimate',
    repositories: 2,
    revisions: 3,
    unique_objects: 4,
    unique_bytes: 1000,
    unreadable_objects: 0,
    measured_throughput_bytes_per_second: 100,
    estimated_duration_seconds: 10,
    storage_maintenance: 'undetectable'
});
function envelope(data: Record<string, unknown>, exit = 0): Envelope {
    return {
        schema_version: 1,
        command: 'verify --estimate',
        run_id: 'a'.repeat(32),
        started_at: '2026-10-20T12:00:00Z',
        completed_at: '2026-10-20T12:00:01Z',
        data,
        exit_code: exit,
        outcome: exit ? 'failed' : 'success',
        warnings: [],
        errors: exit ? [{ code: 'HFAPI003', message: 'Original refusal', repository: null }] : []
    };
}
test('V47 metadata estimate retains actual counters and unknown confidence', () => {
    assert.deepEqual(parseEstimate(envelope(payload())).payload, payload());
    const unknown = { ...payload(), measured_throughput_bytes_per_second: null, estimated_duration_seconds: null };
    assert.deepEqual(parseEstimate(envelope(unknown)).payload, unknown);
    assert.equal(parseEstimate(null).payload, null);
    assert.equal(parseEstimate(envelope({})).payload, null);
    for (const data of [null, [], 'SYNTHETIC_SECRET']) {
        const result = parseEstimate({ ...envelope({}), data });
        assert.equal(result.payload, null);
        assert.ok(result.error);
    }
});
test('V47 original negative results need no success payload and valid partial estimates stay informational', () => {
    const failed = envelope({}, 20);
    assert.deepEqual(parseEstimate(failed), { payload: null, error: null, partial: true });
    const partial = parseEstimate(envelope(payload(), 20));
    assert.equal(partial.partial, true);
    assert.deepEqual(partial.payload, payload());
    assert.equal(failed.errors[0].code, 'HFAPI003');
});
for (const [field, invalid] of [
    ['repositories', -1], ['revisions', '3'], ['unique_objects', false],
    ['unique_bytes', Number.MAX_SAFE_INTEGER + 1], ['unreadable_objects', 0.5],
    ['measured_throughput_bytes_per_second', -1], ['estimated_duration_seconds', Infinity],
    ['storage_maintenance', 'guaranteed-safe'], ['mode', 'full'],
] as const) {
    test('V47 malformed estimate field ' + field + ' cannot become a zero or successful placeholder', () => {
        const result = parseEstimate(envelope({ ...payload(), [field]: invalid }));
        assert.equal(result.payload, null);
        assert.equal(result.error?.stage, 'api-read');
        assert.equal(result.error?.hostMutationUncertain, false);
    });
}
test('V47 missing fields, invented fields and inconsistent measurement cannot grant confidence', () => {
    const missing: Record<string, unknown> = payload(); delete missing.unique_objects;
    for (const data of [missing, { ...payload(), unknown: 'SYNTHETIC_SECRET' },
        { ...payload(), measured_throughput_bytes_per_second: null },
        { ...payload(), measured_throughput_bytes_per_second: 0 },
        { ...payload(), estimated_duration_seconds: 20 }]) {
        const result = parseEstimate(envelope(data));
        assert.equal(result.payload, null);
        assert.ok(!result.error?.message.includes('SYNTHETIC_SECRET'));
    }
});
