/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Candidate syntax, installed authority and installation are separate (ADR122).
 * Pure injected ports keep the real privilege boundary independently testable.
 */

import type { CandidateGuard } from './candidate-guard.ts';
import { validateCandidateText } from './candidate-guard.ts';
import { parseConfig, selectorsNeedingPreview } from './config.ts';
import type { ConfigDocument } from './config.ts';
import { isFullCommitSha } from './command.ts';
import type { Envelope } from './envelope.ts';
import type { OperationNotice } from './events.ts';
import { normalizeFailure } from './failure.ts';
import type { BoundaryError, FailureReason } from './failure.ts';

const FINGERPRINT = /^[0-9a-f]{64}$/;
const AUTHORITY_FIELDS = new Set([
    'storage.archive_root', 'storage.archive_id', 'hub.endpoint', 'hub.token_mode',
    'hub.expected_account', 'hub.credential_name',
]);

export interface CandidateAssessment {
    syntaxValid: boolean;
    compatible: boolean | null;
    installedPolicyValid: boolean;
    mismatches: string[];
    fingerprint: string | null;
}

export const MANUAL_AUTHORITY_GUIDANCE =
    'The plugin cannot install a candidate with changed or unknown writer authority. ' +
    'An operator must review and install the policy manually, restart the API when its ' +
    'archive root or UUID changes, then validate and obtain a compatible sizing preview ' +
    'before starting synchronization.';

export const UNCONFIRMED_INSTALLATION =
    'Installation may have completed, but installed validation did not confirm the expected document and operational fingerprint. ' +
    'Inspect the captured bytes and backup, confirm the installed configuration, then acknowledge the confirmed installation before preparing another change.';

function record(value: unknown): Record<string, unknown> {
    if (typeof value !== 'object' || value === null || Array.isArray(value))
        throw new Error('Configuration validation evidence is incompatible; update the CLI and plugin');
    return value as Record<string, unknown>;
}

export function candidateAssessment(envelope: Envelope): CandidateAssessment {
    const data = record(envelope.data);
    if (envelope.command !== 'config validate' || typeof data.valid !== 'boolean' ||
        typeof data.syntax_valid !== 'boolean' || typeof data.installed_policy_valid !== 'boolean' ||
        !(data.authority_compatible === null || typeof data.authority_compatible === 'boolean') ||
        !Array.isArray(data.authority_mismatches) ||
        !data.authority_mismatches.every(field => typeof field === 'string' && AUTHORITY_FIELDS.has(field)) ||
        new Set(data.authority_mismatches).size !== data.authority_mismatches.length ||
        data.valid !== data.syntax_valid || (envelope.exit_code === 0) !== data.valid)
        throw new Error('Configuration validation evidence is incompatible; update the CLI and plugin');
    const syntaxValid = data.syntax_valid;
    const fingerprint = typeof data.config_fingerprint === 'string' && FINGERPRINT.test(data.config_fingerprint)
        ? data.config_fingerprint
        : null;
    const compatible = data.authority_compatible;
    const installedPolicyValid = data.installed_policy_valid;
    const mismatches = data.authority_mismatches as string[];
    if ((syntaxValid && fingerprint === null) ||
        (!syntaxValid && (compatible !== null || mismatches.length > 0)) ||
        (syntaxValid && !installedPolicyValid && (compatible !== null || mismatches.length > 0)) ||
        (syntaxValid && installedPolicyValid && (compatible === null || compatible !== (mismatches.length === 0))))
        throw new Error('Configuration validation evidence is inconsistent; reload and validate again');
    return { syntaxValid, compatible, installedPolicyValid, mismatches, fingerprint };
}

export interface CandidateProposal {
    guard: CandidateGuard;
    fingerprint: string;
}

export interface CandidatePreparation {
    validation: Envelope;
    assessment: CandidateAssessment | null;
    plan: Envelope | null;
    proposal: CandidateProposal | null;
    blocked: 'request' | 'invalid' | 'authority' | 'preview' | null;
}

export type ConfigurationStage = 'candidate-write' | 'candidate-validate' | 'candidate-preview' |
    'install' | 'installed-confirm';

interface ConfigurationEvidenceBase {
    guard: Readonly<CandidateGuard>;
    acknowledgedStages: readonly ConfigurationStage[];
}

