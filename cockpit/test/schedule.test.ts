/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { parseCalendarCheck, parseDropIn, renderDropIn } from '../src/lib/schedule.ts';

test('the drop-in clears the list-valued directive before setting it', () => {
    const content = renderDropIn('*-*-* 03:30:00', '15m');
    const lines = content.split('\n');
    const clearIndex = lines.indexOf('OnCalendar=');
    const setIndex = lines.indexOf('OnCalendar=*-*-* 03:30:00');
    assert.ok(clearIndex >= 0, 'empty assignment present');
    assert.ok(setIndex > clearIndex, 'replacement follows the clear');
    assert.ok(lines.includes('RandomizedDelaySec=15m'));
    assert.ok(content.startsWith('# Written by the hfcache Cockpit plugin'));
});

test('a drop-in round-trips through the parser', () => {
    const parsed = parseDropIn(renderDropIn('Mon *-*-* 04:00:00', null));
    assert.equal(parsed.onCalendar, 'Mon *-*-* 04:00:00');
    assert.equal(parsed.randomizedDelaySec, null);
    const withDelay = parseDropIn(renderDropIn('*-*-* 02:00:00', '30m'));
    assert.equal(withDelay.randomizedDelaySec, '30m');
});

test('systemd-analyze calendar output parses, from the ops §9 sample', () => {
    const output = 'Normalized form: Wed *-01,04,07,10-01..07 04:00:00\n' +
        '    Next elapse: Wed 2026-10-07 04:00:00 EDT\n' +
        '       (in UTC): Wed 2026-10-07 08:00:00 UTC\n' +
        '       From now: 2 months 11 days left\n';
    const check = parseCalendarCheck(output);
    assert.equal(check.normalized, 'Wed *-01,04,07,10-01..07 04:00:00');
    assert.equal(check.next, 'Wed 2026-10-07 04:00:00 EDT');
    assert.deepEqual(parseCalendarCheck('garbage'), { normalized: null, next: null });
});
