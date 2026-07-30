/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The schedule drop-in (docs/cockpit.md §7, CP-12): shipped unit files are
 * never edited; the managed drop-in clears the list-valued OnCalendar and
 * sets the replacement. Pure logic: no cockpit import.
 */

export const DROPIN_NAME = '50-cockpit.conf';

export interface DropIn {
    onCalendar: string | null;
    randomizedDelaySec: string | null;
}

/* OnCalendar= is list-valued: an empty assignment clears the shipped value,
 * then the replacement is appended. The last non-empty assignment is the
 * one that matters when reading our own file back. */
export function parseDropIn(content: string): DropIn {
    let onCalendar: string | null = null;
    let randomizedDelaySec: string | null = null;
    for (const line of content.split('\n')) {
        const calendar = /^OnCalendar=(.*)$/.exec(line.trim());
        if (calendar !== null && calendar[1] !== '')
            onCalendar = calendar[1];
        const delay = /^RandomizedDelaySec=(.*)$/.exec(line.trim());
        if (delay !== null && delay[1] !== '')
            randomizedDelaySec = delay[1];
    }
    return { onCalendar, randomizedDelaySec };
}

export function renderDropIn(onCalendar: string, randomizedDelaySec: string | null): string {
    const delay = randomizedDelaySec === null || randomizedDelaySec === ''
        ? ''
        : `RandomizedDelaySec=${randomizedDelaySec}\n`;
    return '# Written by the hfcache Cockpit plugin (docs/cockpit.md §7).\n' +
        '# The shipped unit file is never edited (CP-12); removing this file\n' +
        '# restores the shipped schedule. The empty assignment clears the\n' +
        '# list-valued directive before the replacement is set.\n' +
        '[Timer]\n' +
        'OnCalendar=\n' +
        `OnCalendar=${onCalendar}\n` +
        delay;
}

export interface CalendarCheck {
    normalized: string | null;
    next: string | null;
}

/* `systemd-analyze calendar` output, e.g. (docs/operations.md §9):
 *   Normalized form: Wed *-01,04,07,10-01..07 04:00:00
 *       Next elapse: Wed 2026-10-07 04:00:00 EDT
 */
export function parseCalendarCheck(output: string): CalendarCheck {
    const normalized = /Normalized form:\s*(.+)/.exec(output);
    const next = /Next elapse:\s*(.+)/.exec(output);
    return {
        normalized: normalized === null ? null : normalized[1].trim(),
        next: next === null ? null : next[1].trim(),
    };
}
