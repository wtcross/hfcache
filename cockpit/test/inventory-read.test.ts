/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';

import type { Envelope } from '../src/lib/envelope.ts';
import { parseInventory } from '../src/lib/inventory-read.ts';

const SHA = 'a'.repeat(40);
const PUBLICATION = 'b'.repeat(32);
function repository() {
    return {
        repository_id: 'example/model',
        repository_type: 'model',
        managed: true,
        enabled: true,
        current_commit_sha: SHA,
        current_publication_id: PUBLICATION,
        retained_revisions: 1,
        revisions: [{
            commit_sha: SHA,
            publication_id: PUBLICATION,
            publication_generation: 1,
            file_count: 2,
            total_bytes: 2048,
            published_at: '2026-10-19T12:00:00.123456Z',
            verification_state: 'unverified'
        }],
    };
}
function envelope(data: unknown = { repositories: [repository()] }, failed = false): Envelope {
    return {
        schema_version: 1,
        command: 'list',
        run_id: 'c'.repeat(32),
        started_at: '2026-10-19T12:00:00Z',
        completed_at: '2026-10-19T12:00:00Z',
        exit_code: failed ? 40 : 0,
        outcome: failed ? 'failed' : 'success',
        data,
        warnings: [],
        errors: failed ? [{ code: 'HFVER008', message: 'Original refusal', repository: null }] : [],
    };
}

test('complete joined inventory retains managed and nullable unmanaged revision identities', () => {
    const unmanaged = { ...repository(), repository_id: 'example/unmanaged', managed: false, enabled: null };
    const source = envelope({ repositories: [repository(), unmanaged] });
    const parsed = parseInventory(source);
    assert.equal(parsed.error, null);
    assert.equal(parsed.partial, false);
    assert.deepEqual(parsed.payload, source.data);
    assert.equal(parsed.payload?.repositories[1].enabled, null);
    assert.ok(Object.isFrozen(parsed.payload?.repositories));
    assert.ok(Object.isFrozen(parsed.payload?.repositories[0].revisions));
});

test('only a valid successful empty inventory establishes known empty', () => {
    const empty = parseInventory(envelope({ repositories: [] }));
    assert.deepEqual(empty.payload, { repositories: [] });
    assert.equal(empty.partial, false);
    const unavailable = parseInventory(envelope({}, true));
    assert.equal(unavailable.payload, null);
    assert.equal(unavailable.error, null);
    const malformed = parseInventory(envelope({}));
    assert.equal(malformed.payload, null);
    assert.equal(malformed.error?.reason, 'invalid-envelope');
});

test('valid failed inventory is informational and preserves the exact original Envelope', () => {
    const source = envelope({ repositories: [repository()] }, true);
    const before = structuredClone(source);
    const parsed = parseInventory(source);
    assert.equal(parsed.error, null);
    assert.equal(parsed.partial, true);
    assert.deepEqual(parsed.payload, { repositories: [repository()] });
    assert.deepEqual(source, before);
    const empty = parseInventory(envelope({ repositories: [] }, true));
    assert.equal(empty.partial, true);
    assert.deepEqual(empty.payload?.repositories, []);
});

test('malformed success inventory cannot become an empty array or a usable row', () => {
    for (const data of [null, [], { repositories: {} }, { repositories: null },
        { repositories: [null] }, { repositories: [{}] }, { repositories: [], extra: true }]) {
        const parsed = parseInventory(envelope(data));
        assert.equal(parsed.payload, null);
        assert.equal(parsed.error?.stage, 'api-read');
        assert.equal(parsed.error?.reason, 'invalid-envelope');
        assert.equal(parsed.error?.hostMutationUncertain, false);
    }
});

test('nested revision corruption refuses the entire purported successful inventory', () => {
    for (const replacement of [
        { commit_sha: '../invalid' }, { publication_id: 'x' }, { publication_generation: 0 },
        { file_count: -1 }, { total_bytes: Number.MAX_SAFE_INTEGER + 1 }, { total_bytes: '2048' },
        { verification_state: 'healthy' }, { published_at: '2026-02-30T12:00:00Z' },
        { published_at: '2026-10-19T12:00:00+00:00' }, { extra: true },
    ]) {
        const row = repository();
        const changed = { ...row, revisions: [{ ...row.revisions[0], ...replacement }] };
        assert.equal(parseInventory(envelope({ repositories: [changed] })).payload, null);
    }
});

test('repository enabled state and canonical identity remain exact rather than filtered away', () => {
    for (const replacement of [
        { repository_id: '../etc/shadow' }, { repository_id: 'example/model@' + SHA },
        { repository_type: 'other' }, { managed: 'true' }, { enabled: null },
        { managed: false, enabled: false }, { enabled: 'yes' }, { retained_revisions: 2 },
        { current_publication_id: null }, { current_commit_sha: null },
        { current_publication_id: 'd'.repeat(32) }, { extra: true },
    ]) {
        assert.equal(parseInventory(envelope({ repositories: [{ ...repository(), ...replacement }] })).payload, null);
    }
    const noCurrent = { ...repository(), current_commit_sha: null, current_publication_id: null };
    assert.equal(parseInventory(envelope({ repositories: [noCurrent] })).error, null);
});

test('duplicate repositories or duplicate/inconsistent revisions cannot render ambiguous identities', () => {
    assert.equal(parseInventory(envelope({ repositories: [repository(), repository()] })).payload, null);
    const row = repository();
    const second = { ...row.revisions[0], commit_sha: 'd'.repeat(40), publication_id: 'e'.repeat(32), publication_generation: 2 };
    const valid = { ...row, retained_revisions: 2, revisions: [...row.revisions, second] };
    assert.equal(parseInventory(envelope({ repositories: [valid] })).error, null);
    for (const revisions of [
        [second, row.revisions[0]], [row.revisions[0], row.revisions[0]],
        [row.revisions[0], { ...second, publication_id: PUBLICATION }],
        [row.revisions[0], { ...second, publication_generation: 1 }],
        [row.revisions[0], { ...second, commit_sha: SHA }],
    ]) assert.equal(parseInventory(envelope({ repositories: [{ ...valid, revisions }] })).payload, null);
});

test('wrong success command and malformed failed partial data stay separate from the original code', () => {
    assert.equal(parseInventory({ ...envelope(), command: 'status' }).payload, null);
    const failure = envelope({ repositories: [{}] }, true);
    const parsed = parseInventory(failure);
    assert.equal(parsed.payload, null);
    assert.equal(parsed.error?.reason, 'invalid-envelope');
    assert.equal(failure.errors[0].code, 'HFVER008');
    assert.equal(failure.exit_code, 40);
});

test('unknown failed payload fields or command cannot pass as a recognized partial inventory', () => {
    for (const source of [
        envelope({ unrelated: 'withheld' }, true),
        envelope({ repositories: [repository()], unrelated: 'withheld' }, true),
        { ...envelope({}, true), command: 'status' },
    ]) {
        const parsed = parseInventory(source);
        assert.equal(parsed.payload, null);
        assert.equal(parsed.error?.reason, 'invalid-envelope');
        assert.equal(source.errors[0].code, 'HFVER008');
    }
});
