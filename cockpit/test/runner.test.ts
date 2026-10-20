/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';

import type { Envelope } from '../src/lib/envelope.ts';
import type { OperationNotice } from '../src/lib/events.ts';
import { FAILURE_STAGES } from '../src/lib/failure.ts';
import { HfcacheSpawnError, runSpawned } from '../src/lib/runner.ts';
import type { StreamProcess } from '../src/lib/runner.ts';
import { DIAGNOSTIC_BYTES, TERMINAL_BYTES, utf8Bytes } from '../src/lib/stream.ts';

const ID = 'a'.repeat(32);
const handles = `Idempotency key: stable-key\nOperation: ${ID}\n`;

function envelope(exit = 0, code = 'HFAPI001'): Envelope {
    return {
        schema_version: 1,
        command: 'sync',
        run_id: 'b'.repeat(32),
        started_at: '2026-10-18T12:00:00.000000Z',
        completed_at: '2026-10-18T12:00:01.000000Z',
        exit_code: exit,
        outcome: exit === 0 ? 'success' : 'failed',
        data: {},
        warnings: [],
        errors: exit === 0 ? [] : [{ code, repository: null, message: 'Refused safely' }],
    };
}

function process(chunks: string[], failure = false, wait?: Promise<void>): StreamProcess {
    let callback: (chunk: string) => void = () => undefined;
    const promise = Promise.resolve().then(async () => {
        for (const chunk of chunks)
            callback(chunk);
        await wait;
        if (failure)
            throw new Error('process exited nonzero');
    });
    return Object.assign(promise, { stream: (value: (chunk: string) => void) => { callback = value } });
}

for (const [exit, code] of [[10, 'HFAPI001'], [20, 'HFMNT010'], [10, 'HFAPI007'], [30, 'HFHUB001']] as const) {
    test(`exact ${code} failure Envelope survives a rejected process`, async () => {
        const result = envelope(exit, code);
        assert.deepEqual(await runSpawned(['hfcache'], () => process([handles, JSON.stringify(result)], true)), result);
    });
}

test('a single large progress callback preserves early handles and a large final JSON line', async () => {
    const result = envelope(40, 'HFVER001');
    result.data = { findings: 'x'.repeat(12000) };
    const notices: OperationNotice[] = [];
    const lines: string[] = [];
    const progress = Array.from({ length: 10000 }, (_, index) => `[${index + 1}] running: Hashing\n`).join('');
    assert.deepEqual(await runSpawned(['hfcache'], () => process([handles + progress + JSON.stringify(result)], true), {
        onNotice: notice => notices.push(notice), onLine: line => lines.push(line),
    }), result);
    assert.ok(notices.some(notice => notice.kind === 'key' && notice.key === 'stable-key'));
    assert.ok(notices.some(notice => notice.kind === 'operation' && notice.operationId === ID));
    assert.ok(lines.length <= 257);
    assert.ok(lines.some(line => line.includes('Progress display truncated')));
});

test('pretty terminal JSON survives chunking and oversized progress', async () => {
    const result = envelope();
    const body = JSON.stringify(result, null, 2);
    const chunks = [handles, 'x'.repeat(20000) + '\n', ...body.match(/.{1,7}|\n/g)!];
    assert.deepEqual(await runSpawned(['hfcache'], () => process(chunks)), result);
});

test('page closure detaches callbacks while the existing process completes', async () => {
    const controller = new AbortController();
    let complete: (() => void) | undefined;
    const wait = new Promise<void>(resolve => { complete = resolve });
    let calls = 0;
    const result = envelope(30, 'HFHUB001');
    const pending = runSpawned(['hfcache'], () => process([handles, '[1] running: First\n', JSON.stringify(result)], true, wait), {
        signal: controller.signal,
        onLine: () => { calls += 1; controller.abort() },
    });
    let finished = false;
    pending.then(() => { finished = true });
    await Promise.resolve();
    await Promise.resolve();
    assert.equal(finished, false);
    complete!();
    assert.deepEqual(await pending, result);
    assert.equal(calls, 1);
});

