/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
    formatSelector, hfcacheArgv, isFullCommitSha, parseSelector, SelectorError,
} from '../src/lib/command.ts';

const SHA = '0123456789abcdef0123456789abcdef01234567';

test('the invocation drops to the service identity and speaks JSON (CP-03)', () => {
    assert.deepEqual(hfcacheArgv(['status']), [
        'systemd-run', '--quiet', '--wait', '--pipe', '--collect',
        '--property=User=hfcache',
        '--property=Group=hfcache',
        '--property=ImportCredential=hfcache.api',
        '--property=UMask=0027',
        '--property=MemoryHigh=4G',
        '--',
        '/opt/hfcache/current/.venv/bin/hfcache',
        '--client-config', '/etc/hfcache/client.toml',
        '--api-socket', '/run/hfcache/api.sock', '--json',
        'status',
    ]);
});

test('the credential is imported by systemd, never read by the page (CP-08)', () => {
    const argv = hfcacheArgv(['doctor', '--read-only']);
    assert.ok(argv.includes('--property=ImportCredential=hfcache.api'));
    // The command line names the credential, not a token file or path the
    // page could read; decryption happens in PID 1 (docs/cockpit.md §2).
    assert.ok(!argv.some(part => part.includes('token-file')));
    assert.ok(!argv.some(part => part.includes('CREDENTIALS_DIRECTORY')));
    assert.ok(!argv.includes('--config'));
    assert.ok(!argv.some(part => part.includes('HF_HOME') || part.includes('HF_XET_CACHE')));
    assert.ok(!argv.some(part => part.includes('hf-token')));
});

test('a candidate configuration replaces the installed path (contract §6)', () => {
    const argv = hfcacheArgv(['config', 'validate'], { config: '/etc/hfcache/.candidate.toml' });
    assert.ok(argv.includes('/etc/hfcache/.candidate.toml'));
    assert.ok(!argv.includes('/etc/hfcache/config.toml'));
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
