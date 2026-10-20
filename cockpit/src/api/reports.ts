/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Fixed authenticated REST report reads: no archive paths, keys or job admission.
 */
import { runHfcache } from './hfcache';
import { assertSession, captureSession } from './connection';
import { currentOperationHost } from './operations';
import type { Envelope } from '../lib/envelope';
import { normalizeFailure } from '../lib/failure';
import { isReadCursor, ReadMetadataError } from '../lib/read-metadata';
import type { RunReadMetadata } from '../lib/read-metadata';
import { isRunId, parseRunPage, parseRunReport, REPORT_PAGE_LIMIT } from '../lib/reports';
import type { RunPage, RunReport } from '../lib/reports';

export interface RunPageResult { envelope: Envelope; metadata: Readonly<RunReadMetadata> | null; page: RunPage | null }
export interface RunDetailResult { envelope: Envelope; metadata: Readonly<RunReadMetadata> | null; report: Readonly<RunReport> | null }

async function read(command: string[]): Promise<{ envelope: Envelope; metadata: Readonly<RunReadMetadata> | null }> {
    const generation = captureSession('api-read');
    const host = currentOperationHost();
    let metadata: Readonly<RunReadMetadata> | null = null;
    const envelope = await runHfcache(command, { onReadMetadata: value => { metadata = value } });
    if (envelope.exit_code === 0) {
        assertSession(generation, 'api-read');
        if (host !== currentOperationHost() || metadata === null)
            throw normalizeFailure({ problem: 'reconnected' }, { stage: 'api-read' });
    }
    return { envelope, metadata: envelope.exit_code === 0 ? metadata : null };
}

export async function listRunReports(cursor: string | null = null, expected?: Readonly<RunReadMetadata>): Promise<RunPageResult> {
    const capturedExpected = expected === undefined ? undefined : Object.freeze({ ...expected });
    if (cursor !== null && !isReadCursor(cursor))
        throw normalizeFailure(new ReadMetadataError(), { stage: 'api-read', reason: 'invalid-envelope' });
    const result = await read(['runs', 'list', '--limit', String(REPORT_PAGE_LIMIT), ...(cursor === null ? [] : ['--cursor=' + cursor])]);
    if (result.envelope.exit_code !== 0)
        return { ...result, page: null };
    try {
        return { ...result, page: parseRunPage(result.envelope, result.metadata!, capturedExpected) };
    } catch {
        throw normalizeFailure(null, { stage: 'api-read', reason: 'invalid-envelope' });
    }
}

export async function readRunReport(runId: string, expectedArchive?: string): Promise<RunDetailResult> {
    if (!isRunId(runId))
        throw normalizeFailure(new ReadMetadataError(), { stage: 'api-read', reason: 'invalid-envelope' });
    const result = await read(['runs', 'show', '--', runId]);
    if (result.envelope.exit_code !== 0)
        return { ...result, report: null };
    try {
        return { ...result, report: parseRunReport(result.envelope, result.metadata!, runId, expectedArchive) };
    } catch {
        throw normalizeFailure(null, { stage: 'api-read', reason: 'invalid-envelope' });
    }
}
