/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { BoundaryError, FAILURE_STAGES, normalizeFailure } from '../src/lib/failure.ts';
import { utf8Bytes } from '../src/lib/stream.ts';

test('reclassifying an explicit preflight refusal does not invent a transmitted host change', () => {
    const preflight = normalizeFailure({ problem: 'access-denied' }, {
        stage: 'candidate-write', hostMutationUncertain: false,
    });
    const pipeline = normalizeFailure(preflight, { stage: 'candidate-write' });
    assert.equal(pipeline.hostMutationUncertain, false);
    assert.equal(pipeline.category, 'access');
    const transmitted = normalizeFailure(pipeline, { stage: 'install', hostMutationUncertain: true });
    assert.equal(normalizeFailure(transmitted, { hostMutationUncertain: false }).hostMutationUncertain, true);
});

const KEY = 'original-safe-key';
const ID = 'a'.repeat(32);
const SECRET = 'synthetic-api-hub-mcp-candidate-secret';

for (const stage of FAILURE_STAGES) {
    test(`reconnected retains a known ${stage} boundary without raw exception prose`, () => {
        for (const failure of [
            Object.assign(new Error(SECRET), { problem: 'reconnected' }),
            { message: SECRET, problem: 'reconnected' },
            new Error('reconnected'),
        ]) {
            const result = normalizeFailure(failure, { stage });
            assert.ok(result instanceof BoundaryError);
            assert.equal(result.stage, stage);
            assert.equal(result.category, 'bridge');
            assert.equal(result.problem, 'reconnected');
            assert.ok(result.safeDiagnostics.includes('Cockpit problem: reconnected'));
            assert.ok(!result.message.includes(SECRET));
            assert.ok(!JSON.stringify(result).includes(SECRET));
            assert.ok(utf8Bytes(result.message) <= 1024);
        }
    });
}

test('access, launcher, process, protocol and unavailable observation remain distinct', () => {
    for (const [failure, category] of [
        [{ problem: 'access-denied' }, 'access'],
        [{ problem: 'authentication-failed' }, 'access'],
        [{ problem: 'not-found' }, 'launcher'],
        [{ exit_status: 127 }, 'process'],
        [{ exit_signal: 15 }, 'process'],
        [{ problem: 'protocol-error' }, 'protocol'],
        [{ message: SECRET }, 'observation'],
    ] as const)
        assert.equal(normalizeFailure(failure).category, category);
    assert.equal(normalizeFailure(null, { reason: 'invalid-envelope' }).category, 'protocol');
});

test('plain and Error process fields keep finite status and recognized signals', () => {
    for (const fields of [
        { exit_status: 17, exit_signal: 'TERM' },
        { exit_status: 255, exit_signal: 'SIGTERM' },
        { exit_status: 1, exit_signal: 9 },
    ]) {
        for (const failure of [fields, Object.assign(new Error(SECRET), fields)]) {
            const result = normalizeFailure(failure, { stage: 'operation-observe' });
            assert.equal(result.category, 'process');
            assert.equal(result.exitStatus, fields.exit_status);
            assert.equal(result.exitSignal, fields.exit_signal);
        }
    }
});

test('malformed and unbounded rejection values never become messages or diagnostics', () => {
    for (const problem of [SECRET, SECRET.repeat(100000), '\u0000\n' + SECRET]) {
        for (const exit of [Infinity, NaN, -1, 9999999999999, '17', {}]) {
            const result = normalizeFailure({
                message: SECRET.repeat(100000),
                problem,
                exit_status: exit,
                exit_signal: exit,
                stderr: SECRET,
                candidate: SECRET,
                credentials: SECRET,
            });
            assert.equal(result.problem, 'unknown');
            assert.equal(result.exitStatus, undefined);
            assert.equal(result.exitSignal, undefined);
            assert.deepEqual(result.safeDiagnostics, ['Cockpit problem: unrecognized value (withheld)']);
            assert.ok(!JSON.stringify(result).includes(SECRET));
            assert.ok(!result.message.includes(SECRET));
            assert.ok(!result.stack?.includes(SECRET));
        }
    }
    assert.equal(normalizeFailure({ exit_signal: SECRET }).exitSignal, undefined);
    assert.equal(normalizeFailure({ exit_signal: 'SIG' + SECRET }).exitSignal, undefined);
});

