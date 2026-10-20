/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
    ACTION_ROUTES, createOperationRegistry, MAX_OPERATION_RECORDS, MAX_OPERATION_STORAGE_BYTES,
    OPERATION_ACTIONS, OPERATION_STORAGE_KEY, OperationRegistryError, sameOperationScope,
    validOperationScope,
} from '../src/lib/operation-registry.ts';
import type { OperationAction, OperationScope, OperationStorage } from '../src/lib/operation-registry.ts';
import type { Envelope } from '../src/lib/envelope.ts';

const SCOPE: OperationScope = {
    host: 'test-host',
    profile: 'a'.repeat(64),
    endpoint: 'unix:/run/hfcache/api/api.sock',
    credentialClass: 'rest-writer',
    archiveId: '12345678-1234-1234-1234-123456789abc',
    instanceId: 'b'.repeat(32),
    authorityFingerprint: 'c'.repeat(64),
};
const ID = 'd'.repeat(32);

class Storage implements OperationStorage {
    value: string | null = null;
    failedRead = false;
    failedWrite = false;
    writes = 0;
    getItem(key: string): string | null {
        assert.equal(key, OPERATION_STORAGE_KEY);
        if (this.failedRead) throw new Error('SYNTHETIC_SECRET');
        return this.value;
    }

    setItem(key: string, value: string): void {
        assert.equal(key, OPERATION_STORAGE_KEY);
        this.writes += 1;
        if (this.failedWrite) throw new Error('SYNTHETIC_SECRET');
        this.value = value;
    }
}

function fixture(storage = new Storage()) {
    let sequence = 0;
    let time = 1000;
    const registry = createOperationRegistry({ storage, keyFactory: () => 'original-' + ++sequence, clock: () => ++time });
    return { storage, registry };
}

function result(command = 'sync', exit = 0, code = 'HFMNT010'): Envelope {
    return {
        schema_version: 1,
        command,
        run_id: 'e'.repeat(32),
        started_at: '2026-10-19T12:00:00.000000Z',
        completed_at: '2026-10-19T12:00:01.000000Z',
        exit_code: exit,
        outcome: exit === 0 ? 'success' : 'failed',
        data: {},
        warnings: [],
        errors: exit === 0 ? [] : [{ code, message: 'classified refusal', repository: null, context: {} }]
    };
}

test('V22 the original key is synchronously persisted before a caller can spawn', () => {
    const { registry, storage } = fixture();
    const prepared = registry.prepare('sync-selected', SCOPE);
    assert.equal(prepared.key, 'original-1');
    const persisted = JSON.parse(storage.value!);
    assert.equal(persisted.records[0].key, prepared.key);
    assert.equal(persisted.records[0].state, 'prepared');
    registry.uncertain(prepared.key);
    assert.equal(registry.snapshot().records[0].key, prepared.key);
    assert.equal(registry.snapshot().records[0].operationId, null);
    assert.throws(() => registry.prepare('sync-selected', SCOPE), OperationRegistryError);
});

test('V24/V25 reload retains original identities and converts prepared to uncertain without resubmission', () => {
    const { registry, storage } = fixture();
    const first = registry.prepare('sync-selected', SCOPE);
    const reloaded = createOperationRegistry({ storage, keyFactory: () => assert.fail('Reload cannot create another key') });
    assert.equal(reloaded.snapshot().records[0].state, 'uncertain');
    assert.equal(reloaded.snapshot().records[0].key, first.key);
    assert.equal(storage.writes, 1);
    registry.identity(first.key, { kind: 'operation', operationId: ID });
    const accepted = createOperationRegistry({ storage });
    assert.equal(accepted.snapshot().records[0].operationId, ID);
    assert.equal(accepted.snapshot().records[0].state, 'accepted');
});

