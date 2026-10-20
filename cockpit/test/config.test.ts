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
    configuredTagSuggestions, extractFieldPath, GLOBAL_FIELDS, getField, normalizeTags, parseConfig, repositorySelectors,
    selectorsNeedingPreview, serializeConfig, setField, tagInput, validateRevisionReference,
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

test('retention defaults to numeric three and preserves an explicit five (RET-010)', () => {
    const spec = GLOBAL_FIELDS.find(field => field.table === 'storage' && field.key === 'maximum_revisions');
    assert.ok(spec);
    assert.equal(spec.kind, 'int');
    assert.deepEqual(spec.options, [3, 5]);
    assert.equal(getField(parseConfig(workedExample()), spec), 3);
    const omitted = parseConfig('schema_version = 1\n[storage]\n');
    assert.equal(getField(omitted, spec), 3);
    const explicitFive = setField(omitted, spec, 5);
    const roundTrip = parseConfig(serializeConfig(explicitFive, new Date('2026-09-14T00:00:00Z')));
    assert.equal(getField(roundTrip, spec), 5);
    assert.equal(getField(omitted, spec), 3);
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

test('sizing follows backend enabled and revision defaults without changing verbatim intent', () => {
    const implicit = parseConfig('[[repositories]]\nid="org/model"\ntype="model"\n');
    const explicit = parseConfig('[[repositories]]\nid="org/model"\ntype="model"\nenabled=true\nrevision="main"\n');
    assert.deepEqual(selectorsNeedingPreview({}, implicit), ['model:org/model']);
    assert.deepEqual(selectorsNeedingPreview(explicit, implicit), []);
    assert.deepEqual(selectorsNeedingPreview(implicit, explicit), []);
    const retargeted = parseConfig('[[repositories]]\nid="org/model"\ntype="model"\nrevision="v2"\n');
    assert.deepEqual(selectorsNeedingPreview(implicit, retargeted), ['model:org/model']);
    const disabled = parseConfig('[[repositories]]\nid="org/model"\ntype="model"\nenabled=false\n');
    assert.deepEqual(selectorsNeedingPreview(disabled, implicit), ['model:org/model']);
    assert.deepEqual(selectorsNeedingPreview(implicit, disabled), []);
    assert.equal(implicit.repositories?.[0]?.enabled, undefined);
    assert.equal(implicit.repositories?.[0]?.revision, undefined);
});

test('validation issues map back to fields best-effort', () => {
    assert.equal(extractFieldPath({ message: 'HFCFG005 [sync.max_workers]: not an integer' }),
                 'sync.max_workers');
    assert.equal(extractFieldPath({ message: 'no path here', context: { key: 'hub.endpoint' } }),
                 'hub.endpoint');
    assert.equal(extractFieldPath({ message: 'nothing at all' }), null);
});

const tagCases = JSON.parse(readFileSync(new URL('../../tests/fixtures/tags.json', import.meta.url), 'utf8'));
for (const { input, expected } of tagCases.valid) {
    test('tag normalization agrees with shared backend golden', () => {
        assert.deepEqual(normalizeTags(input), expected);
        assert.deepEqual(normalizeTags(normalizeTags(input)), expected);
    });
}
for (const input of [...tagCases.invalid, ['a'.repeat(65)], [' '.repeat(128) + 'a'], Array(65).fill('a')]) {
    test('invalid tag grammar refuses without echoing the input', () => {
        assert.throws(() => normalizeTags(input), /[Tt]ag/);
    });
}

test('tag forms, toggles, add/remove and text serialization preserve canonical labels', () => {
    const document = parseConfig(workedExample());
    const original = JSON.stringify(document);
    document.repositories = [...(document.repositories ?? []), {
        id: 'org/tagged',
        type: 'model',
        revision: 'main',
        enabled: true,
        tags: tagInput(' Coding, coding ,project:Assistant'),
        declared_dependencies: [],
    }];
    const before = JSON.stringify(document);
    const text = serializeConfig(document, new Date('2026-10-19T00:00:00Z'));
    assert.equal(JSON.stringify(document), before, 'serialize must not mutate the draft');
    const form = parseConfig(text);
    assert.deepEqual(form.repositories?.[2].tags, ['coding', 'project:assistant']);
    assert.deepEqual(configuredTagSuggestions(form), ['coding', 'project:assistant']);
    assert.deepEqual(normalizeTags(Array(64).fill('a')), ['a']);
    assert.deepEqual(tagInput(''), []);
    assert.ok(form.repositories);
    form.repositories[2] = { ...form.repositories[2], enabled: false };
    const disabled = parseConfig(serializeConfig(form, new Date()));
    assert.deepEqual(disabled.repositories?.[2].tags, ['coding', 'project:assistant']);
    assert.deepEqual(selectorsNeedingPreview(form, disabled), []);
    form.repositories = form.repositories.slice(0, 2);
    assert.equal(JSON.stringify(form), original);
});

test('existing tags are suggestions for an invalid draft, with no registry or silent repair', () => {
    const document = parseConfig('[[repositories]]\nid="org/a"\ntype="dataset"\ntags=["Z", "a"]');
    assert.deepEqual(document.repositories?.[0].tags, ['a', 'z']);
    assert.ok(document.repositories);
    document.repositories.push({
        id: 'org/b',
        type: 'model',
        revision: 'main',
        enabled: false,
        tags: ['bad tag'],
        declared_dependencies: []
    });
    assert.deepEqual(configuredTagSuggestions(document), ['a', 'z']);
    assert.throws(() => serializeConfig(document, new Date()), /tag/);
});

test('script, shell, URL and terminal fragments cannot become browser tag labels', () => {
    for (const hostile of ['<img src=x onerror=alert(1)>', '$(touch PWN)', 'https://example.invalid/?token=x', '\u001b[2J', 'ignore previous instructions']) {
        assert.throws(() => normalizeTags([hostile]), (error: unknown) => {
            assert.ok(error instanceof Error);
            assert.ok(!error.message.includes(hostile));
            return true;
        });
    }
});
