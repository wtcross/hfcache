/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { parseRunPage, parseRunReport } from '../src/lib/reports.ts';
import type { Envelope } from '../src/lib/envelope.ts';
import { ReadMetadataError } from '../src/lib/read-metadata.ts';
import type { RunReadMetadata } from '../src/lib/read-metadata.ts';

const report = JSON.parse(readFileSync(new URL('../../tests/fixtures/schemas/run-report.json', import.meta.url), 'utf8'));
const verification = JSON.parse(readFileSync(new URL('../../tests/fixtures/schemas/verification-report.json', import.meta.url), 'utf8'));
const metadata: RunReadMetadata = {
    schema_version: 1,
    command: 'runs read',
    run_id: report.run_id,
    request_id: 'b'.repeat(32),
    archive_id: report.archive_id,
    config_fingerprint: 'f'.repeat(64),
    next_cursor: null
};
function envelope(data: unknown, command = 'runs read'): Envelope {
    return {
        schema_version: 1,
        command,
        run_id: report.run_id,
        started_at: '2026-10-20T12:00:00Z',
        completed_at: '2026-10-20T12:00:01Z',
        exit_code: 0,
        outcome: 'success',
        data,
        warnings: [],
        errors: []
    };
}

test('V41 actual durable sync and failed verification fixtures preserve historical policy and outcome', () => {
    const parsed = parseRunReport(envelope({ report }), metadata, report.run_id, report.archive_id);
    assert.deepEqual(parsed, report);
    assert.notEqual(parsed.config_fingerprint, metadata.config_fingerprint);
    const failed = parseRunReport(envelope({ report: verification }), metadata, report.run_id);
    assert.deepEqual(failed, verification);
    assert.equal(failed.exit_code, 40);
});

test('V41 list pages preserve exact server order without a fabricated total or report filename', () => {
    const ids = ['f'.repeat(32), 'a'.repeat(32)];
    const page = parseRunPage(envelope({ runs: ids }, 'runs'), { ...metadata, command: 'runs', next_cursor: '-opaque-page' });
    assert.deepEqual(page, { runs: ids, nextCursor: '-opaque-page' });
    assert.deepEqual(parseRunPage(envelope({ runs: [] }, 'runs'), { ...metadata, command: 'runs' }), { runs: [], nextCursor: null });
});

for (const data of [{}, { runs: 'wrong' }, { runs: ['../unsafe'] }, { runs: ['a'.repeat(32), 'a'.repeat(32)] },
    { runs: Array.from({ length: 51 }, (_, index) => index.toString(16).padStart(32, '0')) }, { runs: [], total: 0 }]) {
    test('V42 invalid list success is unavailable rather than empty or silently truncated', () => {
        assert.throws(() => parseRunPage(envelope(data, 'runs'), { ...metadata, command: 'runs' }), ReadMetadataError);
    });
}

test('V42 a continuing cursor requires a nonempty page and stable archive/current policy identity', () => {
    assert.throws(() => parseRunPage(envelope({ runs: [] }, 'runs'), { ...metadata, command: 'runs', next_cursor: 'next' }), ReadMetadataError);
    for (const changed of [{ archive_id: '12345678-1234-1234-1234-123456789abc' }, { config_fingerprint: 'e'.repeat(64) }])
        assert.throws(() => parseRunPage(envelope({ runs: [report.run_id] }, 'runs'), { ...metadata, command: 'runs', ...changed }, metadata), ReadMetadataError);
});

for (const patch of [{ schema_version: 2 }, { schema_version: true }, { run_id: 'e'.repeat(32) },
    { archive_id: '12345678-1234-1234-1234-123456789abc' }, { config_fingerprint: 'bad' },
    { completed_at: '2020-01-01T00:00:00Z' }, { repositories: {} }, { repositories: [null] },
    { totals: { downloaded_bytes: -1 } }, { outcome: 'failed' }, { warnings: ['arbitrary secret prose'] },
    { extra_secret: 'SYNTHETIC_SECRET' }]) {
    test('V42/V51 malformed or wrong-identity report success refuses before raw data rendering', () => {
        assert.throws(() => parseRunReport(envelope({ report: { ...report, ...patch } }), metadata, report.run_id), error =>
            error instanceof ReadMetadataError && !error.message.includes('SYNTHETIC_SECRET'));
    });
}

test('V42 nested unknown report/repository/finding fields cannot enter raw JSON', () => {
    for (const malformed of [{ ...report, repositories: [{ ...report.repositories[0], extra_secret: 'SYNTHETIC_SECRET' }] },
        { ...verification, findings: [{ ...verification.findings[0], extra_secret: 'SYNTHETIC_SECRET' }] },
        { ...verification, mode: 'new' }, { ...verification, findings: 'wrong' }])
        assert.throws(() => parseRunReport(envelope({ report: malformed }), metadata, report.run_id), ReadMetadataError);
});

test('V42 requested, response, selected archive and durable run identities remain distinct and bound', () => {
    assert.throws(() => parseRunReport(envelope({ report }), metadata, 'e'.repeat(32)), ReadMetadataError);
    assert.throws(() => parseRunReport(envelope({ report }), metadata, report.run_id, '12345678-1234-1234-1234-123456789abc'), ReadMetadataError);
    assert.throws(() => parseRunReport(envelope({ report }), { ...metadata, run_id: 'e'.repeat(32) }, report.run_id), ReadMetadataError);
    assert.throws(() => parseRunReport(envelope({ report, wrapper: {} }), metadata, report.run_id), ReadMetadataError);
});
