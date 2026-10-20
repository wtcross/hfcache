/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Reading, validating, writing, and removing the schedule drop-in
 * (docs/cockpit.md §7). Calendar expressions are validated by
 * systemd-analyze before anything is written (CP-12).
 */

import cockpit from 'cockpit';

import { assertSession, captureSession, hostCall } from './connection';
import { requireHostAction } from './profile';
import { HostProfileError } from '../lib/host-profile';

import {
    CalendarCheck, DROPIN_NAME, parseCalendarCheck, renderDropIn, ScheduleInputError,
    validateCalendarExpression,
} from '../lib/schedule';

const DROPIN_DIR = '/etc/systemd/system/hfcache-sync.timer.d';
export const DROPIN_PATH = `${DROPIN_DIR}/${DROPIN_NAME}`;

export function readDropIn(): Promise<string | null> {
    return hostCall('schedule-read', false, async () => {
        const file = cockpit.file(DROPIN_PATH, { superuser: 'try' });
        try {
            const content = await file.read();
            if (content !== null && new TextEncoder().encode(content).length > 65536)
                throw new Error('Schedule content exceeds its bound');
            return content;
        } finally {
            file.close();
        }
    });
}

/* Unprivileged and read-only: the validation the contract requires before
 * any write. Failure retains safe process facts without raw stderr. */
export async function checkCalendar(expression: string): Promise<CalendarCheck> {
    validateCalendarExpression(expression);
    const output = await hostCall('schedule-validate', false, () => cockpit.spawn(
        ['systemd-analyze', 'calendar', '--iterations=1', '--', expression],
        { err: 'message' }));
    if (new TextEncoder().encode(output).length > 65536)
        throw new ScheduleInputError('Calendar validation output exceeded its bound.');
    const result = parseCalendarCheck(output);
    if (result.normalized === null)
        throw new ScheduleInputError('Calendar validation did not return a normalized expression.');
    return result;
}

export async function writeDropIn(onCalendar: string, randomizedDelaySec: string | null): Promise<void> {
    const generation = captureSession('schedule-write');
    const host = cockpit.transport.host;
    const content = renderDropIn(onCalendar, randomizedDelaySec);
    await requireHostAction('schedule');
    await checkCalendar(onCalendar);
    if (randomizedDelaySec !== null && randomizedDelaySec !== '') {
        const output = await hostCall('schedule-validate', false, () => cockpit.spawn(
            ['systemd-analyze', 'timespan', '--', randomizedDelaySec], { err: 'message' }));
        if (new TextEncoder().encode(output).length > 65536)
            throw new ScheduleInputError('Delay validation output exceeded its bound.');
    }
    assertSession(generation, 'schedule-write');
    await requireHostAction('schedule');
    assertSession(generation, 'schedule-write');
    if (host !== cockpit.transport.host)
        throw new HostProfileError();
    const script =
        `mkdir -p ${DROPIN_DIR}\n` +
        `tmp=$(mktemp ${DROPIN_DIR}/.${DROPIN_NAME}.XXXXXX)\n` +
        'cat > "$tmp"\n' +
        'chmod 0644 "$tmp"\n' +
        `mv -f "$tmp" ${DROPIN_PATH}\n`;
    await hostCall('schedule-write', true, async () => {
        const proc = cockpit.spawn(['bash', '-ec', script], { superuser: 'require', err: 'message' });
        proc.input(content);
        await proc;
    });
}

/* Removing the drop-in is "reset to the shipped schedule"; the directory
 * goes too when this file was the only reason it existed. */
export async function removeDropIn(): Promise<void> {
    const generation = captureSession('schedule-write');
    const host = cockpit.transport.host;
    await requireHostAction('schedule');
    assertSession(generation, 'schedule-write');
    if (host !== cockpit.transport.host)
        throw new HostProfileError();
    const script =
        `rm -f ${DROPIN_PATH}\n` +
        `rmdir ${DROPIN_DIR} 2>/dev/null || true\n`;
    await hostCall('schedule-write', true, () =>
        cockpit.spawn(['bash', '-ec', script], { superuser: 'require', err: 'message' }));
}
