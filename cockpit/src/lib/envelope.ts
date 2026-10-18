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
        typeof issue.message === 'string' &&
        (issue.context === undefined || isRecord(issue.context));
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isTimestamp(value: unknown): value is string {
    return typeof value === 'string' && value.length <= 64 &&
        /^\d{4}-\d{2}-\d{2}T/.test(value) && Number.isFinite(Date.parse(value));
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
    if (typeof env.command !== 'string' || env.command.length === 0 ||
        typeof env.run_id !== 'string' || !/^[0-9a-f]{32}$/.test(env.run_id) ||
        !isTimestamp(env.started_at) || !isTimestamp(env.completed_at) ||
        !isRecord(env.data) ||
        ![0, 10, 20, 30, 40, 50].includes(env.exit_code as number) ||
        !['success', 'success_with_warnings', 'failed'].includes(env.outcome as string) ||
        !Array.isArray(env.warnings) || !Array.isArray(env.errors) ||
        !env.warnings.every(isIssue) || !env.errors.every(isIssue))
        throw new EnvelopeError('stdout is not a JSON envelope: required fields missing or mistyped');
    const success = env.exit_code === 0;
    if (success !== (env.outcome !== 'failed') ||
        (success && (env.errors.length !== 0 ||
            ((env.outcome === 'success_with_warnings') !== (env.warnings.length > 0)))) ||
        (!success && env.errors.length === 0))
        throw new EnvelopeError('stdout is not a JSON envelope: outcome and failure evidence disagree');
    return env as unknown as Envelope;
}

/* A page observer merges stderr into the stream so API progress is visible
 * (docs/cockpit.md §5); the envelope is the last JSON document in that mixed
 * output. Documented progress/handle lines never start with `{`,
 * so scanning line starts from the end finds it deterministically. */
export function extractEnvelope(output: string): Envelope {
    try {
        return parseEnvelope(output);
    } catch {
        // Mixed stream; scan for the envelope below.
    }
    const lines = output.split('\n');
    for (let index = lines.length - 1; index >= 0; index -= 1) {
        if (lines[index].startsWith('{')) {
            const candidate = lines.slice(index).join('\n');
            try {
                return parseEnvelope(candidate);
            } catch {
                // Not the envelope's first line; keep scanning.
            }
        }
    }
    throw new EnvelopeError('no JSON envelope found in command output');
}

/* HFMNT010: the benign "another mutating command is running" case (AD-17),
 * rendered as a busy state and never as a failure (docs/cockpit.md CP-10). */
export const LOCK_BUSY_CODE = 'HFMNT010';

export type ResultKind =
    'success' | 'warnings' | 'invalid' | 'busy' | 'refused' | 'observation' |
    'sync_failures' | 'integrity' | 'maintenance' | 'unknown';

export interface OperationEvidence {
    idempotencyKey?: string;
    operationId?: string;
    workMayContinue: boolean;
}

/* Only validated nonsecret handles become reconnection commands (ADR122).
 * Evidence never turns an observer failure into an execution outcome. */
export function operationEvidence(envelope: Envelope): OperationEvidence {
    return readOperationEvidence(envelope.data);
}

export function readOperationEvidence(value: unknown): OperationEvidence {
    const data = isRecord(value) ? value : {};
    const evidence: OperationEvidence = { workMayContinue: data.work_may_continue === true };
    if (typeof data.idempotency_key === 'string' && /^[A-Za-z0-9._~+-]{1,128}$/.test(data.idempotency_key))
        evidence.idempotencyKey = data.idempotency_key;
    if (typeof data.operation_id === 'string' && /^[0-9a-f]{32}$/.test(data.operation_id))
        evidence.operationId = data.operation_id;
    return evidence;
}

export function operationCommands(evidence: OperationEvidence): { lookup?: string; wait?: string } {
    const valid = readOperationEvidence({
        idempotency_key: evidence.idempotencyKey, operation_id: evidence.operationId,
    });
    const commands: { lookup?: string; wait?: string } = {};
    if (valid.idempotencyKey !== undefined)
        commands.lookup = `hfcache --json operations lookup -- '${valid.idempotencyKey}'`;
    if (valid.operationId !== undefined)
        commands.wait = `hfcache --json operations wait -- ${valid.operationId}`;
    return commands;
}

const OBSERVATION_CODES = new Set(['HFAPI013', 'HFAPI015', 'HFAPI019', 'HFAPI020']);

/* Exit codes map to UI states, not to a generic error toast
 * (docs/cockpit.md §4; docs/cli.md §3). */
export function classifyEnvelope(envelope: Envelope): ResultKind {
    if (envelope.exit_code !== 0 && (operationEvidence(envelope).workMayContinue ||
        envelope.errors.some(issue => OBSERVATION_CODES.has(issue.code))))
        return 'observation';
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
        guidance: 'Review the request, API credential and configuration. Refresh policy or preview ' +
            'evidence before submitting a corrected request; retain any operation handles.',
    },
    20: {
        title: 'Safety refusal',
        guidance: 'Read the reported safety condition. The single-writer lock (AD-17) is a benign ' +
            'busy case. A stopped or unavailable observer does not prove execution stopped.',
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