test('V25 saved terminal metadata cannot authorize another submission before original authenticated completion', () => {
    const { registry, storage } = fixture();
    const prepared = registry.prepare('sync-selected', SCOPE);
    registry.identity(prepared.key, { kind: 'operation', operationId: ID });
    const envelope = result();
    const completed = registry.complete(prepared.key, envelope, SCOPE);
    const writes = storage.writes;
    const raw = JSON.parse(storage.value!);
    raw.records[0].terminal = Object.fromEntries(Object.entries(raw.records[0].terminal).reverse());
    storage.value = JSON.stringify(raw);
    const restored = createOperationRegistry({ storage, keyFactory: () => 'replacement-key' });
    const saved = restored.snapshot().records[0];
    assert.equal(restored.hasUnresolved('sync-selected', SCOPE), true);
    assert.throws(() => restored.prepare('sync-selected', SCOPE), OperationRegistryError);
    assert.equal(saved.state, 'unverified');
    assert.deepEqual(saved.terminal, completed.terminal);
    assert.equal(saved.operationId, ID);
    assert.equal(storage.writes, writes);
    assert.equal(restored.canRecover(saved, SCOPE), true);
    assert.equal(restored.canRecover(saved, { ...SCOPE, authorityFingerprint: 'f'.repeat(64) }), false);
    const observing = restored.observing(prepared.key, SCOPE);
    assert.equal(observing.state, 'observing');
    assert.deepEqual(observing.terminal, completed.terminal);
    assert.equal(restored.complete(prepared.key, envelope, SCOPE).state, 'terminal');
    assert.equal(restored.hasUnresolved('sync-selected', SCOPE), false);
    assert.equal(restored.prepare('sync-selected', SCOPE).key, 'replacement-key');
});

test('V25 a valid forged terminal summary remains blocked and cannot replace authentic contradictory evidence', () => {
    const { registry, storage } = fixture();
    const prepared = registry.prepare('sync-selected', SCOPE);
    registry.identity(prepared.key, { kind: 'operation', operationId: ID });
    registry.uncertain(prepared.key);
    const raw = JSON.parse(storage.value!);
    const forged = { command: 'sync', exitCode: 0, outcome: 'success', runId: 'f'.repeat(32), code: null };
    raw.records[0].state = 'terminal';
    raw.records[0].terminal = forged;
    storage.value = JSON.stringify(raw);
    const restored = createOperationRegistry({ storage, keyFactory: () => assert.fail('No replacement key') });
    const saved = restored.snapshot().records[0];
    assert.equal(restored.hasUnresolved('sync-selected', SCOPE), true);
    assert.throws(() => restored.prepare('sync-selected', SCOPE), OperationRegistryError);
    assert.equal(saved.state, 'unverified');
    assert.equal(saved.key, prepared.key);
    assert.equal(saved.operationId, ID);
    assert.deepEqual(saved.terminal, forged);
    const conflict = restored.complete(prepared.key, result(), SCOPE);
    assert.equal(conflict.state, 'conflict');
    assert.equal(conflict.key, prepared.key);
    assert.equal(conflict.operationId, ID);
    assert.deepEqual(conflict.terminal, forged);
    assert.equal(restored.hasUnresolved('sync-selected', SCOPE), true);
});

test('V25 missing history retains unverified terminal metadata across observation and another reload', () => {
    const { registry, storage } = fixture();
    const prepared = registry.prepare('sync-selected', SCOPE);
    registry.identity(prepared.key, { kind: 'operation', operationId: ID });
    const envelope = result();
    const original = registry.complete(prepared.key, envelope, SCOPE);
    let restored = createOperationRegistry({ storage });
    for (const state of ['missing', 'unavailable'] as const) {
        restored.observing(prepared.key, SCOPE);
        const unknown = restored.lookupState(prepared.key, state);
        assert.equal(unknown.state, state);
        assert.deepEqual(unknown.terminal, original.terminal);
        restored = createOperationRegistry({ storage });
        assert.equal(restored.snapshot().storage, 'ready');
        assert.equal(restored.snapshot().records[0].state, state);
        assert.equal(restored.hasUnresolved('sync-selected', SCOPE), true);
        assert.throws(() => restored.prepare('sync-selected', SCOPE), OperationRegistryError);
    }
    const failedLookup = result('sync', 20, 'HFAPI013');
    failedLookup.data = { idempotency_key: prepared.key, operation_id: ID, work_may_continue: true };
    assert.equal(restored.complete(prepared.key, failedLookup, SCOPE).state, 'missing');
    assert.deepEqual(restored.snapshot().records[0].terminal, original.terminal);
    assert.equal(restored.hasUnresolved('sync-selected', SCOPE), true);
    assert.equal(restored.complete(prepared.key, envelope, SCOPE).state, 'terminal');
});

