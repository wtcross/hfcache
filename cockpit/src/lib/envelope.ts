/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The CLI JSON envelope (docs/cli.md §4) as the plugin consumes it
 * (docs/cockpit.md CP-02, §4). Pure logic: no cockpit import, so it runs
 * under node:test as well as in the browser bundle.
 */

export const ENVELOPE_SCHEMA_VERSION = 1;

export interface EnvelopeIssue {
    code: string;
    repository: string | null;
    message: string;
    context?: unknown;
}

export type EnvelopeOutcome = 'success' | 'success_with_warnings' | 'failed';

export interface Envelope {
    schema_version: number;
    command: string;
    run_id: string;
    started_at: string;
    completed_at: string;
    exit_code: number;
    outcome: EnvelopeOutcome;
    data: unknown;
    warnings: EnvelopeIssue[];
    errors: EnvelopeIssue[];
}

export class EnvelopeError extends Error {}

export class EnvelopeSchemaError extends EnvelopeError {
    constructor(found: unknown) {
        super(`envelope schema_version ${String(found)} is not ${ENVELOPE_SCHEMA_VERSION}: ` +
              'this plugin build does not understand it; update the plugin to match the deployed hfcache');
    }
}

function isIssue(value: unknown): value is EnvelopeIssue {
    if (typeof value !== 'object' || value === null)
        return false;
    const issue = value as Record<string, unknown>;
    return typeof issue.code === 'string' &&
        (typeof issue.repository === 'string' || issue.repository === null) &&
        typeof issue.message === 'string';
}

/* Parse one envelope from stdout. The envelope is emitted even on failure
 * (docs/cli.md §4), so callers hand every stdout here and never interpret
 * human text; refusing an unknown schema_version is CP-02. */
export function parseEnvelope(stdout: string): Envelope {
    let parsed: unknown;
    try {
        parsed = JSON.parse(stdout);
    } catch (error) {
        throw new EnvelopeError(`stdout is not a JSON envelope: ${String(error)}`);
    }
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed))
        throw new EnvelopeError('stdout is not a JSON envelope: not an object');
    const env = parsed as Record<string, unknown>;
    if (env.schema_version !== ENVELOPE_SCHEMA_VERSION)
        throw new EnvelopeSchemaError(env.schema_version);
    if (typeof env.command !== 'string' || typeof env.exit_code !== 'number' ||
        typeof env.outcome !== 'string' ||
        !Array.isArray(env.warnings) || !Array.isArray(env.errors) ||
        !env.warnings.every(isIssue) || !env.errors.every(isIssue))
        throw new EnvelopeError('stdout is not a JSON envelope: required fields missing or mistyped');
    return env as unknown as Envelope;
}

/* HFMNT010: the benign "another mutating command is running" case (AD-17),
 * rendered as a busy state and never as a failure (docs/cockpit.md CP-10). */
export const LOCK_BUSY_CODE = 'HFMNT010';

export type ResultKind =
    'success' | 'warnings' | 'invalid' | 'busy' | 'refused' |
    'sync_failures' | 'integrity' | 'maintenance' | 'unknown';

/* Exit codes map to UI states, not to a generic error toast
 * (docs/cockpit.md §4; docs/cli.md §3). */
export function classifyEnvelope(envelope: Envelope): ResultKind {
    switch (envelope.exit_code) {
    case 0:
        return envelope.warnings.length > 0 ? 'warnings' : 'success';
    case 10:
        return 'invalid';
    case 20:
        return envelope.errors.some(issue => issue.code === LOCK_BUSY_CODE) ? 'busy' : 'refused';
    case 30:
        return 'sync_failures';
    case 40:
        return 'integrity';
    case 50:
        return 'maintenance';
    default:
        return 'unknown';
    }
}

/* The operator meaning of each exit code, from docs/operations.md §7. */
export const EXIT_CODE_GUIDANCE: Record<number, { title: string; guidance: string }> = {
    0: {
        title: 'Success',
        guidance: 'Nothing to do. Check outstanding findings if warnings were reported.',
    },
    10: {
        title: 'Invalid configuration or invocation',
        guidance: 'Fix the command or the file. Nothing was touched.',
    },
    20: {
        title: 'Safety refusal',
        guidance: 'Stop. Nothing was downloaded or changed. The common benign cause is the ' +
            'single-writer lock (AD-17); otherwise run doctor.',
    },
    30: {
        title: 'One or more repository sync failures',
        guidance: 'Other repositories may have succeeded. Read the run report.',
    },
    40: {
        title: 'Integrity verification failure',
        guidance: 'Do not sync or prune. Preserve evidence and follow the corruption runbook.',
    },
    50: {
        title: 'Prune, repair, or recovery failure',
        guidance: 'The archive prefers over-retention; run recover --dry-run.',
    },
};
