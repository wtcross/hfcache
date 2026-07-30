/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Run report names: `runs/<UTC>-<run-id>.json` (docs/schemas.md §6;
 * docs/operations.md §4). Pure logic: no cockpit import.
 */

const REPORT_NAME = /^(\d{8})T(\d{6})Z-([0-9a-f]{32})\.json$/;

export interface ReportName {
    file: string;
    startedAt: Date | null;
    runId: string | null;
}

export function isReportName(file: string): boolean {
    return REPORT_NAME.test(file);
}

export function parseReportName(file: string): ReportName {
    const match = REPORT_NAME.exec(file);
    if (match === null)
        return { file, startedAt: null, runId: null };
    const day = match[1];
    const time = match[2];
    const iso = `${day.slice(0, 4)}-${day.slice(4, 6)}-${day.slice(6, 8)}` +
        `T${time.slice(0, 2)}:${time.slice(2, 4)}:${time.slice(4, 6)}Z`;
    const startedAt = new Date(iso);
    return {
        file,
        startedAt: Number.isNaN(startedAt.getTime()) ? null : startedAt,
        runId: match[3],
    };
}

export function isRunId(text: string): boolean {
    return /^[0-9a-f]{32}$/.test(text);
}
