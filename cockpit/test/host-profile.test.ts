/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
    AcknowledgedHostChangeError, HOST_ACTIONS, HOST_UNITS, HostProfileError, MAX_HOST_PROFILE_BYTES, parseHostProfile,
    profileActionAllowed, profileActionReason,
} from '../src/lib/host-profile.ts';
import { SYNC_SERVICE, SYNC_TIMER } from '../src/lib/systemd.ts';
import { normalizeFailure } from '../src/lib/failure.ts';

function permitted() {
    return {
        schema_version: 1,
        state: 'permitted',
        deployment: 'rootless',
        source_commit: 'a'.repeat(40),
        index_sha256: 'b'.repeat(64),
        image: 'sha256:' + 'c'.repeat(64),
        policy_sha256: 'd'.repeat(64),
        permissions: { archive: true, hub: true, control: true, schedule: true, configuration: true, observer: true },
        facts: {
            guard: 'inactive',
            archive_mount: 'local-rw',
            units: Object.fromEntries(HOST_UNITS.map(unit => [unit,
                { load: 'loaded', active: 'inactive', unit_file: 'disabled' }]))
        }
    };
}

function refuses(value: unknown): void {
    assert.throws(() => parseHostProfile(JSON.stringify(value)), error => {
        assert.ok(error instanceof HostProfileError);
        assert.ok(!error.message.includes('SYNTHETIC_SECRET'));
        return true;
    });
}

test('V38 trusted explicit permissions are exact, deeply immutable and never inferred', () => {
    const result = parseHostProfile(JSON.stringify(permitted()));
    assert.notEqual(result.state, 'unknown');
    if (result.state === 'unknown') assert.fail('Expected known fixture profile');
    assert.ok(Object.isFrozen(result) && Object.isFrozen(result.permissions) && Object.isFrozen(result.facts));
    assert.ok(Object.isFrozen(result.facts.units) && Object.isFrozen(result.facts.units[SYNC_TIMER]));
    for (const action of HOST_ACTIONS)
        assert.equal(profileActionAllowed(result, action), true);
    const denied = permitted();
    denied.permissions = { archive: false, hub: false, control: false, schedule: false, configuration: false, observer: false };
    denied.facts.guard = 'absent';
    for (const action of HOST_ACTIONS)
        assert.equal(profileActionAllowed(parseHostProfile(JSON.stringify(denied)), action), false);
});

test('V37 held original guard always denies archive execution and explains the restriction', () => {
    const value = permitted();
    value.state = 'guarded';
    value.facts.guard = 'held';
    value.facts.archive_mount = 'nfs-ro';
    refuses(value);
    value.permissions.archive = false;
    const parsed = parseHostProfile(JSON.stringify(value));
    assert.equal(profileActionAllowed(parsed, 'archive'), false);
    assert.match(profileActionReason(parsed, 'archive'), /retained read-only guard/);
    value.state = 'permitted';
    refuses(value);
});

test('V38 read-only facts alone neither create nor erase explicit submission permissions', () => {
    const value = permitted();
    value.facts.archive_mount = 'local-ro';
    const profile = parseHostProfile(JSON.stringify(value));
    assert.equal(profileActionAllowed(profile, 'archive'), true);
    value.permissions.archive = false;
    value.facts.archive_mount = 'local-rw';
    assert.equal(profileActionAllowed(parseHostProfile(JSON.stringify(value)), 'archive'), false);
});

test('V38 every known unknown inspection reason denies all effects without echoing input', () => {
    for (const reason of ['policy-missing', 'policy-invalid', 'deployment-unverified', 'facts-unavailable', 'privilege-required']) {
        const parsed = parseHostProfile(JSON.stringify({ schema_version: 1, state: 'unknown', reason }));
        for (const action of HOST_ACTIONS)
            assert.equal(profileActionAllowed(parsed, action), false);
        assert.ok(profileActionReason(parsed).length > 0);
    }
    for (const action of HOST_ACTIONS)
        assert.equal(profileActionAllowed(null, action), false);
    refuses({ schema_version: 1, state: 'unknown', reason: 'SYNTHETIC_SECRET' });
    refuses({ schema_version: 1, state: 'unknown', reason: 'policy-missing', permissions: permitted().permissions });
});

test('V38/V51 missing or extra fields at every boundary refuse instead of granting defaults', () => {
    for (const key of Object.keys(permitted())) {
        const value = permitted() as Record<string, unknown>;
        delete value[key];
        refuses(value);
    }
    refuses({ ...permitted(), secret: 'SYNTHETIC_SECRET' });
    const permissions = permitted();
    Object.assign(permissions.permissions, { unknown: true });
    refuses(permissions);
    const facts = permitted();
    Object.assign(facts.facts, { credential: 'SYNTHETIC_SECRET' });
    refuses(facts);
    const units = permitted();
    units.facts.units['sshd.service'] = { load: 'loaded', active: 'inactive', unit_file: 'enabled' };
    refuses(units);
    const unit = permitted();
    Object.assign(unit.facts.units[SYNC_TIMER], { path: 'SYNTHETIC_SECRET' });
    refuses(unit);
});

