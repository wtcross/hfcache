/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Following a unit's journal for the live activity feed
 * (docs/cockpit.md §5). Display and the closed event vocabulary only.
 */

import cockpit from 'cockpit';

import { BoundedLineDecoder } from '../lib/stream';
import { interpretOperationLine, OperationNotice } from '../lib/events';

/* Start following; returns the stop function. The consumer renders lines
 * and interprets them only through lib/events' closed vocabulary. */
export function followUnitJournal(
    unit: string, onLine: (line: string) => void, onNotice?: (notice: OperationNotice) => void,
): () => void {
    const proc = cockpit.spawn(
        ['journalctl', '-u', unit, '-n', '80', '-f', '-q', '-o', 'cat'],
        { superuser: 'require', err: 'ignore' });
    const decoder = new BoundedLineDecoder();
    let dropped = 0;
    let active = true;
    proc.stream(data => {
        // Retain the newest journal invocation's handles before display eviction.
        // At most a key and ID survive a chunk, regardless of line count.
        const handles: OperationNotice[] = [];
        const lines = decoder.push(data, line => {
            const notice = interpretOperationLine(line);
            if (notice?.kind === 'key') {
                handles.length = 0;
                handles.push(notice);
            } else if (notice?.kind === 'operation') {
                if (handles[handles.length - 1]?.kind === 'operation')
                    handles.pop();
                handles.push(notice);
            }
        });
        if (!active)
            return;
        for (const notice of handles)
            onNotice?.(notice);
        if (decoder.droppedLines > dropped) {
            onLine('Journal display gap: oversized or excess lines were omitted');
            dropped = decoder.droppedLines;
        }
        for (const line of lines)
            onLine(line);
    });
    // The follower only ends when closed; swallow that rejection.
    proc.then(() => undefined, () => undefined);
    return () => {
        active = false;
        // This is only journalctl's display follower, never the API executor.
        proc.close();
    };
}