test('V24 registry snapshots are stable, immutable and independent of subscribers', () => {
    const { registry } = fixture();
    const initial = registry.snapshot();
    assert.equal(registry.snapshot(), initial);
    let notices = 0;
    const dispose = registry.subscribe(() => { notices += 1 });
    registry.subscribe(() => { throw new Error('detached view') });
    const prepared = registry.prepare('sync-selected', SCOPE);
    assert.equal(notices, 1);
    const snapshot = registry.snapshot();
    assert.notEqual(snapshot, initial);
    assert.ok(Object.isFrozen(snapshot) && Object.isFrozen(snapshot.records));
    assert.ok(Object.isFrozen(prepared) && Object.isFrozen(prepared.scope));
    dispose();
    registry.identity(prepared.key, { kind: 'operation', operationId: ID });
    assert.equal(notices, 1);
    assert.equal(initial.records.length, 0);
});

for (const when of ['read', 'write', 'absent'] as const) {
    test(`V23 storage ${when} failure refuses submission without exposing arbitrary errors`, () => {
        const storage = new Storage();
        storage.failedRead = when === 'read';
        storage.failedWrite = when === 'write';
        const registry = createOperationRegistry({
            storage: when === 'absent' ? null : storage,
            keyFactory: () => 'safe-key'
        });
        assert.throws(() => registry.prepare('plan', SCOPE), OperationRegistryError);
        assert.equal(registry.snapshot().storage, 'unavailable');
        assert.ok(!JSON.stringify(registry.snapshot()).includes('SYNTHETIC_SECRET'));
        if (when === 'write') assert.equal(registry.snapshot().records[0].key, 'safe-key');
    });
}

test('V23 post-admission persistence failure retains the learned ID in memory and blocks new work', () => {
    const { registry, storage } = fixture();
    const prepared = registry.prepare('sync-selected', SCOPE);
    storage.failedWrite = true;
    registry.identity(prepared.key, { kind: 'operation', operationId: ID });
    assert.equal(registry.snapshot().records[0].operationId, ID);
    assert.equal(registry.snapshot().storage, 'unavailable');
    assert.throws(() => registry.prepare('doctor', SCOPE), OperationRegistryError);
    assert.ok(!JSON.stringify(registry.snapshot()).includes('SYNTHETIC_SECRET'));
});

test('V25 storage changed after startup is preserved rather than overwritten by new observation', () => {
    const { registry, storage } = fixture();
    const prepared = registry.prepare('sync-selected', SCOPE);
    storage.value = '{"unrecognized":"SYNTHETIC_SECRET"}';
    registry.identity(prepared.key, { kind: 'operation', operationId: ID });
    assert.equal(registry.snapshot().storage, 'corrupt');
    assert.equal(registry.snapshot().records[0].operationId, ID);
    assert.equal(storage.value, '{"unrecognized":"SYNTHETIC_SECRET"}');
    assert.throws(() => registry.prepare('doctor', SCOPE), OperationRegistryError);
    assert.ok(!JSON.stringify(registry.snapshot()).includes('SYNTHETIC_SECRET'));
});

for (const saved of ['not JSON', '{}', '{"schemaVersion":2,"records":[]}',
    '{"schemaVersion":1,"records":[],"token":"SYNTHETIC_SECRET"}', 'x'.repeat(MAX_OPERATION_STORAGE_BYTES + 1)]) {
    test('V25 corrupt or oversized recovery storage is preserved and cannot authorize submission', () => {
        const storage = new Storage();
        storage.value = saved;
        const { registry } = fixture(storage);
        assert.equal(registry.snapshot().storage, 'corrupt');
        assert.throws(() => registry.prepare('plan', SCOPE), OperationRegistryError);
        assert.equal(storage.value, saved);
        assert.equal(storage.writes, 0);
        assert.ok(!JSON.stringify(registry.snapshot()).includes('SYNTHETIC_SECRET'));
    });
}

