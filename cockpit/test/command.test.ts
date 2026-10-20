/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
    assertCockpitCommand, CommandSurfaceError, formatSelector, hfcacheArgv, isFullCommitSha, parseSelector, SelectorError,
} from '../src/lib/command.ts';

const SHA = '0123456789abcdef0123456789abcdef01234567';

test('plugin dispatch accepts only its closed authenticated command surface', () => {
    for (const command of [
        ['version', '--server'], ['client', 'describe'], ['status'], ['list', '--revisions'],
        ['config', 'validate'], ['verify', '--estimate'], ['verify', '--full'], ['verify', '--new'], ['doctor'], ['doctor', '--read-only'],
        ['prune', '--apply'], ['recover', '--dry-run'], ['sync'], ['sync', 'model:org/model'],
        ['plan'], ['plan', 'dataset:org/data'], ['verify', '--revision', `model:org/model@${SHA}`],
        ['repair', `model:org/model@${SHA}`, '--reason', '--help'],
    ])
        assert.doesNotThrow(() => assertCockpitCommand(command));
    for (const command of [
        [], ['--quiet', 'sync'], ['--api-url', 'https://SYNTHETIC_SECRET', 'sync'],
        ['archive', 'init', '--confirm'], ['config', 'validate', '--local'], ['version'],
        ['verify', '--estimate', '--full'], ['sync', '--config', '/tmp/other'],
        ['purge', '--apply'], ['catalog', 'refresh'], ['unknown'], ['doctor', '--local'],
        ['verify', '--revision', 'model:org/model'], ['repair', 'model:org/model'],
    ])
        assert.throws(() => assertCockpitCommand(command), error => {
            assert.ok(error instanceof CommandSurfaceError);
            assert.ok(!error.message.includes('SYNTHETIC_SECRET'));
            return true;
        });
});

test('the invocation drops to the service identity and speaks JSON (CP-03)', () => {
    assert.deepEqual(hfcacheArgv(['status']), [
        'systemd-run', '--quiet', '--wait', '--pipe', '--collect',
        '--property=User=hfcache',
        '--property=Group=hfcache',
        '--property=UMask=0027',
        '--property=MemoryHigh=4G',
        '--',
        '/usr/local/libexec/hfcache-client',
        '--client-config', '/etc/hfcache/client.toml',
        '--api-socket', '/run/hfcache/api/api.sock', '--json',
        'status',
    ]);
});

test('the fixed container launcher owns API credential delivery outside the page (CP-08)', () => {
    const argv = hfcacheArgv(['doctor', '--read-only']);
    assert.ok(argv.includes('/usr/local/libexec/hfcache-client'));
    assert.ok(!argv.some(part => part.includes('Credential')));
    // The protected runtime profile chooses the Podman secret. Neither its
    // source nor container engine arguments enter this browser-facing adapter.
    assert.ok(!argv.some(part => part.includes('token-file')));
    assert.ok(!argv.some(part => part.includes('CREDENTIALS_DIRECTORY')));
    assert.ok(!argv.includes('--config'));
    assert.ok(!argv.some(part => part.includes('HF_HOME') || part.includes('HF_XET_CACHE')));
    assert.ok(!argv.some(part => part.includes('hf-token')));
    assert.ok(!argv.some(part => part.includes('podman') || part.includes('image')));
});

test('a candidate configuration replaces the installed path (contract §6)', () => {
    const argv = hfcacheArgv(['config', 'validate'], { config: '/etc/hfcache/.candidate.toml' });
    assert.ok(argv.includes('/etc/hfcache/.candidate.toml'));
    assert.ok(!argv.includes('/etc/hfcache/config.toml'));
});

test('original keys and client authority pins remain separate global CLI arguments', () => {
    const pin = 'b'.repeat(64);
    const argv = hfcacheArgv(['prune', '--apply'], { idempotencyKey: '~original-key', expectedClientScope: pin });
    assert.deepEqual(argv.slice(-6), ['--idempotency-key', '~original-key', '--expected-client-scope', pin, 'prune', '--apply']);
    assert.ok(argv.includes('--property=User=hfcache'));
    assert.ok(!argv.some(value => value.includes('token')));
    for (const idempotencyKey of ['', 'x;command', 'x\ncommand', 'x'.repeat(129)])
        assert.throws(() => hfcacheArgv(['sync'], { idempotencyKey }), /Invalid original operation key/);
    assert.throws(() => hfcacheArgv(['sync'], { expectedClientScope: 'https://unexpected' }), /Invalid expected client authority/);
});

test('selectors round-trip', () => {
    for (const text of ['model:org/name', 'dataset:org/data.set', `model:org/name@${SHA}`]) {
        assert.equal(formatSelector(parseSelector(text)), text);
    }
});

test('an abbreviated commit SHA is rejected, as HFARG001 would', () => {
    assert.throws(() => parseSelector('model:org/name@0123456'), SelectorError);
    assert.ok(isFullCommitSha(SHA));
    assert.ok(!isFullCommitSha(SHA.toUpperCase()));
});

test('single-segment canonical identifiers are rejected, as HFCFG008 would', () => {
    assert.throws(() => parseSelector('model:gpt2'), SelectorError);
});

test('selector grammar violations are rejected', () => {
    assert.throws(() => parseSelector('weights:org/name'), SelectorError);
    assert.throws(() => parseSelector('model:-org/name'), SelectorError);
    assert.throws(() => parseSelector('model:org/..'), SelectorError);
    assert.throws(() => parseSelector('org/name'), SelectorError);
    assert.throws(() => parseSelector(`model:${'a'.repeat(60)}/${'b'.repeat(60)}`), SelectorError);
});
