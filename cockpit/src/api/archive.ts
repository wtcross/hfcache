/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Optional bounded host-local journal diagnostics (CP-09, decision 136).
 * Durable run reports use the authenticated REST-backed client in reports.ts.
 */

import cockpit from 'cockpit';

import { isRunId } from '../lib/reports';
import { assertSession, captureSession } from './connection';
import { collectRunJournal, JournalReadError } from '../lib/run-journal';
import type { RunJournal } from '../lib/run-journal';

export { JournalReadError } from '../lib/run-journal';
export type { RunJournal, JournalTruncationReason } from '../lib/run-journal';

/* Optional host-local event trail (decision 136). REST reports remain usable
 * independently of this diagnostic's availability, retention window or caps. */
export async function journalForRun(runId: string): Promise<RunJournal> {
    if (typeof runId !== 'string' || !isRunId(runId))
        throw new JournalReadError({ problem: 'protocol-error' });
    try {
        const generation = captureSession('journal-read');
        const host = cockpit.transport.host;
        const result = await collectRunJournal(runId, argv =>
            cockpit.spawn(argv, { superuser: 'require', err: 'ignore' }));
        assertSession(generation, 'journal-read');
        if (host !== cockpit.transport.host)
            throw new JournalReadError({ problem: 'reconnected' });
        return result;
    } catch (failure) {
        throw failure instanceof JournalReadError ? failure : new JournalReadError(failure);
    }
}