test('terminal overflow waits for process completion then refuses with retained handles', async () => {
    let complete: (() => void) | undefined;
    const wait = new Promise<void>(resolve => { complete = resolve });
    const pending = runSpawned(['hfcache'], () => process([handles, '{"data":"', 'x'.repeat(TERMINAL_BYTES), '"}\n'], false, wait));
    let finished = false;
    pending.catch(() => { finished = true });
    await Promise.resolve();
    await Promise.resolve();
    assert.equal(finished, false);
    complete!();
    await assert.rejects(pending, error => {
        assert.ok(error instanceof HfcacheSpawnError);
        assert.equal(error.idempotencyKey, 'stable-key');
        assert.equal(error.operationId, ID);
        assert.equal(error.workMayContinue, true);
        assert.ok(utf8Bytes(error.stderr) <= DIAGNOSTIC_BYTES);
        return true;
    });
});

test('invalid or absent result never invents domain success', async () => {
    for (const body of ['', '{"schema_version":2}']) {
        await assert.rejects(runSpawned(['hfcache'], () => process([handles, body], true)), error => {
            assert.ok(error instanceof HfcacheSpawnError);
            assert.equal(error.operationId, ID);
            return true;
        });
    }
});

test('unknown schema retains safe upgrade guidance without echoing its value', async () => {
    const value = 'opaque-untrusted-schema-value';
    await assert.rejects(runSpawned(['hfcache'], () => process([handles, JSON.stringify({ schema_version: value })])), error => {
        assert.ok(error instanceof HfcacheSpawnError);
        assert.match(error.message, /update the plugin to match the deployed hfcache/);
        assert.ok(!error.message.includes(value));
        assert.equal(error.operationId, ID);
        assert.equal(error.idempotencyKey, 'stable-key');
        return true;
    });
});

test('lost result retains early handles independently of diagnostic tail eviction', async () => {
    const progress = '[1] running: Hashing\n'.repeat(10000);
    await assert.rejects(runSpawned(['hfcache'], () => process([handles + progress], true)), error => {
        assert.ok(error instanceof HfcacheSpawnError);
        assert.equal(error.idempotencyKey, 'stable-key');
        assert.equal(error.operationId, ID);
        assert.equal(error.workMayContinue, true);
        assert.ok(!error.stderr.includes('Idempotency key:'));
        assert.ok(utf8Bytes(error.stderr) <= DIAGNOSTIC_BYTES);
        return true;
    });
});

test('installed confirmation requires process completion even with a valid success Envelope', async () => {
    const result = envelope();
    result.command = 'config validate';
    await assert.rejects(runSpawned(['fixed-confirmation'], () => process([JSON.stringify(result)], true), {}, true),
                         /Installed confirmation did not complete successfully/);
    assert.deepEqual(await runSpawned(['fixed-confirmation'], () => process([JSON.stringify(result)]), {}, true), result);
});

function rejectedProcess(chunks: string[], failure: unknown): StreamProcess {
    let callback: (chunk: string) => void = () => undefined;
    return Object.assign(Promise.resolve().then(() => {
        for (const chunk of chunks)
            callback(chunk);
        throw failure;
    }), { stream: (value: (chunk: string) => void) => { callback = value } });
}

for (const stage of FAILURE_STAGES) {
    test(`actual runner retains a reconnected rejection at ${stage}`, async () => {
        for (const failure of [new Error('reconnected'), { problem: 'reconnected', message: 'sensitive rejection prose' }]) {
            await assert.rejects(runSpawned(['fixed-client'], () => rejectedProcess([], failure), { stage }), error => {
                assert.ok(error instanceof HfcacheSpawnError);
                assert.equal(error.stage, stage);
                assert.equal(error.category, 'bridge');
                assert.equal(error.problem, 'reconnected');
                assert.equal(error.workMayContinue, false);
                assert.ok(!error.message.includes('sensitive rejection prose'));
                return true;
            });
        }
    });
}

