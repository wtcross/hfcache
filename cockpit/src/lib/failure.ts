/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Bounded host-boundary evidence. Untrusted messages and diagnostic output are
 * never presentation authority; terminal API/domain Envelopes remain separate.
 */

export const FAILURE_STAGES = [
    'installed-read', 'candidate-write', 'candidate-validate', 'candidate-preview',
    'install', 'installed-confirm', 'installed-validate', 'operation-lookup',
    'operation-wait', 'operation-observe', 'api-read', 'unit-read', 'unit-mutation',
    'schedule-read', 'schedule-validate', 'schedule-write', 'profile-read', 'journal-read',
] as const;

export type FailureStage = typeof FAILURE_STAGES[number];
export type FailureCategory = 'access' | 'bridge' | 'launcher' | 'process' | 'protocol' | 'observation';
export type FailureReason = 'no-envelope' | 'terminal-overflow' | 'unsupported-schema' |
    'invalid-envelope' | 'process-postcheck';

export interface FailureContext {
    stage?: FailureStage;
    reason?: FailureReason;
    idempotencyKey?: string;
    operationId?: string;
    workMayContinue?: boolean;
    hostMutationUncertain?: boolean;
}

const STAGE_LABELS: Record<FailureStage, string> = {
    'installed-read': 'installed configuration read',
    'candidate-write': 'candidate write',
    'candidate-validate': 'candidate validation',
    'candidate-preview': 'candidate preview',
    install: 'configuration installation',
    'installed-confirm': 'installed configuration confirmation',
    'installed-validate': 'installed configuration validation',
    'operation-lookup': 'original operation lookup',
    'operation-wait': 'original operation wait',
    'operation-observe': 'operation observation',
    'api-read': 'API read',
    'unit-read': 'system unit read',
    'unit-mutation': 'system unit change',
    'schedule-read': 'schedule read',
    'schedule-validate': 'schedule validation',
    'schedule-write': 'schedule write',
    'profile-read': 'host profile inspection',
    'journal-read': 'optional host journal read',
};

const REASONS = new Set<FailureReason>([
    'no-envelope', 'terminal-overflow', 'unsupported-schema', 'invalid-envelope', 'process-postcheck',
]);
const ACCESS_PROBLEMS = new Set(['access-denied', 'authentication-failed', 'permission-denied', 'not-authorized']);
const BRIDGE_PROBLEMS = new Set(['reconnected', 'disconnected', 'terminated', 'no-session', 'timeout']);
const LAUNCHER_PROBLEMS = new Set(['not-found', 'no-cockpit', 'no-bridge', 'not-supported']);
const KNOWN_PROBLEMS = new Set([
    ...ACCESS_PROBLEMS, ...BRIDGE_PROBLEMS, ...LAUNCHER_PROBLEMS,
    'protocol-error', 'internal-error', 'cancelled',
]);
const SIGNALS = new Set([
    'ABRT', 'ALRM', 'BUS', 'CHLD', 'CLD', 'CONT', 'FPE', 'HUP', 'ILL', 'INT', 'IO', 'IOT',
    'KILL', 'PIPE', 'POLL', 'PROF', 'PWR', 'QUIT', 'SEGV', 'STKFLT', 'STOP', 'SYS', 'TERM',
    'TRAP', 'TSTP', 'TTIN', 'TTOU', 'URG', 'USR1', 'USR2', 'VTALRM', 'WINCH', 'XCPU', 'XFSZ',
]);
const HOST_MUTATIONS = new Set<FailureStage>([
    'candidate-write', 'install', 'installed-confirm', 'unit-mutation', 'schedule-write',
]);
const NORMALIZED = new WeakSet<object>();

/* Only own data fields are evidence. Do not invoke arbitrary getters, toString,
 * stringify an exception, retain its cause, or enumerate its other properties. */
function field(value: unknown, name: string): unknown {
    if (typeof value !== 'object' || value === null)
        return undefined;
    try {
        return Object.getOwnPropertyDescriptor(value, name)?.value;
    } catch {
        return undefined;
    }
}

