/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
    classifyEnvelope, EnvelopeError, EnvelopeSchemaError, EXIT_CODE_GUIDANCE, extractEnvelope, parseEnvelope,
} from '../src/lib/envelope.ts';

function envelope(overrides: Record<string, unknown> = {}): string {
    return JSON.stringify({
        schema_version: 1,
        command: 'status',
        run_id: '4c1e8a55b0d24f1e9a3c7d2b6f80e114',
        started_at: '2026-07-24T20:38:11.500000Z',
        completed_at: '2026-07-24T20:41:46.002000Z',
        exit_code: 0,
        outcome: 'success',
        data: {},
        warnings: [],
        errors: [],
        ...overrides,
    });
}

test('a success envelope parses and classifies', () => {
    const parsed = parseEnvelope(envelope());
    assert.equal(parsed.command, 'status');
    assert.equal(classifyEnvelope(parsed), 'success');
});

test('a failure envelope still parses: the envelope is emitted even on failure', () => {
    const parsed = parseEnvelope(envelope({
        exit_code: 20,
        outcome: 'failed',
        errors: [{ code: 'HFMNT005', repository: null, message: 'sentinel missing' }],
    }));
    assert.equal(parsed.exit_code, 20);
    assert.equal(classifyEnvelope(parsed), 'refused');
});

test('the lock holder is busy, not failed (CP-10)', () => {
    const parsed = parseEnvelope(envelope({
        exit_code: 20,
        outcome: 'failed',
        errors: [{ code: 'HFMNT010', repository: null, message: 'lock held' }],
    }));
    assert.equal(classifyEnvelope(parsed), 'busy');
});

test('warnings flip a zero exit to the warnings state', () => {
    const parsed = parseEnvelope(envelope({
        outcome: 'success_with_warnings',
        warnings: [{ code: 'HFWRN007', repository: 'model:a/b', message: 'unmanaged' }],
    }));
    assert.equal(classifyEnvelope(parsed), 'warnings');
});

test('every non-zero class maps to its UI state', () => {
    const expectations: Array<[number, string]> = [
        [10, 'invalid'], [30, 'sync_failures'], [40, 'integrity'], [50, 'maintenance'],
    ];
    for (const [code, kind] of expectations) {
        const parsed = parseEnvelope(envelope({ exit_code: code, outcome: 'failed' }));
        assert.equal(classifyEnvelope(parsed), kind, `exit ${code}`);
    }
});

test('a schema_version other than 1 is refused with guidance (CP-02)', () => {
    assert.throws(() => parseEnvelope(envelope({ schema_version: 2 })), EnvelopeSchemaError);
});

test('non-JSON stdout is an EnvelopeError, never interpreted', () => {
    assert.throws(() => parseEnvelope('Traceback (most recent call last):'), EnvelopeError);
    assert.throws(() => parseEnvelope('[]'), EnvelopeError);
});

test('missing or mistyped required fields are an EnvelopeError', () => {
    assert.throws(() => parseEnvelope(JSON.stringify({ schema_version: 1 })), EnvelopeError);
    assert.throws(
        () => parseEnvelope(envelope({ errors: [{ code: 42, repository: null, message: 'x' }] })),
        EnvelopeError);
});

test('the envelope is extracted from a merged logfmt stream', () => {
    const pretty = JSON.stringify(JSON.parse(envelope({ command: 'sync' })), null, 2);
    const mixed = 'event=run.started level=info run_id=abc repositories=1\n' +
        'event=repository.resolved level=info run_id=abc repository=model:a/b\n' +
        `${pretty}\n`;
    assert.equal(extractEnvelope(mixed).command, 'sync');
    assert.equal(extractEnvelope(envelope()).command, 'status');
});

test('a stream with no envelope is an EnvelopeError', () => {
    assert.throws(() => extractEnvelope('event=run.started level=info\nnothing else'), EnvelopeError);
});

test('every documented exit code carries operator guidance', () => {
    for (const code of [0, 10, 20, 30, 40, 50]) {
        assert.ok(EXIT_CODE_GUIDANCE[code]?.title, `exit ${code}`);
        assert.ok(EXIT_CODE_GUIDANCE[code]?.guidance, `exit ${code}`);
    }
});