test('launcher, process and access facts survive actual runner rejection independently of raw stderr', async () => {
    for (const [failure, category] of [
        [{ problem: 'not-found', message: 'sensitive launcher details' }, 'launcher'],
        [{ problem: 'access-denied', message: 'sensitive PAM details' }, 'access'],
        [{ exit_status: 17, exit_signal: 'TERM', message: 'sensitive process details' }, 'process'],
    ] as const) {
        await assert.rejects(runSpawned(['fixed-client'], () => rejectedProcess(['sensitive stderr\n'], failure)), error => {
            assert.ok(error instanceof HfcacheSpawnError);
            assert.equal(error.category, category);
            assert.equal(error.exitStatus, category === 'process' ? 17 : undefined);
            assert.equal(error.exitSignal, category === 'process' ? 'TERM' : undefined);
            assert.ok(!error.message.includes('sensitive'));
            assert.ok(!error.stderr.includes('sensitive'));
            return true;
        });
    }
});

test('untrusted stderr and terminal bodies never enter browser display callbacks or retained diagnostics', async () => {
    const sentinel = 'synthetic-api-hub-mcp-candidate-secret';
    const lines: string[] = [];
    await assert.rejects(runSpawned(['fixed-client'], () => rejectedProcess([
        handles, sentinel + '\n', '[1] running: safe progress\n',
        JSON.stringify({ schema_version: sentinel }),
    ], { problem: sentinel, message: sentinel, stderr: sentinel }), { onLine: line => lines.push(line) }), error => {
        assert.ok(error instanceof HfcacheSpawnError);
        assert.equal(error.problem, 'unknown');
        assert.equal(error.category, 'protocol');
        assert.ok(!JSON.stringify(error).includes(sentinel));
        assert.ok(!error.message.includes(sentinel));
        assert.ok(!error.stderr.includes(sentinel));
        assert.equal(error.idempotencyKey, 'stable-key');
        assert.equal(error.operationId, ID);
        return true;
    });
    assert.ok(lines.includes('[1] running: safe progress'));
    assert.ok(!lines.some(line => line.includes(sentinel)));
});

test('installed postcheck rejection retains the original bridge cause instead of accepting stdout', async () => {
    const result = envelope();
    result.command = 'config validate';
    await assert.rejects(runSpawned(['fixed-confirmation'], () => rejectedProcess([JSON.stringify(result)], {
        problem: 'reconnected', exit_status: 17, exit_signal: 'TERM', message: 'private postcheck detail',
    }), { stage: 'installed-confirm' }, true), error => {
        assert.ok(error instanceof HfcacheSpawnError);
        assert.equal(error.stage, 'installed-confirm');
        assert.equal(error.category, 'bridge');
        assert.equal(error.problem, 'reconnected');
        assert.equal(error.exitStatus, 17);
        assert.equal(error.exitSignal, 'TERM');
        assert.equal(error.hostMutationUncertain, true);
        assert.match(error.message, /Installed confirmation did not complete successfully/);
        assert.ok(!error.message.includes('private postcheck detail'));
        return true;
    });
    await assert.rejects(runSpawned(['fixed-confirmation'], () => rejectedProcess([JSON.stringify(result)], null), {}, true),
                         /Installed confirmation did not complete successfully/);
});

test('late handles survive aborted display and callback failure without a process-close shortcut', async () => {
    for (const abort of [false, true]) {
        const controller = new AbortController();
        let displays = 0;
        let closes = 0;
        const spawned = rejectedProcess(['[1] running: first\n', handles], { problem: 'reconnected' });
        const withClose = Object.assign(spawned, { close: () => { closes += 1 } });
        await assert.rejects(runSpawned(['fixed-client'], () => withClose, {
            signal: controller.signal,
            onLine: () => {
                displays += 1;
                if (abort)
                    controller.abort();
                else
                    throw new Error('display detached');
            },
        }), error => {
            assert.ok(error instanceof HfcacheSpawnError);
            assert.equal(error.idempotencyKey, 'stable-key');
            assert.equal(error.operationId, ID);
            assert.equal(error.workMayContinue, true);
            return true;
        });
        assert.equal(displays, 1);
        assert.equal(closes, 0);
    }
});

test('failed installed validation Envelope remains classified evidence after nonzero process exit', async () => {
    const refused = envelope(10, 'HFAPI003');
    refused.command = 'config validate';
    assert.deepEqual(await runSpawned(['fixed-confirmation'], () =>
        process([JSON.stringify(refused)], true), {}, true), refused);
});