test('V25 injected fields, duplicate keys and forged terminal records fail closed without erasure', () => {
    const { registry, storage } = fixture();
    registry.prepare('plan', SCOPE);
    const saved = JSON.parse(storage.value!);
    for (const mutate of [
        (value: typeof saved) => { value.records[0].argv = ['SYNTHETIC_SECRET'] },
        (value: typeof saved) => { value.records[0].scope.token = 'SYNTHETIC_SECRET' },
        (value: typeof saved) => { value.records.push(value.records[0]) },
        (value: typeof saved) => { value.records[0].route = '/arbitrary' },
        (value: typeof saved) => { value.records[0].state = 'terminal'; value.records[0].terminal = {} },
    ]) {
        const changed = JSON.parse(JSON.stringify(saved));
        mutate(changed);
        storage.value = JSON.stringify(changed);
        const before = storage.value;
        const restored = createOperationRegistry({ storage });
        assert.equal(restored.snapshot().storage, 'corrupt');
        assert.equal(storage.value, before);
    }
});

test('V26 scope drift preserves old work and blocks a new key for that action on the same host', () => {
    const { registry } = fixture();
    const prepared = registry.prepare('sync-selected', SCOPE);
    for (const drift of [
        { profile: 'f'.repeat(64) }, { endpoint: 'unix:/run/other/api.sock' },
        { credentialClass: 'rest-reader' as const }, { archiveId: null },
        { archiveId: 'abcdefab-1234-1234-1234-123456789abc' }, { authorityFingerprint: 'f'.repeat(64) },
    ]) {
        const current = { ...SCOPE, ...drift };
        assert.equal(registry.canRecover(prepared, current), false);
        assert.equal(registry.hasUnresolved('sync-selected', current), true);
        assert.throws(() => registry.observing(prepared.key, current), OperationRegistryError);
        assert.throws(() => registry.prepare('sync-selected', current), OperationRegistryError);
    }
    const another = { ...SCOPE, host: 'different-trusted-host' };
    assert.equal(registry.hasUnresolved('sync-selected', another), false);
    assert.ok(registry.prepare('sync-selected', another));
    assert.equal(registry.snapshot().records[0].key, prepared.key);
});

test('V26 instance restart with identical confirmed archive authority permits original observation', () => {
    const { registry } = fixture();
    const prepared = registry.prepare('sync-selected', SCOPE);
    const restarted = { ...SCOPE, instanceId: 'f'.repeat(32) };
    assert.equal(sameOperationScope(SCOPE, restarted), true);
    assert.equal(registry.observing(prepared.key, restarted).state, 'observing');
});

test('V26 unknown archive scope never silently binds to a later UUID or creates a new submission', () => {
    const { registry, storage } = fixture();
    const prepared = registry.prepare('plan', SCOPE);
    const saved = JSON.parse(storage.value!);
    saved.records[0].scope.archiveId = null;
    storage.value = JSON.stringify(saved);
    const restored = createOperationRegistry({ storage });
    const historical = restored.snapshot().records[0];
    assert.equal(restored.canRecover(historical, SCOPE), false);
    assert.equal(restored.hasUnresolved('plan', SCOPE), true);
    assert.throws(() => restored.complete(prepared.key, result('plan', 10), SCOPE), OperationRegistryError);
    assert.throws(() => registry.prepare('doctor', { ...SCOPE, archiveId: null }), OperationRegistryError);
    assert.equal(restored.snapshot().records[0].scope.archiveId, null);
});

for (const endpoint of ['unix:/run/hfcache/api.sock', 'https://service.example/api',
    'http://localhost:8080', 'http://127.0.0.1:8080', 'http://[::1]:8080']) {
    test(`V26 trusted supported endpoint syntax ${endpoint} is retained as scope data`, () => {
        assert.equal(validOperationScope({ ...SCOPE, endpoint }), true);
    });
}