test('V38 mistyped schema, permission, identity and host fact values refuse', () => {
    for (const schema_version of [null, true, '1', 2]) refuses({ ...permitted(), schema_version });
    for (const deployment of ['native', 'mixed', null]) refuses({ ...permitted(), deployment });
    for (const source_commit of ['a'.repeat(39), 'A'.repeat(40), 'SYNTHETIC_SECRET'])
        refuses({ ...permitted(), source_commit });
    for (const image of ['c'.repeat(64), 'sha256:' + 'C'.repeat(64), null])
        refuses({ ...permitted(), image });
    for (const key of ['index_sha256', 'policy_sha256'])
        refuses({ ...permitted(), [key]: 'SYNTHETIC_SECRET' });
    for (const action of HOST_ACTIONS) {
        const value = permitted();
        Object.assign(value.permissions, { [action]: 1 });
        refuses(value);
    }
    const value = permitted();
    value.facts.guard = 'unknown';
    refuses(value);
    value.facts.guard = 'inactive';
    value.facts.archive_mount = 'nfs-rw';
    refuses(value);
});

test('V39 masked or unavailable timer/service facts cannot carry positive scheduling permission', () => {
    for (const name of [SYNC_TIMER, SYNC_SERVICE]) {
        for (const field of ['load', 'unit_file'] as const) {
            const value = permitted();
            value.facts.units[name][field] = 'masked';
            refuses(value);
            value.permissions.schedule = false;
            value.permissions.observer = false;
            assert.doesNotThrow(() => parseHostProfile(JSON.stringify(value)));
        }
    }
    const observer = permitted();
    observer.permissions.schedule = false;
    observer.facts.units[SYNC_SERVICE].load = 'not-found';
    refuses(observer);
});

test('V38 linked and runtime unit states retain exact fixed-system facts', () => {
    for (const unit_file of ['linked', 'linked-runtime', 'enabled-runtime']) {
        const value = permitted();
        value.facts.units[SYNC_TIMER].unit_file = unit_file;
        assert.doesNotThrow(() => parseHostProfile(JSON.stringify(value)));
    }
});

test('V38 duplicate decoded keys, unbounded data and malformed JSON never become host permissions', () => {
    const original = JSON.stringify(permitted());
    for (const value of [
        original.replace('"schema_version":1', '"schema_version":2,"schema_version":1'),
        original.replace('"archive":true', '"archive":false,"\\u0061rchive":true'),
        original.replace('"load":"loaded"', '"load":"masked","load":"loaded"'),
        ' '.repeat(MAX_HOST_PROFILE_BYTES) + original,
        '{"SYNTHETIC_SECRET":',
        '['.repeat(10) + '0' + ']'.repeat(10),
    ])
        assert.throws(() => parseHostProfile(value), HostProfileError);
});

test('V39 a later permission refusal retains acknowledged host-change uncertainty', () => {
    const denied = new HostProfileError('Sync scheduling is not approved by the trusted host profile.');
    for (const stage of ['schedule-write', 'unit-mutation'] as const) {
        const failed = new AcknowledgedHostChangeError(denied, stage);
        assert.equal(failed.stage, stage);
        assert.equal(failed.hostMutationUncertain, true);
        assert.equal(failed.category, 'access');
        assert.equal(failed.problem, 'access-denied');
        assert.equal(failed.restrictionReason, denied.message);
        assert.equal(normalizeFailure(failed).hostMutationUncertain, true);
    }
});

test('V39 a failure after acknowledgement preserves original classified bridge facts safely', () => {
    const original = normalizeFailure({ problem: 'reconnected', exit_status: 125, message: 'SYNTHETIC_SECRET' },
                                      { stage: 'unit-read', hostMutationUncertain: false });
    const failed = new AcknowledgedHostChangeError(original, 'schedule-write');
    assert.equal(failed.stage, 'schedule-write');
    assert.equal(failed.hostMutationUncertain, true);
    assert.equal(failed.problem, 'reconnected');
    assert.equal(failed.category, 'bridge');
    assert.equal(failed.exitStatus, 125);
    assert.equal(failed.restrictionReason, null);
    assert.equal(original.hostMutationUncertain, false);
    assert.ok(!failed.message.includes('SYNTHETIC_SECRET'));
    assert.ok(!failed.safeDiagnostics.join(' ').includes('SYNTHETIC_SECRET'));
});