type ConfigurationTransition =
    { stage: ConfigurationStage; status: 'started' | 'acknowledged' } |
    { stage: 'candidate-validate' | 'candidate-preview' | 'installed-confirm'; status: 'result';
        envelope: Envelope } |
    { stage: 'candidate-preview'; status: 'notice';
        notice: Extract<OperationNotice, { kind: 'key' | 'operation' }> } |
    { stage: ConfigurationStage; status: 'failed'; error: BoundaryError | null; envelope: Envelope | null };

export type ConfigurationEvidence = ConfigurationEvidenceBase & ConfigurationTransition;

export interface ConfigurationOptions {
    /* Only explicit revalidation after exact guarded inspection may skip write. */
    skipWrite?: boolean;
    isCurrent?: () => boolean;
    onEvidence?: (evidence: ConfigurationEvidence) => void;
    onPreviewNotice?: (notice: OperationNotice) => void;
}

export interface ConfigurationPorts {
    write: (guard: CandidateGuard) => Promise<void>;
    validate: (guard: CandidateGuard) => Promise<Envelope>;
    preview: (selectors: string[], guard: CandidateGuard,
        onNotice?: (notice: OperationNotice) => void) => Promise<Envelope>;
    install: (guard: CandidateGuard) => Promise<void>;
    confirm: (expected: string) => Promise<Envelope>;
}

/* Boundary causes are already safe and classified. An authentic failed terminal
 * result has no boundary cause: retain its Envelope rather than inventing one.
 * Exact drafts are session memory only and must never enter browser storage. */
export class ConfigurationPipelineError extends Error {
    readonly cause: BoundaryError | null;
    readonly stage: ConfigurationStage;
    readonly guard: Readonly<CandidateGuard>;
    readonly proposal: Readonly<CandidateProposal> | null;
    readonly envelope: Envelope | null;
    readonly acknowledgedStages: readonly ConfigurationStage[];

    constructor(stage: ConfigurationStage, guard: Readonly<CandidateGuard>,
        acknowledgedStages: readonly ConfigurationStage[], cause: BoundaryError | null,
        envelope: Envelope | null = null, proposal: Readonly<CandidateProposal> | null = null) {
        super(cause?.message ?? 'Installed configuration validation returned a failed result.');
        this.name = 'ConfigurationPipelineError';
        this.cause = cause;
        this.stage = stage;
        this.guard = guard;
        this.proposal = proposal;
        this.envelope = envelope;
        this.acknowledgedStages = Object.freeze([...acknowledgedStages]);
    }
}

export class PreparationSuperseded extends Error {
    constructor() {
        super('Candidate changed during validation; validate the current draft again');
    }
}

export async function prepareConfiguration(
    guard: CandidateGuard, ports: ConfigurationPorts,
    isCurrent: () => boolean = () => true,
    options: ConfigurationOptions = {},
): Promise<CandidatePreparation> {
    const current = () => {
        if (!isCurrent() || options.isCurrent?.() === false)
            throw new PreparationSuperseded();
    };
    validateCandidateText(guard.candidateContent);
    validateCandidateText(guard.installedContent, true);
    const captured = Object.freeze({ ...guard });
    const evidence = configurationEvidence(captured, options);
    current();
    if (options.skipWrite !== true)
        await evidence.invoke('candidate-write', () => ports.write(captured));
    current();
    const validation = await evidence.result('candidate-validate', () => ports.validate(captured));
    current();
    // API/authentication/client refusals need not contain candidate assessment
    // data. Their exact failed Envelope remains the presentation authority.
    if (validation.exit_code !== 0 && !hasCandidateAssessment(validation))
        return { validation, assessment: null, plan: null, proposal: null, blocked: 'request' };
    let assessment: CandidateAssessment;
    try {
        assessment = candidateAssessment(validation);
    } catch (error) {
        throw evidence.failure('candidate-validate', error, validation, 'invalid-envelope');
    }
    if (!assessment.syntaxValid)
        return { validation, assessment, plan: null, proposal: null, blocked: 'invalid' };
    if (assessment.compatible !== true || !assessment.installedPolicyValid)
        return { validation, assessment, plan: null, proposal: null, blocked: 'authority' };
    let selectors: string[];
    let candidate: ConfigDocument;
    try {
        candidate = parseConfig(captured.candidateContent);
        selectors = selectorsNeedingPreview(parseConfig(captured.installedContent), candidate);
    } catch (error) {
        throw evidence.failure('candidate-preview', error, null, 'invalid-envelope');
    }
    const plan = selectors.length > 0
        ? await evidence.result('candidate-preview', () => ports.preview(selectors, captured, notice => {
            evidence.notice(notice);
            // Display callbacks cannot turn an admitted preview into a retry.
            try { options.onPreviewNotice?.(notice) } catch { /* Observation remains attached. */ }
        }))
        : null;
    current();
    if (plan !== null && (plan.command !== 'plan' || plan.exit_code !== 0))
        return { validation, assessment, plan, proposal: null, blocked: 'preview' };
    if (plan !== null) {
        try { confirmedPreview(plan, selectors, candidate) } catch (error) {
            throw evidence.failure('candidate-preview', error, plan, 'invalid-envelope');
        }
    }
    if (assessment.fingerprint === null)
        throw new Error('Candidate fingerprint is missing');
    return {
        validation,
        assessment,
        plan,
        proposal: Object.freeze({ guard: captured, fingerprint: assessment.fingerprint }),
        blocked: null,
    };
}