for (const endpoint of ['file:/etc/secret', 'unix:/run/../secret', 'unix:/run//socket', 'http://remote.example',
    'https://user:secret@example.test', 'https://example.test?a=secret', 'https://example.test#secret',
    'https://example.test/\nsecret', 'https:example.test', 'https://example.test?', 'https://example.test#',
    'https://example.test\\path']) {
    test('V26 unsafe scope endpoint cannot become recovery authority', () => {
        assert.equal(validOperationScope({ ...SCOPE, endpoint }), false);
    });
}

test('V27 unresolved Apply remains blocked while successful dry-run summary remains preserved', () => {
    const { registry } = fixture();
    const dry = registry.prepare('prune-dry-run', SCOPE);
    registry.identity(dry.key, { kind: 'operation', operationId: ID });
    registry.complete(dry.key, result('prune --dry-run'), SCOPE);
    const apply = registry.prepare('prune-apply', SCOPE);
    registry.uncertain(apply.key);
    assert.equal(registry.hasUnresolved('prune-apply', SCOPE), true);
    assert.throws(() => registry.prepare('prune-apply', SCOPE), OperationRegistryError);
    assert.equal(registry.snapshot().records[0].terminal?.command, 'prune --dry-run');
    assert.equal(registry.snapshot().records[1].key, apply.key);
});

test('V28 every allowed keyed action has a fixed route and synchronous persisted key', () => {
    const { registry, storage } = fixture();
    for (const action of OPERATION_ACTIONS) {
        const prepared = registry.prepare(action, SCOPE);
        assert.equal(prepared.route, ACTION_ROUTES[action]);
        assert.ok(JSON.parse(storage.value!).records.some((record: { key: string }) => record.key === prepared.key));
    }
    assert.throws(() => registry.prepare('arbitrary' as OperationAction, SCOPE), OperationRegistryError);
});

for (const code of ['HFAPI013', 'HFAPI015', 'HFAPI018', 'HFAPI019', 'HFAPI020']) {
    test(`V29/V30 ${code} is uncertainty and never permission for another submission`, () => {
        const { registry } = fixture();
        const prepared = registry.prepare('sync-selected', SCOPE);
        const failed = result('sync', 20, code);
        failed.data = { idempotency_key: prepared.key, operation_id: ID, work_may_continue: true };
        const retained = registry.complete(prepared.key, failed, SCOPE);
        assert.equal(retained.operationId, ID);
        assert.equal(retained.terminal, null);
        assert.notEqual(retained.state, 'terminal');
        assert.throws(() => registry.prepare('sync-selected', SCOPE), OperationRegistryError);
    });
}

test('V30 missing/unavailable lookup preserves identity and does not create a replacement key', () => {
    const { registry } = fixture();
    const prepared = registry.prepare('sync-selected', SCOPE);
    registry.identity(prepared.key, { kind: 'operation', operationId: ID });
    for (const state of ['missing', 'unavailable'] as const) {
        const retained = registry.lookupState(prepared.key, state);
        assert.equal(retained.state, state);
        assert.equal(retained.operationId, ID);
        assert.equal(retained.key, prepared.key);
    }
    assert.equal(registry.snapshot().records.length, 1);
});

for (const exit of [0, 10, 20, 30, 40, 50]) {
    test(`V31 authentic terminal exit ${exit} keeps its safe exact classification`, () => {
        const { registry, storage } = fixture();
        const prepared = registry.prepare('sync-selected', SCOPE);
        registry.identity(prepared.key, { kind: 'operation', operationId: ID });
        const envelope = result('sync', exit);
        envelope.data = { ignored: 'SYNTHETIC_SECRET' };
        const completed = registry.complete(prepared.key, envelope, SCOPE);
        assert.equal(completed.state, 'terminal');
        assert.equal(completed.terminal?.exitCode, exit);
        assert.equal(completed.terminal?.outcome, envelope.outcome);
        assert.equal(completed.terminal?.runId, envelope.run_id);
        assert.ok(!storage.value!.includes('SYNTHETIC_SECRET'));
    });
}

