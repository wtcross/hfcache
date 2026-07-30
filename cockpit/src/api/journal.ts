/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Following a unit's journal for the live activity feed
 * (docs/cockpit.md §5). Display and the closed event vocabulary only.
 */

import cockpit from 'cockpit';

/* Start following; returns the stop function. The consumer renders lines
 * and interprets them only through lib/events' closed vocabulary. */
export function followUnitJournal(unit: string, onLine: (line: string) => void): () => void {
    const proc = cockpit.spawn(
        ['journalctl', '-u', unit, '-n', '80', '-f', '-q', '-o', 'cat'],
        { superuser: 'require', err: 'ignore' });
    let pending = '';
    proc.stream(data => {
        pending += data;
        const parts = pending.split('\n');
        pending = parts.pop() ?? '';
        for (const line of parts)
            onLine(line);
    });
    // The follower only ends when closed; swallow that rejection.
    proc.then(() => undefined, () => undefined);
    return () => proc.close();
}