/* A required preview proves complete sizing for precisely the captured request.
 * Partial/nonzero plans bypass this success-only check and remain exact results.
 * The array is bounded by the requested set from the <=1 MiB candidate. */
function confirmedPreview(envelope: Envelope, selectors: string[], candidate: ConfigDocument): void {
    const fail = (): never => { throw new Error('Sizing preview evidence is incompatible with the captured candidate') };
    const data = record(envelope.data);
    if (!Array.isArray(data.repositories) || data.repositories.length === 0 ||
        data.repositories.length !== selectors.length)
        fail();
    const wanted = new Set(selectors);
    const configured = new Map((candidate.repositories ?? []).map(entry => [`${entry.type}:${entry.id}`, entry]));
    const seen = new Set<string>();
    const mode = candidate.storage === undefined ? 'hardlink' : record(candidate.storage).publication_mode ?? 'hardlink';
    if (wanted.size !== selectors.length || (mode !== 'hardlink' && mode !== 'copy'))
        fail();
    for (const value of data.repositories as unknown[]) {
        const row = record(value);
        const selector = `${row.repository_type}:${row.repository_id}`;
        const expected = configured.get(selector);
        const requestedRevision = expected?.revision ?? 'main';
        if (!wanted.has(selector) || seen.has(selector) || expected === undefined ||
            row.repository_type !== expected.type || row.repository_id !== expected.id ||
            row.enabled !== true || row.requested_revision !== requestedRevision ||
            typeof row.resolved_commit_sha !== 'string' || !isFullCommitSha(row.resolved_commit_sha) ||
            (isFullCommitSha(requestedRevision) && row.resolved_commit_sha !== requestedRevision) ||
            row.upstream_state !== 'available' || row.publication_mode !== mode)
            fail();
        for (const field of ['file_count', 'logical_bytes', 'estimated_new_bytes', 'projected_publication_bytes']) {
            if (typeof row[field] !== 'number' || !Number.isSafeInteger(row[field]) || row[field] < 0)
                fail();
        }
        if (row.projected_publication_bytes !== (mode === 'hardlink' ? 0 : row.logical_bytes))
            fail();
        seen.add(selector);
    }
}

export function confirmedFingerprint(envelope: Envelope, expected: string): string {
    const data = record(envelope.data);
    if (envelope.command !== 'config validate' || envelope.exit_code !== 0 ||
        !FINGERPRINT.test(expected) || data.config_fingerprint !== expected)
        throw new Error('Installed validation did not confirm the expected configuration fingerprint');
    return expected;
}

export async function installConfiguration(
    proposal: CandidateProposal, ports: Pick<ConfigurationPorts, 'install' | 'confirm'>,
    options: ConfigurationOptions = {},
): Promise<{ envelope: Envelope; fingerprint: string }> {
    if (!FINGERPRINT.test(proposal.fingerprint))
        throw new Error('Validated candidate fingerprint is missing');
    const captured = captureProposal(proposal);
    const evidence = configurationEvidence(captured.guard, options, captured);
    if (options.isCurrent?.() === false)
        throw new PreparationSuperseded();
    await evidence.invoke('install', () => ports.install(captured.guard));
    return confirmCapturedConfiguration(captured, ports, options, evidence);
}

/* Explicit observation after guarded reconciliation. It never writes, renames,
 * rolls back or removes anything, and cannot restore a prior install proposal. */
