/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

import { sameOperationScope } from '../src/lib/operation-registry.ts';
import type { OperationScope } from '../src/lib/operation-registry.ts';

// Execute the actual production effect body, without a parallel implementation.
// Mounted component lifecycle coverage remains in browser.fixture.tsx.
const source = readFileSync(new URL('../src/configuration.tsx', import.meta.url), 'utf8');
const effectEnd = source.indexOf('    }, [operations.registry.records, operations.views.authority,');
const marker = '    useEffect(() => {\n';
const effectStart = source.lastIndexOf(marker, effectEnd);
assert.ok(effectEnd >= 0 && effectStart >= 0, 'Actual Configuration authority effect must be identifiable');
const effect = source.slice(effectStart + marker.length, effectEnd);

const connection = Object.freeze({ generation: 17, administrative: true });
const scope: Readonly<OperationScope> = Object.freeze({
    host: 'synthetic-configuration-host',
    profile: 'a'.repeat(64),
    authorityFingerprint: 'b'.repeat(64),
    endpoint: 'unix:/run/hfcache/api/api.sock',
    credentialClass: 'rest-writer',
    archiveId: '11111111-2222-4333-8444-555555555555',
    instanceId: 'c'.repeat(32)
});

interface Authority {
    scope: Readonly<OperationScope> | null;
    generation: number;
    loading: boolean;
    error: Error | null;
}

const matching: Authority = { scope, generation: 17, loading: false, error: null };
const unavailable: readonly Authority[] = [
    { scope: null, generation: 17, loading: true, error: null },
    { scope: null, generation: 17, loading: false, error: new Error('Synthetic authority read failed') },
];

function runEffect(phase: 'idle' | 'ready', capturedAuthority: Authority, liveAuthority: Authority) {
    const proposal = Object.freeze({ captured: 'exact synthetic configuration proposal' });
    let state = {
        phase,
        confirmed: phase === 'idle',
        previewUncertain: false,
        previewKey: null,
        preparation: phase === 'ready' ? proposal : null,
        authority: scope,
        inspectedGeneration: 17,
        connectionChanged: false
    };
    const before = state;
    runInNewContext(`(() => {\n${effect}\n})()`, {
        session: {
            snapshot: () => state,
            patch: (patch: Partial<typeof state>) => { state = { ...state, ...patch } }
        },
        operations: { registry: { records: [] }, views: { authority: capturedAuthority } },
        operationRegistry: { snapshot: () => ({ records: [] }) },
        operationViews: () => ({ authority: liveAuthority }),
        synchronizeConnection: () => connection,
        connection,
        currentOperationHost: () => scope.host,
        sameOperationScope
    });
    return { before, after: state };
}

for (const phase of ['idle', 'ready'] as const) {
    const result = phase === 'idle' ? 'confirmed installation' : 'ready proposal';
    test(`actual Configuration authority effect preserves a fresh ${result} after an older authority read`, () => {
        for (const capturedAuthority of unavailable) {
            const { before, after } = runEffect(phase, capturedAuthority, matching);
            assert.strictEqual(after, before, 'A captured loading/error authority must not invalidate newer matching evidence');
        }
    });

    test(`actual Configuration authority effect invalidates a ${result} when live authority is unavailable or changed`, () => {
        for (const liveAuthority of [...unavailable, { ...matching, scope: { ...scope, profile: 'd'.repeat(64) } }]) {
            const { after } = runEffect(phase, matching, liveAuthority);
            assert.equal(after.confirmed, false);
            assert.equal(after.phase, 'idle');
            assert.equal(after.preparation, null);
            assert.equal(after.connectionChanged, true);
        }
    });
}
