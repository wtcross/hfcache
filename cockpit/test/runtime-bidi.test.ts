/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import childProcess from 'node:child_process';
import type { SpawnOptions } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { syncBuiltinESMExports } from 'node:module';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

import { RuntimeCheckError, startFirefox } from './runtime-bidi.mjs';

// Real helper/owned filesystem with only process/protocol boundaries controlled.
// These are recovery preservation regressions, never Firefox/PAM acceptance.
class ControlledSocket extends EventTarget {
    constructor() {
        super();
        queueMicrotask(() => this.dispatchEvent(new Event('open')));
    }

    send(body: string) {
        const request = JSON.parse(body);
        const result = request.method === 'session.new'
            ? { capabilities: { browserVersion: 'controlled-fixture' } }
            : { context: 'controlled-context' };
        queueMicrotask(() => this.dispatchEvent(new MessageEvent('message', {
            data: JSON.stringify({ type: 'success', id: request.id, result })
        })));
    }

    close() {}
}

for (const startupFailure of [true, false]) {
    test(`retained runtime profile survives ${startupFailure ? 'startup failure' : 'default close'}`, async t => {
        const profile = await mkdtemp(join(tmpdir(), 'hfcache-cpr008-bidi-'));
        const marker = join(profile, 'original-operation.json');
        const original = '{"key":"synthetic-original","state":"uncertain"}\n';
        await writeFile(marker, original, { mode: 0o600 });
        const spawn = childProcess.spawn;
        const socket = globalThis.WebSocket;
        t.mock.method(childProcess, 'spawn', (command: string, args: string[], options: SpawnOptions) => {
            assert.equal(command, '/usr/bin/firefox');
            assert.ok(args.includes(profile));
            const program = startupFailure
                ? 'process.exit(17)'
                : "process.stderr.write('WebDriver BiDi listening on ws://127.0.0.1:59999\\n');setTimeout(()=>{},60000)";
            return spawn(process.execPath, ['-e', program], options);
        });
        syncBuiltinESMExports();
        globalThis.WebSocket = ControlledSocket as unknown as typeof WebSocket;
        try {
            if (startupFailure) {
                await assert.rejects(startFirefox(profile), error =>
                    error instanceof RuntimeCheckError && error.code === 'firefox-exit');
            } else {
                const browser = await startFirefox(profile);
                assert.equal(browser.profile, profile);
                await browser.close();
            }
            assert.equal(await readFile(marker, 'utf8'), original);
        } finally {
            globalThis.WebSocket = socket;
            t.mock.restoreAll();
            syncBuiltinESMExports();
            await rm(profile, { recursive: true, force: true });
        }
    });
}

// Exercise the exact emitted browser expression: template escaping crosses a
// JavaScript realm and cannot be verified by checking source regex spelling.
async function failureProjection(text: string) {
    const source = await readFile(new URL('./runtime-browser.mjs', import.meta.url), 'utf8');
    const literal = /const failure = await browser\.evaluate\(browser\.context, (`[\s\S]*?`)\);/.exec(source)?.[1];
    assert.ok(literal, 'actual runtime failure projection template');
    const expression = runInNewContext(literal);
    assert.equal(typeof expression, 'string');
    return JSON.parse(runInNewContext(expression, {
        document: {
            querySelectorAll: (selector: string) => selector === '.pf-v6-c-alert' ? [{ textContent: text }] : [],
            body: { textContent: text },
        },
    }));
}

test('runtime failure projection preserves classified facts across template evaluation', async () => {
    const result = await failureProjection('candidate-write: Host connection interrupted; Host problem: reconnected; ' +
        'Process exit status: 17; Process exit signal: SIGTERM; HFAPI003; secret-fixture-prose-withheld');
    assert.equal(result.facts[0].stage, 'candidate-write');
    assert.equal(result.facts[0].category, 'bridge');
    assert.equal(result.facts[0].problem, 'reconnected');
    assert.equal(result.facts[0].exit_status, '17');
    assert.equal(result.facts[0].exit_signal, 'SIGTERM');
    assert.deepEqual(result.facts[0].codes, ['HFAPI003']);
    assert.ok(!JSON.stringify(result).includes('secret-fixture-prose-withheld'));
});

test('runtime failure projection withholds unknown problem and arbitrary prose', async () => {
    const result = await failureProjection('Host problem: secret-fixture-problem; arbitrary-fixture-credential');
    assert.equal(result.facts[0].problem, null);
    assert.equal(result.facts[0].exit_status, null);
    assert.deepEqual(result.facts[0].codes, []);
    assert.ok(!JSON.stringify(result).includes('secret-fixture'));
    assert.ok(!JSON.stringify(result).includes('arbitrary-fixture-credential'));
});