export async function confirmConfiguration(
    proposal: CandidateProposal, ports: Pick<ConfigurationPorts, 'confirm'>,
    options: ConfigurationOptions = {},
): Promise<{ envelope: Envelope; fingerprint: string }> {
    if (!FINGERPRINT.test(proposal.fingerprint))
        throw new Error('Validated candidate fingerprint is missing');
    const captured = captureProposal(proposal);
    return confirmCapturedConfiguration(captured, ports, options,
                                        configurationEvidence(captured.guard, options, captured));
}

function captureProposal(proposal: CandidateProposal): Readonly<CandidateProposal> {
    validateCandidateText(proposal.guard.candidateContent);
    validateCandidateText(proposal.guard.installedContent, true);
    return Object.freeze({ guard: Object.freeze({ ...proposal.guard }), fingerprint: proposal.fingerprint });
}

function hasCandidateAssessment(envelope: Envelope): boolean {
    const data = envelope.data;
    return typeof data === 'object' && data !== null && !Array.isArray(data) &&
        ['syntax_valid', 'authority_compatible', 'authority_mismatches', 'installed_policy_valid']
                .some(field => Object.prototype.hasOwnProperty.call(data, field));
}

function configurationEvidence(guard: Readonly<CandidateGuard>, options: ConfigurationOptions,
    proposal: Readonly<CandidateProposal> | null = null) {
    const acknowledgedStages: ConfigurationStage[] = [];
    const receipts = new Set<string>();
    const publish = (evidence: ConfigurationTransition) => {
        // Evidence/display failures do not cancel or replay host actions.
        try {
            options.onEvidence?.({ ...evidence, guard, acknowledgedStages: Object.freeze([...acknowledgedStages]) });
        } catch { /* Keep observing the original invocation. */ }
    };
    const failure = (stage: ConfigurationStage, error: unknown, envelope: Envelope | null = null,
        reason?: FailureReason): ConfigurationPipelineError => {
        const cause = error === null
            ? null
            : normalizeFailure(error, {
                stage, ...(reason === undefined ? {} : { reason }),
            });
        publish({ stage, status: 'failed', error: cause, envelope });
        return new ConfigurationPipelineError(stage, guard, acknowledgedStages, cause, envelope, proposal);
    };
    const invoke = async <T>(stage: ConfigurationStage, action: () => Promise<T>): Promise<T> => {
        publish({ stage, status: 'started' });
        try {
            const result = await action();
            acknowledgedStages.push(stage);
            publish({ stage, status: 'acknowledged' });
            return result;
        } catch (error) {
            throw failure(stage, error);
        }
    };
    const result = async (stage: 'candidate-validate' | 'candidate-preview' | 'installed-confirm',
        action: () => Promise<Envelope>): Promise<Envelope> => {
        const envelope = await invoke(stage, action);
        // Publish before checking whether a newer draft/session superseded us:
        // negative results and already-started failures remain useful evidence.
        publish({ stage, status: 'result', envelope });
        return envelope;
    };
    const notice = (notice: OperationNotice): void => {
        if (((notice.kind === 'key' && /^[A-Za-z0-9._~+-]{1,128}$/.test(notice.key)) ||
            (notice.kind === 'operation' && /^[0-9a-f]{32}$/.test(notice.operationId))) &&
            !receipts.has(notice.kind)) {
            receipts.add(notice.kind);
            publish({ stage: 'candidate-preview', status: 'notice', notice: Object.freeze({ ...notice }) });
        }
    };
    return { invoke, result, failure, notice };
}

async function confirmCapturedConfiguration(
    proposal: Readonly<CandidateProposal>, ports: Pick<ConfigurationPorts, 'confirm'>,
    options: ConfigurationOptions, evidence: ReturnType<typeof configurationEvidence>,
): Promise<{ envelope: Envelope; fingerprint: string }> {
    if (options.isCurrent?.() === false)
        throw evidence.failure('installed-confirm', { problem: 'reconnected' });
    const envelope = await evidence.result('installed-confirm', () => ports.confirm(proposal.guard.candidateContent));
    if (envelope.exit_code !== 0)
        throw evidence.failure('installed-confirm', null, envelope);
    if (options.isCurrent?.() === false)
        throw evidence.failure('installed-confirm', { problem: 'reconnected' }, envelope);
    try {
        return { envelope, fingerprint: confirmedFingerprint(envelope, proposal.fingerprint) };
    } catch (error) {
        throw evidence.failure('installed-confirm', error, envelope, 'invalid-envelope');
    }
}
