/* SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The worked example in docs/configuration.md §10 is the fixture: the form
 * model must read the document the contract shows, and a canonical
 * serialization must round-trip it.
 */

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

import {
    extractFieldPath, GLOBAL_FIELDS, getField, parseConfig, repositorySelectors,
    selectorsNeedingPreview, serializeConfig, setField, validateRevisionReference,
} from '../src/lib/config.ts';

function workedExample(): string {
    const contract = readFileSync(new URL('../../docs/configuration.md', import.meta.url), 'utf8');
    const match = /```toml\n(# \/etc\/hfcache\/config\.toml[\s\S]*?)```/.exec(contract);
    assert.ok(match, 'docs/configuration.md §10 worked example not found');
    return match[1];
}

test('the contract worked example parses into the form model', () => {
    const document = parseConfig(workedExample());
    assert.equal(document.schema_version, 1);
    assert.equal(document.repositories?.length, 2);
    assert.equal(document.repositories?.[0].type, 'model');
    assert.deepEqual(repositorySelectors(document),
                     ['model:organization/model-name', 'dataset:organization/dataset-name']);
    const endpoint = GLOBAL_FIELDS.find(field => field.table === 'hub' && field.key === 'endpoint');
    assert.ok(endpoint);
    assert.equal(getField(document, endpoint), 'https://huggingface.co');
    const tokenMode = GLOBAL_FIELDS.find(field => field.table === 'hub' && field.key === 'token_mode');
    assert.deepEqual(tokenMode?.options, ['disabled', 'optional', 'required']);
});

test('serialization round-trips the document, comments aside', () => {
    const document = parseConfig(workedExample());
    const rewritten = serializeConfig(document, new Date('2026-07-30T00:00:00Z'));
    assert.ok(rewritten.startsWith('# /etc/hfcache/config.toml — written by the hfcache Cockpit plugin'));
    assert.deepEqual(parseConfig(rewritten), document);
});

test('every global field the contract defines reads from the worked example', () => {
    const document = parseConfig(workedExample());
    assert.equal(GLOBAL_FIELDS.length, 19);
    for (const field of GLOBAL_FIELDS)
        assert.notEqual(getField(document, field), undefined, `${field.table}.${field.key}`);
});

test('setField copies rather than mutating', () => {
    const document = parseConfig(workedExample());
    const spec = GLOBAL_FIELDS.find(field => field.key === 'max_workers');
    assert.ok(spec);
    const changed = setField(document, spec, 8);
    assert.equal(getField(changed, spec), 8);
    assert.equal(getField(document, spec), 4);
});

test('the reference-name grammar matches configuration.md §6', () => {
    assert.equal(validateRevisionReference('main'), null);
    assert.equal(validateRevisionReference('refs/pr/1'.replace('refs/', 'pr-')), null);
    assert.equal(validateRevisionReference('0123456789abcdef0123456789abcdef01234567'), null);
    for (const bad of ['', '/x', 'x/', 'a//b', 'a..b', '-x', 'x.lock', 'a'.repeat(256), 'abc123f']) {
        assert.notEqual(validateRevisionReference(bad), null, bad);
    }
});

test('the sizing preview covers added and retargeted enabled repositories', () => {
    const installed = parseConfig(workedExample());
    const candidate = parseConfig(workedExample());
    candidate.repositories = [
        ...(candidate.repositories ?? []),
        { id: 'org/new', type: 'model', revision: 'main', enabled: true, declared_dependencies: [] },
        { id: 'org/off', type: 'model', revision: 'main', enabled: false, declared_dependencies: [] },
    ];
    candidate.repositories[0] = { ...candidate.repositories[0], revision: 'v2' };
    assert.deepEqual(selectorsNeedingPreview(installed, candidate),
                     ['model:organization/model-name', 'model:org/new']);
});

test('validation issues map back to fields best-effort', () => {
    assert.equal(extractFieldPath({ message: 'HFCFG005 [sync.max_workers]: not an integer' }),
                 'sync.max_workers');
    assert.equal(extractFieldPath({ message: 'no path here', context: { key: 'hub.endpoint' } }),
                 'hub.endpoint');
    assert.equal(extractFieldPath({ message: 'nothing at all' }), null);
});
