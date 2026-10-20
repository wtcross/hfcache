/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { normalizeFailure } from '../src/lib/failure.ts';
import { AcknowledgedHostChangeError, HostProfileError } from '../src/lib/host-profile.ts';
import { renderDropIn, ScheduleInputError } from '../src/lib/schedule.ts';
import {
    createScheduleSession, MAX_SCHEDULE_ATTEMPTS, MAX_SCHEDULE_EXPECTED_BYTES, ScheduleSessionError,
} from '../src/lib/schedule-session.ts';

test('V39 pending host attempt is retained synchronously before any asynchronous effect', () => {
    const session = createScheduleSession();
    const attempt = session.begin('fixture-host', 'captured drop-in\n');
    assert.equal(session.snapshot()[0], attempt);
    assert.equal(attempt.state, 'pending');
    assert.ok(Object.isFrozen(attempt) && Object.isFrozen(session.snapshot()));
    assert.throws(() => session.begin('fixture-host', null), ScheduleSessionError);
    assert.equal(session.snapshot()[0].expected, 'captured drop-in\n');
    session.complete(attempt);
    assert.equal(session.snapshot().length, 0);
});

test('V39 the actual UTF-8 rendered drop-in is retained exactly rather than rejecting its public header', () => {
    const session = createScheduleSession();
    const expected = renderDropIn('daily', '30m');
    assert.equal(session.begin('fixture-host', expected).expected, expected);
});

test('V39 component detach cannot drop captured state or a later uncertain completion', () => {
    const session = createScheduleSession();
    const attempt = session.begin('fixture-host', null);
    const detach = session.subscribe(() => undefined);
    detach();
    const failure = new AcknowledgedHostChangeError(new HostProfileError('Sync scheduling is not approved.'), 'schedule-write');
    session.fail(attempt, failure);
    const restored = session.snapshot()[0];
    assert.equal(restored.state, 'uncertain');
    assert.equal(restored.host, 'fixture-host');
    assert.equal(restored.expected, null);
    assert.equal(restored.error?.problem, 'access-denied');
    assert.equal(restored.error?.hostMutationUncertain, true);
    assert.equal(restored.restrictionReason, 'Sync scheduling is not approved.');
    assert.throws(() => session.begin('fixture-host', 'another draft'), ScheduleSessionError);
    session.complete(attempt);
    assert.equal(session.snapshot()[0], restored);
    session.acknowledge(restored);
    assert.equal(session.snapshot().length, 0);
    assert.notEqual(session.begin('fixture-host', null).id, attempt.id);
});

test('V39 known preflight refusal releases only its own pending attempt', () => {
    for (const failure of [new HostProfileError(), new ScheduleInputError(),
        normalizeFailure({ problem: 'reconnected' }, { stage: 'profile-read', hostMutationUncertain: false })]) {
        const session = createScheduleSession();
        const other = session.begin('other-host', null);
        const attempt = session.begin('fixture-host', null);
        session.fail(attempt, failure);
        assert.deepEqual(session.snapshot(), [other]);
    }
});

test('V39 uncertain error retention contains classified facts without raw rejection prose', () => {
    const session = createScheduleSession();
    const attempt = session.begin('fixture-host', null);
    session.fail(attempt, Object.assign(new Error('SYNTHETIC_SECRET'), { problem: 'reconnected' }));
    const record = session.snapshot()[0];
    assert.equal(record.error?.problem, 'reconnected');
    assert.equal(record.error?.hostMutationUncertain, true);
    assert.equal(record.error?.stack, undefined);
    assert.ok(!JSON.stringify(record).includes('SYNTHETIC_SECRET'));
    assert.throws(() => session.acknowledge({ ...record, host: 'other-host' }), ScheduleSessionError);
    assert.equal(session.snapshot()[0], record);
});

test('V39 full schedule recovery memory never evicts unresolved hosts', () => {
    const session = createScheduleSession();
    for (let index = 0; index < MAX_SCHEDULE_ATTEMPTS; index++)
        session.begin('host-' + index, null);
    const before = session.snapshot();
    assert.throws(() => session.begin('extra-host', null), ScheduleSessionError);
    assert.equal(session.snapshot(), before);
    assert.equal(session.snapshot().length, MAX_SCHEDULE_ATTEMPTS);
    const bounded = createScheduleSession();
    let retained = 0;
    while (retained < MAX_SCHEDULE_ATTEMPTS) {
        try { bounded.begin('large-host-' + retained, 'x'.repeat(MAX_SCHEDULE_EXPECTED_BYTES)); retained++ } catch { break }
    }
    assert.ok(retained > 0 && retained < MAX_SCHEDULE_ATTEMPTS);
    assert.equal(bounded.snapshot().length, retained);
    assert.equal(bounded.snapshot()[0].host, 'large-host-0');
});

test('V39 hostile hosts and oversized or unsafe captured bytes cannot reserve recovery memory', () => {
    const session = createScheduleSession();
    for (const host of ['', 'host\nname', 'x'.repeat(256)])
        assert.throws(() => session.begin(host, null), ScheduleSessionError);
    for (const expected of ['x'.repeat(MAX_SCHEDULE_EXPECTED_BYTES + 1), 'draft\0', 'draft\r'])
        assert.throws(() => session.begin('fixture-host', expected), ScheduleSessionError);
    assert.equal(session.snapshot().length, 0);
});
