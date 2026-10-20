/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
    classifyEnvelope, EnvelopeError, EnvelopeSchemaError, EXIT_CODE_GUIDANCE, extractEnvelope,
    operationCommands, operationEvidence, parseEnvelope,
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
        const parsed = parseEnvelope(envelope({
            exit_code: code,
            outcome: 'failed',
            errors: [{ code: 'HFERR001', repository: null, message: 'classified failure' }]
        }));
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

test('schema-1 decisions require complete coherent terminal evidence (CP-02)', () => {
    for (const overrides of [
        { run_id: 'short' }, { run_id: null }, { started_at: 'unknown' },
        { completed_at: undefined }, { data: [] }, { data: null },
        { exit_code: '0' }, { exit_code: true }, { exit_code: 21 },
        { outcome: 'done' }, { outcome: 'failed' }, { outcome: 'success_with_warnings' },
        { exit_code: 20, outcome: 'failed', errors: [] },
        { errors: [{ code: 'HFAPI018', repository: null, message: 'invalid' }] },
        { warnings: [{ code: 'HFWRN001', repository: null, message: 'warning' }] },
        { warnings: [{ code: 'HFWRN001', repository: null, message: 'warning', context: [] }] },
    ]) {
        assert.throws(() => parseEnvelope(envelope(overrides)), EnvelopeError, JSON.stringify(overrides));
    }
});

test('lost observation preserves handles without claiming that execution stopped (ADR122)', () => {
    for (const code of ['HFAPI013', 'HFAPI015', 'HFAPI019', 'HFAPI020']) {
        const result = parseEnvelope(envelope({
            command: 'sync',
            exit_code: 20,
            outcome: 'failed',
            data: { idempotency_key: 'original-key', operation_id: 'a'.repeat(32), work_may_continue: true },
            errors: [{ code, repository: null, message: 'observation unavailable' }],
        }));
        assert.equal(classifyEnvelope(result), 'observation');
        assert.deepEqual(operationEvidence(result), {
            idempotencyKey: 'original-key', operationId: 'a'.repeat(32), workMayContinue: true,
        });
    }
    const internal = parseEnvelope(envelope({
        exit_code: 20,
        outcome: 'failed',
        data: { work_may_continue: true },
        errors: [{ code: 'HFAPI008', repository: null, message: 'internal failure after submission' }]
    }));
    assert.equal(classifyEnvelope(internal), 'observation');
    assert.doesNotMatch(EXIT_CODE_GUIDANCE[10].guidance, /nothing was touched/i);
    assert.doesNotMatch(EXIT_CODE_GUIDANCE[20].guidance, /nothing.*changed/i);
});

test('malformed recovery handles never become displayed commands', () => {
    for (const data of [
        { idempotency_key: 'key; command', operation_id: '../../file', work_may_continue: 'true' },
        { idempotency_key: 'x'.repeat(129), operation_id: 'A'.repeat(32) },
        { idempotency_key: '[REDACTED]', operation_id: 12 },
    ])
        assert.deepEqual(operationEvidence(parseEnvelope(envelope({ data }))), { workMayContinue: false });
});

test('stale policy refusal stays a classified result with its exact evidence', () => {
    const result = parseEnvelope(envelope({
        command: 'prune',
        exit_code: 10,
        outcome: 'failed',
        errors: [{ code: 'HFAPI007', repository: null, message: 'Installed policy changed after admission' }]
    }));
    assert.equal(classifyEnvelope(result), 'invalid');
    assert.equal(result.errors[0].code, 'HFAPI007');
});

test('valid option-like keys remain positional data in reconnect commands', () => {
    const evidence = operationEvidence(parseEnvelope(envelope({
        data: {
            idempotency_key: '--help', operation_id: 'a'.repeat(32),
        }
    })));
    const fixed = 'sudo systemd-run --quiet --wait --pipe --collect --property=User=hfcache ' +
        '--property=Group=hfcache --property=UMask=0027 --property=MemoryHigh=4G -- ' +
        '/usr/local/libexec/hfcache-client --client-config /etc/hfcache/client.toml ' +
        '--api-socket /run/hfcache/api/api.sock --json';
    assert.deepEqual(operationCommands(evidence), {
        lookup: fixed + " operations lookup -- '--help'",
        wait: fixed + ` operations wait -- '${'a'.repeat(32)}'`,
    });
    assert.equal(operationCommands(evidence, 'b'.repeat(64)).lookup,
                 fixed + ` --expected-client-scope ${'b'.repeat(64)} operations lookup -- '--help'`);
    assert.deepEqual(operationCommands({ idempotencyKey: 'x; command', workMayContinue: false }), {});
    assert.equal(operationCommands({ idempotencyKey: '~root', workMayContinue: false }).lookup,
                 fixed + " operations lookup -- '~root'");
});