test('V31 success without an original accepted operation ID cannot resolve a submitted job', () => {
    const { registry } = fixture();
    const prepared = registry.prepare('sync-selected', SCOPE);
    assert.equal(registry.complete(prepared.key, result(), SCOPE).state, 'conflict');
    assert.equal(registry.snapshot().records[0].terminal, null);
});

test('V32 conflicting key/ID never overwrites original handles or prior terminal evidence', () => {
    for (const terminal of [false, true]) {
        const { registry } = fixture();
        const prepared = registry.prepare('sync-selected', SCOPE);
        registry.identity(prepared.key, { kind: 'operation', operationId: ID });
        if (terminal) registry.complete(prepared.key, result(), SCOPE);
        registry.identity(prepared.key, { kind: 'key', key: 'different-key' });
        registry.identity(prepared.key, { kind: 'operation', operationId: 'f'.repeat(32) });
        const conflicted = registry.snapshot().records[0];
        assert.equal(conflicted.key, prepared.key);
        assert.equal(conflicted.operationId, ID);
        assert.equal(conflicted.state, 'conflict');
        assert.equal(conflicted.terminal?.runId ?? null, terminal ? 'e'.repeat(32) : null);
        assert.equal(registry.canRecover(conflicted, SCOPE), false);
    }
});

test('V32 terminal identity conflict retains original domain result identity rather than replacing it', () => {
    const { registry } = fixture();
    const prepared = registry.prepare('sync-selected', SCOPE);
    registry.identity(prepared.key, { kind: 'operation', operationId: ID });
    const wrong = result();
    wrong.data = { idempotency_key: prepared.key, operation_id: 'f'.repeat(32) };
    assert.equal(registry.complete(prepared.key, wrong, SCOPE).state, 'conflict');
    assert.equal(registry.snapshot().records[0].operationId, ID);
});

test('V32 already observed identity conflict remains an identity conflict when terminal evidence arrives', () => {
    for (const terminal of [false, true]) {
        const { registry, storage } = fixture();
        const prepared = registry.prepare('sync-selected', SCOPE);
        registry.identity(prepared.key, { kind: 'operation', operationId: ID });
        if (terminal) registry.complete(prepared.key, result(), SCOPE);
        const conflicted = registry.identity(prepared.key, { kind: 'operation', operationId: 'f'.repeat(32) });
        const writes = storage.writes;
        const incoming = result('sync', 10, 'HFAPI003');
        incoming.data = { idempotency_key: prepared.key, operation_id: 'f'.repeat(32) };
        const retained = registry.complete(prepared.key, incoming, SCOPE);
        assert.equal(retained, conflicted);
        assert.equal(retained.state, 'conflict');
        assert.equal(retained.operationId, ID);
        assert.equal(retained.terminal?.runId ?? null, terminal ? 'e'.repeat(32) : null);
        assert.equal(retained.terminal?.exitCode ?? null, terminal ? 0 : null);
        assert.equal(storage.writes, writes);
        assert.equal(registry.canRecover(retained, SCOPE), false);
        const changedScope = { ...SCOPE, authorityFingerprint: 'f'.repeat(64) };
        assert.throws(() => registry.complete(prepared.key, incoming, changedScope),
                      (error: unknown) => error instanceof OperationRegistryError && error.reason === 'scope');
        assert.equal(registry.snapshot().records[0], conflicted);
    }
});

test('V32 a late new ID cannot erase an already terminal admission refusal', () => {
    const { registry } = fixture();
    const prepared = registry.prepare('sync-selected', SCOPE);
    const refused = registry.complete(prepared.key, result('sync', 10, 'HFAPI003'), SCOPE);
    assert.equal(refused.state, 'terminal');
    assert.equal(refused.operationId, null);
    const contradictory = registry.identity(prepared.key, { kind: 'operation', operationId: ID });
    assert.equal(contradictory.state, 'conflict');
    assert.equal(contradictory.operationId, null);
    assert.deepEqual(contradictory.terminal, refused.terminal);
    assert.equal(registry.hasUnresolved('sync-selected', SCOPE), true);
});