test('normalization does not evaluate arbitrary getters or stringify failure objects', () => {
    let evaluated = 0;
    const failure = {
        get problem() { evaluated += 1; throw new Error(SECRET) },
        get message() { evaluated += 1; throw new Error(SECRET) },
        toString() { evaluated += 1; return SECRET },
    };
    assert.equal(normalizeFailure(failure).category, 'observation');
    assert.equal(evaluated, 0);
    assert.equal(normalizeFailure(new Proxy({}, {
        getOwnPropertyDescriptor() { throw new Error(SECRET) },
        getPrototypeOf() { throw new Error(SECRET) },
    })).category, 'observation');
});

test('rewrapping preserves original facts and uncertainty while accepting explicit stage context', () => {
    const original = normalizeFailure({ problem: 'reconnected', exit_status: 17, exit_signal: 'TERM' }, {
        stage: 'candidate-preview',
        idempotencyKey: KEY,
        operationId: ID,
        hostMutationUncertain: true,
    });
    const same = normalizeFailure(original);
    const moved = normalizeFailure(original, { stage: 'installed-confirm', hostMutationUncertain: false });
    assert.equal(same.stage, 'candidate-preview');
    for (const result of [same, moved]) {
        assert.equal(result.category, 'bridge');
        assert.equal(result.problem, 'reconnected');
        assert.equal(result.exitStatus, 17);
        assert.equal(result.exitSignal, 'TERM');
        assert.equal(result.idempotencyKey, KEY);
        assert.equal(result.operationId, ID);
        assert.equal(result.hostMutationUncertain, true);
        assert.equal(result.workMayContinue, true);
    }
    assert.equal(moved.stage, 'installed-confirm');
});

test('synchronous validation creates no operation while host mutation uncertainty remains explicit', () => {
    for (const stage of ['candidate-validate', 'installed-validate'] as const) {
        const result = normalizeFailure({ problem: 'reconnected' }, { stage });
        assert.equal(result.workMayContinue, false);
        assert.equal(result.idempotencyKey, undefined);
        assert.equal(result.operationId, undefined);
        assert.match(result.message, /Validation has no operation receipt/);
        assert.doesNotMatch(result.message, /Accepted server work/);
    }
    for (const stage of ['candidate-write', 'install', 'installed-confirm', 'unit-mutation', 'schedule-write'] as const)
        assert.equal(normalizeFailure(null, { stage }).hostMutationUncertain, true);
    assert.equal(normalizeFailure(null).stage, 'api-read');
    assert.equal(normalizeFailure(null).hostMutationUncertain, false);
});

test('pre-transmission access refusal does not invent a host write or clear prior uncertainty', () => {
    const refused = normalizeFailure({ problem: 'access-denied' }, {
        stage: 'install', hostMutationUncertain: false,
    });
    assert.equal(refused.category, 'access');
    assert.equal(refused.hostMutationUncertain, false);
    assert.doesNotMatch(refused.message, /host change may have completed/);
    assert.equal(normalizeFailure(null, { stage: 'install' }).hostMutationUncertain, true);
    const prior = normalizeFailure({ problem: 'reconnected' }, {
        stage: 'install', hostMutationUncertain: true,
    });
    assert.equal(normalizeFailure(prior, {
        stage: 'installed-confirm', hostMutationUncertain: false,
    }).hostMutationUncertain, true);
});

test('only bounded safe handles become operation evidence', () => {
    const bad = normalizeFailure(null, {
        idempotencyKey: KEY + '\n' + SECRET, operationId: SECRET,
    });
    assert.equal(bad.idempotencyKey, undefined);
    assert.equal(bad.operationId, undefined);
    assert.equal(bad.workMayContinue, false);
    const good = normalizeFailure(null, { idempotencyKey: KEY, operationId: ID });
    assert.equal(good.idempotencyKey, KEY);
    assert.equal(good.operationId, ID);
    assert.equal(good.workMayContinue, true);
});
