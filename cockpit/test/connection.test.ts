/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { OwnedConnection } from '../src/lib/connection.ts';

class Client {
    listeners = new Set<() => void>();
    disposals = 0;
    addEventListener(_event: 'close', listener: () => void) { this.listeners.add(listener) }
    removeEventListener(_event: 'close', listener: () => void) { this.listeners.delete(listener) }
    close() { this.disposals += 1 }
    disconnect() { for (const listener of this.listeners) listener(); }
}

test('closed clients dispose listeners and subsequent reads use a new client', async () => {
    const clients: Client[] = [];
    const owner = new OwnedConnection(() => { const value = new Client(); clients.push(value); return value });
    assert.equal(await owner.read(async client => client), clients[0]);
    clients[0].disconnect();
    assert.equal(clients[0].listeners.size, 0);
    assert.equal(clients[0].disposals, 1);
    assert.equal(await owner.read(async client => client), clients[1]);
    clients[0].disconnect();
    assert.equal(owner.generation, 1);
    owner.invalidate();
    assert.equal(clients[1].listeners.size, 0);
});

test('a read has one finite reconnect delay and at most two attempts', async () => {
    let attempts = 0;
    const delays: number[] = [];
    const owner = new OwnedConnection(() => new Client(), async delay => { delays.push(delay) });
    await assert.rejects(owner.read(async () => {
        attempts += 1;
        throw Object.assign(new Error('reconnected'), { problem: 'reconnected' });
    }));
    assert.equal(attempts, 2);
    assert.deepEqual(delays, [100]);
});

test('a late old read cannot become fresh evidence after invalidation', async () => {
    let resume: (() => void) | undefined;
    const waiting = new Promise<void>(resolve => { resume = resolve });
    const owner = new OwnedConnection(() => new Client(), async () => {});
    let attempts = 0;
    const result = owner.read(async () => {
        attempts += 1;
        if (attempts === 1) {
            await waiting;
            return 'stale';
        }
        return 'fresh';
    });
    owner.invalidate();
    resume!();
    assert.equal(await result, 'fresh');
    assert.equal(attempts, 2);
});

test('privilege change during mutation preserves uncertainty without another call', async () => {
    const owner = new OwnedConnection(() => new Client());
    let attempts = 0;
    await assert.rejects(owner.mutate(async () => {
        attempts += 1;
        owner.invalidate();
        return 'possibly completed';
    }), error => {
        assert.equal((error as { problem: unknown }).problem, 'reconnected');
        return true;
    });
    assert.equal(attempts, 1);
});

test('ordinary D-Bus refusal is not retried or reclassified as reconnect', async () => {
    const owner = new OwnedConnection(() => new Client());
    let attempts = 0;
    const refusal = { problem: 'access-denied' };
    await assert.rejects(owner.read(async () => { attempts += 1; throw refusal }), error => error === refusal);
    assert.equal(attempts, 1);
    assert.equal(owner.generation, 0);
});

test('throwing channel disposal still publishes invalidation to every view', async () => {
    const client = new Client();
    client.close = () => { throw new Error('already closed') };
    const owner = new OwnedConnection(() => client);
    await owner.read(async () => true);
    owner.subscribe(() => { throw new Error('detached view') });
    let notices = 0;
    owner.subscribe(() => { notices += 1 });
    owner.invalidate();
    assert.equal(owner.generation, 1);
    assert.equal(notices, 1);
    assert.equal(client.listeners.size, 0);
});

test('V49 host changes retire the cached connection even without a close event', async () => {
    let host = 'first-host';
    const clients: Client[] = [];
    const owner = new OwnedConnection(() => { const value = new Client(); clients.push(value); return value },
                                      async () => {}, () => host);
    const original = await owner.read(async client => client);
    host = 'second-host';
    const replacement = await owner.read(async client => client);
    assert.notEqual(replacement, original);
    assert.equal(original.disposals, 1);
    assert.equal(original.listeners.size, 0);
    assert.equal(owner.generation, 1);
});

test('V49 a late read from another host is retried finitely without returning old evidence', async () => {
    let host = 'first-host';
    const owner = new OwnedConnection(() => new Client(), async () => {}, () => host);
    let attempts = 0;
    const result = await owner.read(async () => {
        attempts += 1;
        if (attempts === 1) { host = 'second-host'; return 'old-host-evidence' }
        return 'current-host-evidence';
    });
    assert.equal(result, 'current-host-evidence');
    assert.equal(attempts, 2);
});

test('V49 host change after a mutation preserves uncertainty and never repeats it', async () => {
    let host = 'first-host';
    const owner = new OwnedConnection(() => new Client(), async () => {}, () => host);
    let attempts = 0;
    await assert.rejects(owner.mutate(async () => {
        attempts += 1; host = 'second-host'; return 'possibly-completed';
    }), error => (error as { problem?: string }).problem === 'reconnected');
    assert.equal(attempts, 1);
});
