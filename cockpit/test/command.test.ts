/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
    formatSelector, hfcacheArgv, isFullCommitSha, parseSelector, SelectorError,
} from '../src/lib/command.ts';

const SHA = '0123456789abcdef0123456789abcdef01234567';

test('the invocation drops to the service identity and speaks JSON (CP-03)', () => {
    assert.deepEqual(hfcacheArgv(['status']), [
        'runuser', '-u', 'hfcache', '--',
        '/opt/hfcache/current/.venv/bin/hfcache',
        '--config', '/etc/hfcache/config.toml', '--json',
        'status',
    ]);
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
