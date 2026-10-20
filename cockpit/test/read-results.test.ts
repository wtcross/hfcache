/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';
import type { Envelope } from '../src/lib/envelope.ts';
import { DOCTOR_CHECK_NAMES, parseDoctor, parseStatus, parseVersion } from '../src/lib/read-results.ts';

const verification = { degraded: false, outstanding_failures: 0, last_full_verification: null };
const archive = {
    archive_id: '11111111-1111-4111-8111-111111111111',
    root: '/fixture/archive',
    reachable: true,
    verification,
    available_bytes: 100,
    available_gib: 0,
    reserve_bytes: 10,
    headroom_bytes: 90,
    total_bytes: 200,
    quarantined_bytes: 0,
    unfinished_transactions: 0,
    deferred_cleanup: 0,
    findings: [],
    unknown_entries: []
};
const repository = {
    repository_id: 'org/model',
    repository_type: 'model',
    managed: true,
    enabled: true,
    requested_revision: 'main',
    current_commit_sha: null,
    current_publication_generation: null,
    retained_revisions: 0,
    retained_generations: [],
    last_run_status: null,
    upstream_state: 'unknown',
    verification_state: 'unverified'
};
const version = { application: '0.1.3', python: '3.13.9', huggingface_hub: '1.0.0', transfer_backend: 'http' };
function envelope(command: string, data: Record<string, unknown>, exit = 0): Envelope {
    return {
        schema_version: 1,
        command,
        data,
        exit_code: exit,
        outcome: exit ? 'failed' : 'success',
        errors: [],
        warnings: [],
        run_id: 'a'.repeat(32),
        started_at: '2026-10-20T12:00:00Z',
        completed_at: '2026-10-20T12:00:01Z'
    };
}
test('status accepts actual reachable and unreachable service shapes without fabricated counters', () => {
    const valid = parseStatus(envelope('status', { archive, repositories: [repository] }));
    assert.equal(valid.error, null); assert.equal(valid.partial, false); assert.equal(valid.payload?.repositories?.length, 1);
    const unavailable = { archive_id: archive.archive_id, root: archive.root, reachable: false, verification };
    const parsed = parseStatus(envelope('status', { archive: unavailable, repositories: [] }));
    assert.equal(parsed.error, null); assert.equal(parsed.payload?.archive?.reachable, false);
    assert.equal(Object.prototype.hasOwnProperty.call(parsed.payload?.archive ?? {}, 'available_bytes'), false);
});
test('status accepts nullable unmanaged values and every actual repository report status', () => {
    for (const last_run_status of [null, 'skipped', 'ref_moved_to_retained_revision', 'published', 'completed_with_warnings', 'failed', 'disabled']) {
        const result = parseStatus(envelope('status', { archive, repositories: [{ ...repository, last_run_status, managed: false, enabled: null, requested_revision: null }] }));
        assert.equal(result.error, null);
    }
});
test('status preserves a complete paginated CLI aggregate above ten thousand rows', () => {
    const repositories = Array.from({ length: 10001 }, (_, index) => ({ ...repository, repository_id: 'org/model-' + index }));
    const data = { archive, repositories };
    assert.ok(Buffer.byteLength(JSON.stringify(data), 'utf8') < 16 * 1024 * 1024);
    const result = parseStatus(envelope('status', data));
    assert.equal(result.error, null);
    assert.equal(result.payload?.repositories?.length, 10001);
    assert.equal(result.payload?.repositories?.[10000]?.repository_id, 'org/model-10000');
});
test('status accepts complete verification history and rejects impossible timestamps', () => {
    const last = {
        started_at: '2026-10-20T12:00:00.000000Z',
        completed_at: '2026-10-20T12:00:01.000000Z',
        duration_seconds: 1,
        outcome: 'clean',
        report: 'runs/20261020T120000Z-' + 'a'.repeat(32) + '.json',
        throughput_bytes_per_second: 10,
        unique_bytes: 10,
        unique_objects: 1,
    };
    const data = { archive: { ...archive, verification: { ...verification, last_full_verification: last } }, repositories: [] };
    assert.equal(parseStatus(envelope('status', data)).error, null);
    last.completed_at = '2026-02-30T12:00:01Z';
    assert.equal(parseStatus(envelope('status', data)).payload, null);
});
test('failed read Envelopes remain values with no invented success payload', () => {
    for (const [command, parse] of [['status', parseStatus], ['version', parseVersion], ['doctor', parseDoctor]] as const) {
        const failed = envelope(command, {}, 20); const before = JSON.stringify(failed);
        const result = parse(failed); assert.equal(result.payload, null); assert.equal(result.error, null); assert.equal(result.partial, true);
        assert.equal(JSON.stringify(failed), before);
    }
});
test('recognized failed sections are partial and preserve the exact original value', () => {
    const data = { repositories: [repository] }; const failed = envelope('status', data, 20);
    const result = parseStatus(failed); assert.equal(result.payload, data); assert.equal(result.partial, true);
    assert.equal(parseVersion(envelope('version', { application: '0.1.3' }, 20)).error, null);
    assert.equal(parseDoctor(envelope('doctor', { checks: [{ name: 'configuration', outcome: 'fail', detail: 'Synthetic refusal' }] }, 20)).error, null);
});
for (const [name, data] of [
    ['missing', {}], ['bad archive', { archive: {}, repositories: [] }], ['bad rows', { archive, repositories: {} }],
    ['unknown field', { archive, repositories: [], synthetic_secret: 'never-render-this' }],
    ['unknown schema', { archive: { ...archive, schema_version: 9 }, repositories: [] }],
    ['wrong headroom', { archive: { ...archive, headroom_bytes: 0 }, repositories: [] }],
    ['unsafe count', { archive: { ...archive, unfinished_transactions: NaN }, repositories: [] }],
    ['inconsistent verification', { archive: { ...archive, verification: { ...verification, degraded: true } }, repositories: [] }],
    ['unknown entry object', { archive: { ...archive, unknown_entries: [{}] }, repositories: [] }],
    ['unknown finding', { archive: { ...archive, findings: [{ detail: 'never-render-this' }] }, repositories: [] }],
    ['nullable managed', { archive, repositories: [{ ...repository, enabled: null }] }],
    ['revision-qualified identity', { archive, repositories: [{ ...repository, repository_id: 'org/model@' + 'a'.repeat(40) }] }],
    ['inconsistent generations', { archive, repositories: [{ ...repository, retained_revisions: 1 }] }],
    ['duplicate selectors', { archive, repositories: [repository, repository] }],
] as const) {
    test('status refuses ' + name + ' with fixed bounded protocol failure', () => {
        const result = parseStatus(envelope('status', data)); assert.equal(result.payload, null);
        assert.equal(result.error?.category, 'protocol'); assert.equal(result.error?.stage, 'api-read');
        assert.ok(!result.error?.message.includes('never-render-this'));
    });
}
test('negative malformed partials keep their classification separate from safe schema error', () => {
    const failed = envelope('status', { repositories: [{}] }, 20);
    assert.equal(parseStatus(failed).error?.category, 'protocol'); assert.equal(failed.exit_code, 20);
});
test('version requires exact current server payload and retains supported unknown versions', () => {
    assert.equal(parseVersion(envelope('version', version)).error, null);
    assert.equal(parseVersion(envelope('version', { ...version, transfer_backend: 'xet unknown', application: 'unknown' })).error, null);
    for (const data of [{}, { ...version, python: 3 }, { ...version, transfer_backend: {} }, { ...version, token: 'never-render-this' }])
        assert.equal(parseVersion(envelope('version', data)).payload, null);
    assert.equal(parseVersion(envelope('status', version)).payload, null);
});
test('Doctor validates known ordered unique checks and bounded detail before rendering', () => {
    const checks = DOCTOR_CHECK_NAMES.map(name => ({ name, outcome: 'skipped', detail: 'Explicitly not exercised' }));
    assert.equal(parseDoctor(envelope('doctor', { checks })).error, null);
    for (const invalid of [null, [], {}, [checks[0], checks[0]], [{ ...checks[0], name: 'unknown' }], [{ ...checks[0], outcome: 'green' }],
        [{ ...checks[0], detail: { synthetic_secret: 'never-render-this' } }], [{ ...checks[0], detail: 'a'.repeat(4097) }], [{ ...checks[0], outcome: 'fail' }]])
        assert.equal(parseDoctor(envelope('doctor', { checks: invalid })).payload, null);
});
test('Doctor requires all seventeen current success checks while negative subsets remain partial', () => {
    const checks = [{ name: 'configuration', outcome: 'pass', detail: 'Configuration check completed' }];
    assert.equal(parseDoctor(envelope('doctor', { checks })).payload, null);
    const result = parseDoctor(envelope('doctor', { checks }, 20));
    assert.equal(result.error, null); assert.equal(result.partial, true); assert.equal(result.payload?.checks.length, 1);
});