test('V33 safe leading-option keys remain inert stored data', () => {
    for (const key of ['-starts-option', '~starts-tilde']) {
        const registry = createOperationRegistry({ storage: new Storage(), keyFactory: () => key });
        assert.equal(registry.prepare('plan', SCOPE).key, key);
    }
    const registry = createOperationRegistry({ storage: new Storage(), keyFactory: () => "key'; secret" });
    assert.throws(() => registry.prepare('plan', SCOPE), OperationRegistryError);
});

test('V23/V25 count capacity never evicts unresolved records', () => {
    const { registry, storage } = fixture();
    for (let index = 0; index < MAX_OPERATION_RECORDS; index += 1)
        registry.prepare('sync-selected', { ...SCOPE, host: 'host-' + index });
    const before = storage.value;
    assert.throws(() => registry.prepare('doctor', SCOPE), OperationRegistryError);
    assert.equal(registry.snapshot().records.length, MAX_OPERATION_RECORDS);
    assert.equal(registry.snapshot().records[0].key, 'original-1');
    assert.equal(registry.snapshot().storage, 'full');
    assert.equal(storage.value, before);
});

test('V23/V25 capacity evicts only the oldest resolved summary when a new submission needs room', () => {
    const { registry } = fixture();
    const first = registry.prepare('sync-selected', SCOPE);
    registry.complete(first.key, result('sync', 10), SCOPE);
    for (let index = 1; index < MAX_OPERATION_RECORDS; index += 1)
        registry.prepare('sync-selected', { ...SCOPE, host: 'host-' + index });
    assert.equal(registry.snapshot().records.length, MAX_OPERATION_RECORDS);
    assert.equal(registry.snapshot().records[0].key, first.key);
    registry.prepare('doctor', SCOPE);
    assert.equal(registry.snapshot().records.length, MAX_OPERATION_RECORDS);
    assert.ok(!registry.snapshot().records.some(record => record.key === first.key));
    assert.equal(registry.snapshot().records[0].key, 'original-2');
});

test('V23 byte capacity reserves terminal/ID growth and preserves every unresolved record', () => {
    const { registry, storage } = fixture();
    let accepted = 0;
    for (let index = 0; index < MAX_OPERATION_RECORDS; index += 1) {
        try {
            registry.prepare('sync-selected', {
                ...SCOPE,
                host: 'host-' + index,
                endpoint: 'https://example.test/' + 'a'.repeat(1900)
            });
            accepted += 1;
        } catch (error) {
            assert.ok(error instanceof OperationRegistryError);
            break;
        }
    }
    assert.ok(accepted > 0 && accepted < MAX_OPERATION_RECORDS);
    assert.ok(Buffer.byteLength(storage.value!) <= MAX_OPERATION_STORAGE_BYTES);
    assert.equal(registry.snapshot().records.length, accepted);
    for (const record of registry.snapshot().records)
        registry.identity(record.key, { kind: 'operation', operationId: ID });
    assert.ok(Buffer.byteLength(storage.value!) <= MAX_OPERATION_STORAGE_BYTES);
    assert.ok(registry.snapshot().records.every(record => record.operationId === ID));
});

test('V51 persisted summaries contain no body, candidate, raw diagnostics or arbitrary error code', () => {
    const { registry, storage } = fixture();
    const prepared = registry.prepare('plan', SCOPE);
    registry.identity(prepared.key, { kind: 'operation', operationId: ID });
    const envelope = result('plan', 10, 'SYNTHETIC_SECRET');
    envelope.data = { token: 'SYNTHETIC_SECRET', candidate: 'raw TOML' };
    envelope.errors[0].message = 'SYNTHETIC_SECRET';
    registry.complete(prepared.key, envelope, SCOPE);
    assert.ok(!storage.value!.includes('SYNTHETIC_SECRET'));
    assert.ok(!storage.value!.includes('raw TOML'));
    assert.equal(registry.snapshot().records[0].terminal?.code, null);
});