function stage(value: unknown): FailureStage | undefined {
    return typeof value === 'string' && FAILURE_STAGES.includes(value as FailureStage)
        ? value as FailureStage
        : undefined;
}

function reason(value: unknown): FailureReason | undefined {
    return REASONS.has(value as FailureReason) ? value as FailureReason : undefined;
}

function key(value: unknown): string | undefined {
    return typeof value === 'string' && /^[A-Za-z0-9._~+-]{1,128}$/.test(value) ? value : undefined;
}

function operation(value: unknown): string | undefined {
    return typeof value === 'string' && /^[0-9a-f]{32}$/.test(value) ? value : undefined;
}

function status(value: unknown): number | undefined {
    return typeof value === 'number' && Number.isInteger(value) && value >= 0 && value <= 255
        ? value
        : undefined;
}

function signal(value: unknown): number | string | undefined {
    if (typeof value === 'number')
        return Number.isInteger(value) && value >= 1 && value <= 64 ? value : undefined;
    if (typeof value !== 'string' || value.length > 10)
        return undefined;
    return SIGNALS.has(value.startsWith('SIG') ? value.slice(3) : value) ? value : undefined;
}

function problem(value: unknown): string | undefined {
    if (typeof value !== 'string' || value === '')
        return undefined;
    // Unknown identifiers may themselves be credentials. Preserve their presence,
    // never their arbitrary contents (even if short and syntactically harmless).
    return value.length <= 64 && KNOWN_PROBLEMS.has(value) ? value : 'unknown';
}

function legacyProblem(value: unknown): string | undefined {
    // Compatibility for the historical Error("reconnected") shape only. This
    // exact finite marker is evidence; arbitrary exception prose is never read.
    return value === 'reconnected' ? 'reconnected' : undefined;
}

function category(problem_: string | undefined, exitStatus: number | undefined,
    exitSignal: string | number | undefined, reason_: FailureReason): FailureCategory {
    if (problem_ !== undefined && ACCESS_PROBLEMS.has(problem_))
        return 'access';
    if (problem_ !== undefined && BRIDGE_PROBLEMS.has(problem_))
        return 'bridge';
    if (problem_ !== undefined && LAUNCHER_PROBLEMS.has(problem_))
        return 'launcher';
    if (exitStatus !== undefined || exitSignal !== undefined || reason_ === 'process-postcheck')
        return 'process';
    if (reason_ !== 'no-envelope' || problem_ === 'protocol-error')
        return 'protocol';
    return 'observation';
}

interface FailureFacts {
    stage: FailureStage;
    reason: FailureReason;
    category: FailureCategory;
    problem: string | undefined;
    exitStatus: number | undefined;
    exitSignal: string | number | undefined;
    idempotencyKey: string | undefined;
    operationId: string | undefined;
    workMayContinue: boolean;
    hostMutationUncertain: boolean;
}

function facts(failure: unknown, context: FailureContext): FailureFacts {
    // Weak identity avoids invoking an untrusted Proxy's prototype traps and
    // distinguishes real normalized values from forged Error prototypes.
    const previous = typeof failure === 'object' && failure !== null && NORMALIZED.has(failure)
        ? failure as BoundaryError
        : undefined;
    const stage_ = stage(context.stage) ?? previous?.stage ?? 'api-read';
    const reason_ = reason(context.reason) ?? previous?.reason ?? 'no-envelope';
    const problem_ = previous?.problem ?? problem(field(failure, 'problem')) ?? legacyProblem(field(failure, 'message'));
    const exitStatus = previous?.exitStatus ?? status(field(failure, 'exit_status'));
    const exitSignal = previous?.exitSignal ?? signal(field(failure, 'exit_signal'));
    const idempotencyKey = key(context.idempotencyKey) ?? previous?.idempotencyKey;
    const operationId = operation(context.operationId) ?? previous?.operationId;
    return {
        stage: stage_,
        reason: reason_,
        category: previous?.category ?? category(problem_, exitStatus, exitSignal, reason_),
        problem: problem_,
        exitStatus,
        exitSignal,
        idempotencyKey,
        operationId,
        workMayContinue: previous?.workMayContinue === true || context.workMayContinue === true ||
            idempotencyKey !== undefined || operationId !== undefined,
        hostMutationUncertain: previous?.hostMutationUncertain === true ||
            (context.hostMutationUncertain ?? previous?.hostMutationUncertain ?? HOST_MUTATIONS.has(stage_)),
    };
}

