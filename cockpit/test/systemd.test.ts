/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
    assertOperable, ForbiddenUnitError, HFCACHE_TARGET, SYNC_SERVICE, SYNC_TIMER,
    type UnitAction, VERIFY_SERVICE, VERIFY_TIMER,
} from '../src/lib/systemd.ts';

const actions: UnitAction[] = ['start', 'stop', 'restart', 'enable', 'disable'];

test('full operations retain the installed observer services (CP-04)', () => {
    assert.doesNotThrow(() => assertOperable(SYNC_SERVICE, 'start'));
    assert.doesNotThrow(() => assertOperable(SYNC_SERVICE, 'stop'));
    assert.doesNotThrow(() => assertOperable(VERIFY_SERVICE, 'start'));
    for (const action of ['restart', 'enable', 'disable'] as const)
        assert.throws(() => assertOperable(SYNC_SERVICE, action), ForbiddenUnitError);
    for (const action of actions.filter(action => action !== 'start'))
        assert.throws(() => assertOperable(VERIFY_SERVICE, action), ForbiddenUnitError);
});

test('only the sync timer can be controlled or rescheduled (CP-05/06)', () => {
    for (const action of actions) {
        assert.doesNotThrow(() => assertOperable(SYNC_TIMER, action));
        assert.throws(() => assertOperable(VERIFY_TIMER, action), ForbiddenUnitError);
        assert.throws(() => assertOperable(HFCACHE_TARGET, action), ForbiddenUnitError);
    }
});

test('client controls grant no actual executor, socket, mount or generic unit authority', () => {
    for (const unit of ['hfcache-api.service', 'hfcache-api.socket',
        'hfcache-verification.service', 'hfcache-verification.socket',
        'srv-hfcache.mount', 'srv-hfcache.automount', 'sshd.service', '__proto__', '']) {
        for (const action of actions)
            assert.throws(() => assertOperable(unit, action), ForbiddenUnitError, `${action} ${unit}`);
    }
});
