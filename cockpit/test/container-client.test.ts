/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';

import { HFCACHE_CLI, hfcacheArgv } from '../src/lib/command.ts';
import type { Envelope } from '../src/lib/envelope.ts';
import type { OperationNotice } from '../src/lib/events.ts';
import { HfcacheSpawnError, runSpawned } from '../src/lib/runner.ts';
import type { Spawn } from '../src/lib/runner.ts';

const OPERATION = 'a'.repeat(32);
const KEY = 'container-client-key';

function fixture(exit: number, terminal = true) {
    const directory = mkdtempSync(join(tmpdir(), 'hfcache-container-client-'));
    const argumentsPath = join(directory, 'arguments.json');
    const resultPath = join(directory, 'result.json');
    const launcher = join(directory, 'client-fixture.mjs');
    const envelope: Envelope = {
        schema_version: 1,
        command: 'sync',
        run_id: 'b'.repeat(32),
        started_at: '2026-10-18T12:00:00.000000Z',
        completed_at: '2026-10-18T12:00:01.000000Z',
        exit_code: exit,
        outcome: exit === 0 ? 'success' : 'failed',
        data: { partial: exit === 30 },
        warnings: [],
        errors: exit === 0
            ? []
            : [{
                code: exit === 40 ? 'HFVER001' : exit === 30 ? 'HFHUB001' : 'HFAPI009',
                repository: null,
                message: 'Fixture refused safely',
            }],
    };
    writeFileSync(resultPath, terminal ? JSON.stringify(envelope) + '\n' : '');
    // Cockpit merges stderr into the same output stream. This real child
    // provides that merged stream without invoking a service manager or Podman.
    writeFileSync(launcher, [
        "import { readFileSync, writeFileSync } from 'node:fs';",
        'writeFileSync(process.env.HFCACHE_TEST_ARGUMENTS, JSON.stringify(process.argv.slice(2)));',
        'process.stdout.write(' + JSON.stringify('Idempotency key: ' + KEY + '\nOperation: ' + OPERATION + '\n') + ');',
        "process.stdout.write('[1] waiting_lock: Waiting for the archive lock\\n');",
        'setImmediate(() => {',
        "    process.stdout.write('[2] running: Observing λ\\n');",
        "    process.stdout.write(readFileSync(process.env.HFCACHE_TEST_RESULT, 'utf8'));",
        '    process.exitCode = ' + exit + ';',
        '});',
    ].join('\n'));
    let calls = 0;
    const client: Spawn = argv => {
        const separator = argv.indexOf('--');
        assert.ok(separator > 0);
        assert.equal(argv[separator + 1], HFCACHE_CLI);
        calls += 1;
        const child = spawn(process.execPath, [launcher, ...argv.slice(separator + 2)], {
            env: {
                HFCACHE_TEST_ARGUMENTS: argumentsPath,
                HFCACHE_TEST_RESULT: resultPath,
            },
            stdio: ['ignore', 'pipe', 'pipe'],
        });
        let receive: (chunk: string) => void = () => undefined;
        child.stdout.setEncoding('utf8').on('data', chunk => receive(chunk));
        child.stderr.setEncoding('utf8').on('data', chunk => receive(chunk));
        const completion = new Promise<void>((resolve, reject) => {
            child.once('error', reject);
            child.once('close', code => {
                if (code === 0)
                    resolve();
                else
                    reject(new Error('Container client exited nonzero'));
            });
        });
        return Object.assign(completion, {
            stream(callback: (chunk: string) => void) {
                receive = callback;
            },
        });
    };
    return {
        client,
        envelope,
        calls: () => calls,
        arguments: () => JSON.parse(readFileSync(argumentsPath, 'utf8')) as string[],
        close: () => rmSync(directory, { recursive: true, force: true }),
    };
}

for (const exit of [0, 10, 20, 30, 40, 50]) {
    test('fixed rootless launcher preserves real child progress and exact exit-' + exit + ' Envelope', async () => {
        const files = fixture(exit);
        const notices: OperationNotice[] = [];
        const lines: string[] = [];
        try {
            const result = await runSpawned(
                hfcacheArgv(['sync', 'model:org/repository']),
                files.client,
                { onNotice: notice => notices.push(notice), onLine: line => lines.push(line) },
            );
            assert.deepEqual(result, files.envelope);
            assert.equal(files.calls(), 1);
            assert.deepEqual(files.arguments(), [
                '--client-config', '/etc/hfcache/client.toml',
                '--api-socket', '/run/hfcache/api/api.sock', '--json',
                'sync', 'model:org/repository',
            ]);
            assert.ok(notices.some(notice => notice.kind === 'key' && notice.key === KEY));
            assert.ok(notices.some(notice => notice.kind === 'operation' &&
                notice.operationId === OPERATION));
            assert.ok(notices.some(notice => notice.kind === 'progress' &&
                notice.sequence === 2 && notice.message === 'Observing λ'));
            assert.ok(lines.includes('[1] waiting_lock: Waiting for the archive lock'));
        } finally {
            files.close();
        }
    });
}

test('option-shaped CLI values remain data after the fixed container-client boundary', async () => {
    const files = fixture(10);
    const key = '--volume=/srv/hfcache:/archive:rw';
    try {
        const argv = hfcacheArgv(['operations', 'lookup', '--', key]);
        const separator = argv.indexOf('--');
        assert.equal(argv[separator + 1], '/usr/local/libexec/hfcache-client');
        assert.ok(!argv.slice(0, separator).some(part => /podman|image|volume|Credential/.test(part)));
        assert.deepEqual(await runSpawned(argv, files.client), files.envelope);
        assert.deepEqual(files.arguments().slice(-4), ['operations', 'lookup', '--', key]);
        assert.equal(files.calls(), 1);
    } finally {
        files.close();
    }
});

test('real launcher failure without a terminal Envelope preserves handles and never retries', async () => {
    const files = fixture(20, false);
    try {
        await assert.rejects(runSpawned(hfcacheArgv(['sync']), files.client), error => {
            assert.ok(error instanceof HfcacheSpawnError);
            assert.equal(error.idempotencyKey, KEY);
            assert.equal(error.operationId, OPERATION);
            assert.equal(error.workMayContinue, true);
            return true;
        });
        assert.equal(files.calls(), 1);
    } finally {
        files.close();
    }
});
