/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ReadMetadataCollector, ReadMetadataError, READ_METADATA_LINE_BYTES, READ_METADATA_PREFIX, parseReadMetadataLine } from '../src/lib/read-metadata.ts';
import type { RunReadMetadata } from '../src/lib/read-metadata.ts';
import { HfcacheSpawnError, runSpawned } from '../src/lib/runner.ts';
import type { StreamProcess } from '../src/lib/runner.ts';
import type { Envelope } from '../src/lib/envelope.ts';

const ID = 'a'.repeat(32);
const metadata: RunReadMetadata = {
    schema_version: 1,
    command: 'runs',
    run_id: ID,
    request_id: 'b'.repeat(32),
    archive_id: '12345678-1234-1234-1234-123456789abc',
    config_fingerprint: 'c'.repeat(64),
    next_cursor: '-opaque_page'
};
const line = (changes: Record<string, unknown> = {}) => READ_METADATA_PREFIX + JSON.stringify({ ...metadata, ...changes });
const envelope = (exit = 0): Envelope => ({
    schema_version: 1,
    command: 'runs',
    run_id: ID,
    started_at: '2026-10-20T12:00:00Z',
    completed_at: '2026-10-20T12:00:01Z',
    exit_code: exit,
    outcome: exit ? 'failed' : 'success',
    data: exit ? {} : { runs: [] },
    warnings: [],
    errors: exit ? [{ code: 'HFAPI003', repository: null, message: 'Classified report refusal' }] : []
});
function process(chunks: string[], failed = false): StreamProcess {
    let receive: (chunk: string) => void = () => undefined;
    return Object.assign(Promise.resolve().then(() => {
        for (const chunk of chunks) receive(chunk);
        if (failed) throw Object.assign(new Error('SYNTHETIC_SECRET'), { problem: 'reconnected' });
    }), { stream: (callback: (chunk: string) => void) => { receive = callback } });
}

test('V41 exact bounded read metadata is independent of operation receipts', () => {
    assert.deepEqual(parseReadMetadataLine(line()), metadata);
    assert.equal(parseReadMetadataLine('Operation: ' + ID), null);
    assert.equal(parseReadMetadataLine('arbitrary SYNTHETIC_SECRET stderr'), null);
});

for (const changes of [{ schema_version: true }, { schema_version: 2 }, { command: 'sync' }, { run_id: '../unsafe' },
    { request_id: 'A'.repeat(32) }, { archive_id: null }, { config_fingerprint: null }, { next_cursor: '' },
    { next_cursor: 'secret\nvalue' }, { next_cursor: 'x'.repeat(257) }, { extra_secret: 'SYNTHETIC_SECRET' },
    { command: 'runs read', next_cursor: 'unexpected' }]) {
    test('V42/V51 incompatible read metadata refuses without echo', () => {
        assert.throws(() => parseReadMetadataLine(line(changes)), error => error instanceof ReadMetadataError && !error.message.includes('SYNTHETIC_SECRET'));
    });
}

test('V42 duplicate keys escaped aliases whitespace and oversized notice lines refuse', () => {
    for (const value of [line().replace('"schema_version":1', '"schema_version":1,"schema_version":1'),
        line().replace('"schema_version"', '"schema_\\u0076ersion"'), READ_METADATA_PREFIX + ' '.repeat(READ_METADATA_LINE_BYTES) + '{}',
        line() + ' ', READ_METADATA_PREFIX + 'not-json-SYNTHETIC_SECRET'])
        assert.throws(() => parseReadMetadataLine(value), ReadMetadataError);
});

test('V41 metadata framing survives arbitrary chunks and display eviction without retaining other data', () => {
    const seen: Readonly<RunReadMetadata>[] = [];
    const collector = new ReadMetadataCollector(value => seen.push(value));
    const input = 'SYNTHETIC_SECRET'.repeat(10000) + '\n' + '[1] running: safe\n'.repeat(10000) + line();
    for (const chunk of input.match(/.{1,13}|\n/g)!) collector.push(chunk);
    collector.finish();
    assert.deepEqual(collector.result(), metadata);
    assert.deepEqual(seen, [metadata]);
});

test('V42 duplicate malformed and oversized prefixed lines cannot be rescued by a later valid line', () => {
    for (const input of [line() + '\n' + line(), READ_METADATA_PREFIX + 'not-json\n' + line(),
        READ_METADATA_PREFIX + 'x'.repeat(10000) + '\n' + line()]) {
        const collector = new ReadMetadataCollector(); collector.push(input); collector.finish();
        assert.throws(() => collector.result(), ReadMetadataError);
    }
});

test('V41 successful report observation refuses missing read metadata', async () => {
    await assert.rejects(runSpawned(['fixed-client'], () => process([JSON.stringify(envelope())]), { onReadMetadata: () => undefined }), HfcacheSpawnError);
});

test('V41 successful report observation binds metadata to the exact terminal command and run ID', async () => {
    for (const prefix of [line({ run_id: 'f'.repeat(32) }), line({ command: 'runs read', next_cursor: null }), line() + '\n' + line()])
        await assert.rejects(runSpawned(['fixed-client'], () => process([prefix + '\n', JSON.stringify(envelope())]), { onReadMetadata: () => undefined }), HfcacheSpawnError);
});

test('V41 read metadata collection remains attached after aborted or failed display callbacks', async () => {
    for (const aborted of [false, true]) {
        const controller = new AbortController(); if (aborted) controller.abort();
        const seen: Readonly<RunReadMetadata>[] = [];
        assert.deepEqual(await runSpawned(['fixed-client'], () => process(['[1] running: safe\n', line() + '\n', JSON.stringify(envelope())]), {
            signal: controller.signal, onReadMetadata: value => seen.push(value), onLine: () => { throw new Error('detached') },
        }), envelope());
        assert.deepEqual(seen, [metadata]);
    }
});

test('V42 metadata callback failure refuses success but preserves an exact negative Envelope', async () => {
    for (const prefix of ['', line() + '\n', READ_METADATA_PREFIX + 'not-json\n']) {
        assert.deepEqual(await runSpawned(['fixed-client'], () => process([prefix, JSON.stringify(envelope(10))], true), {
            onReadMetadata: () => { throw new Error('callback failed') },
        }), envelope(10));
    }
    await assert.rejects(runSpawned(['fixed-client'], () => process([line() + '\n', JSON.stringify(envelope())]), {
        onReadMetadata: () => { throw new Error('callback failed') },
    }), HfcacheSpawnError);
});