function message(details: FailureFacts): string {
    const during = ` during ${STAGE_LABELS[details.stage]}.`;
    let text: string;
    switch (details.category) {
    case 'access': text = 'Administrative access is unavailable' + during; break;
    case 'bridge':
        text = (details.problem === 'reconnected'
            ? 'Cockpit connection changed'
            : 'Cockpit bridge communication stopped') + during;
        break;
    case 'launcher': text = 'The fixed hfcache client could not start' + during; break;
    case 'process': text = 'The host process failed' + during; break;
    case 'protocol':
        text = details.reason === 'unsupported-schema'
            ? 'This terminal Envelope schema is unsupported; update the plugin to match the deployed hfcache.'
            : details.reason === 'terminal-overflow'
                ? 'Terminal result exceeds the observation limit' + during
                : 'No valid terminal Envelope was observed' + during;
        break;
    case 'observation':
        text = (['installed-read', 'candidate-write', 'install', 'unit-read', 'unit-mutation', 'journal-read',
            'schedule-read', 'schedule-validate', 'schedule-write'].includes(details.stage)
            ? 'The host action could not be observed'
            : 'No terminal Envelope was observed') + during;
        break;
    }
    if (details.reason === 'process-postcheck')
        text += ' Installed confirmation did not complete successfully; reload and validate again.';
    if (details.hostMutationUncertain)
        text += ' The host change may have completed. Inspect the guarded state before another change.';
    if (details.workMayContinue)
        text += ' Accepted server work may continue. Preserve the original handles and observe that operation before another submission.';
    else if (details.stage === 'candidate-validate' || details.stage === 'installed-validate')
        text += ' Validation has no operation receipt. Reconnect and explicitly revalidate the captured configuration.';
    return text;
}

export class BoundaryError extends Error {
    readonly stage: FailureStage;
    readonly reason: FailureReason;
    readonly category: FailureCategory;
    readonly problem: string | undefined;
    readonly exitStatus: number | undefined;
    readonly exitSignal: string | number | undefined;
    readonly idempotencyKey: string | undefined;
    readonly operationId: string | undefined;
    readonly workMayContinue: boolean;
    readonly hostMutationUncertain: boolean;
    readonly safeDiagnostics: readonly string[];

    constructor(failure: unknown, context: FailureContext = {}) {
        const normalized = facts(failure, context);
        super(message(normalized));
        this.name = 'BoundaryError';
        this.stage = normalized.stage;
        this.reason = normalized.reason;
        this.category = normalized.category;
        this.problem = normalized.problem;
        this.exitStatus = normalized.exitStatus;
        this.exitSignal = normalized.exitSignal;
        this.idempotencyKey = normalized.idempotencyKey;
        this.operationId = normalized.operationId;
        this.workMayContinue = normalized.workMayContinue;
        this.hostMutationUncertain = normalized.hostMutationUncertain;
        this.safeDiagnostics = Object.freeze([
            ...(this.problem === undefined
                ? []
                : [this.problem === 'unknown'
                    ? 'Cockpit problem: unrecognized value (withheld)'
                    : `Cockpit problem: ${this.problem}`]),
            ...(this.exitStatus === undefined ? [] : [`Process exit status: ${this.exitStatus}`]),
            ...(this.exitSignal === undefined ? [] : [`Process exit signal: ${this.exitSignal}`]),
        ]);
        NORMALIZED.add(this);
    }
}

/* Defaults to a read boundary; adapters supply the known stage and mutation
 * uncertainty. Rewrapping preserves original classified facts and uncertainty. */
export function normalizeFailure(failure: unknown, context: FailureContext = {}): BoundaryError {
    return new BoundaryError(failure, context);
}
