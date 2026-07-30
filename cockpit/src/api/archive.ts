/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The one direct archive read the contract allows (docs/cockpit.md CP-09):
 * run reports under `runs/`, read as the service identity. Everything else
 * about the archive arrives through CLI envelopes. Nothing here writes.
 */

import cockpit from 'cockpit';

import { SERVICE_IDENTITY } from '../lib/command';
import { isReportName, isRunId } from '../lib/reports';

const RUNS_DIRECTORY = '/srv/hfcache/runs';

function readAsService(argv: string[]): cockpit.Spawn<string> {
    return cockpit.spawn(['runuser', '-u', SERVICE_IDENTITY, '--', ...argv],
                         { superuser: 'require', err: 'message' });
}

/* Newest first: the timestamped names sort lexicographically. */
export async function listRunReports(): Promise<string[]> {
    const output = await readAsService(['ls', '-1', RUNS_DIRECTORY]);
    return output.split('\n')
            .filter(isReportName)
            .sort()
            .reverse();
}

export async function readRunReport(file: string): Promise<unknown> {
    if (!isReportName(file))
        throw new Error(`not a run report name: ${file}`);
    const output = await readAsService(['cat', `${RUNS_DIRECTORY}/${file}`]);
    return JSON.parse(output);
}

/* The journal side of the run_id join (docs/cockpit.md §3): every log line
 * carries run_id=…, so one grep over the persistent journal returns exactly
 * one run's trail. Display only — never interpreted beyond the closed
 * event vocabulary. */
export async function journalForRun(runId: string): Promise<string[]> {
    if (!isRunId(runId))
        throw new Error(`not a run id: ${runId}`);
    const output = await cockpit.spawn(
        ['journalctl', '-q', '--no-pager', '-o', 'cat', '-g', `run_id=${runId}`],
        { superuser: 'require', err: 'message' });
    return output.split('\n').filter(line => line !== '');
}
