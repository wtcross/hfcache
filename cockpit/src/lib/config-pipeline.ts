/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Candidate syntax, installed authority and installation are separate (ADR122).
 * Pure injected ports keep the real privilege boundary independently testable.
 */

import type { CandidateGuard } from './candidate-guard.ts';
import { validateCandidateText } from './candidate-guard.ts';
import { parseConfig, selectorsNeedingPreview } from './config.ts';
import type { Envelope } from './envelope.ts';

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
    'Reload and validate the installed configuration before another operation.';

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
    assessment: CandidateAssessment;
    plan: Envelope | null;
    proposal: CandidateProposal | null;
    blocked: 'invalid' | 'authority' | 'preview' | null;
}

export interface ConfigurationPorts {
    write: (guard: CandidateGuard) => Promise<void>;
    validate: (guard: CandidateGuard) => Promise<Envelope>;
    preview: (selectors: string[], guard: CandidateGuard) => Promise<Envelope>;
    install: (guard: CandidateGuard) => Promise<void>;
    confirm: (expected: string) => Promise<Envelope>;
}

export class PreparationSuperseded extends Error {
    constructor() {
        super('Candidate changed during validation; validate the current draft again');
    }
}

export async function prepareConfiguration(
    guard: CandidateGuard, ports: ConfigurationPorts,
    isCurrent: () => boolean = () => true,
): Promise<CandidatePreparation> {
    const current = () => {
        if (!isCurrent())
            throw new PreparationSuperseded();
    };
    validateCandidateText(guard.candidateContent);
    validateCandidateText(guard.installedContent, true);
    const captured = Object.freeze({ ...guard });
    current();
    await ports.write(captured);
    current();
    const validation = await ports.validate(captured);
    current();
    const assessment = candidateAssessment(validation);
    if (!assessment.syntaxValid)
        return { validation, assessment, plan: null, proposal: null, blocked: 'invalid' };
    if (assessment.compatible !== true || !assessment.installedPolicyValid)
        return { validation, assessment, plan: null, proposal: null, blocked: 'authority' };
    const selectors = selectorsNeedingPreview(parseConfig(captured.installedContent), parseConfig(captured.candidateContent));
    const plan = selectors.length > 0 ? await ports.preview(selectors, captured) : null;
    current();
    if (plan !== null && (plan.command !== 'plan' || plan.exit_code !== 0))
        return { validation, assessment, plan, proposal: null, blocked: 'preview' };
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

export function confirmedFingerprint(envelope: Envelope, expected: string): string {
    const data = record(envelope.data);
    if (envelope.command !== 'config validate' || envelope.exit_code !== 0 ||
        !FINGERPRINT.test(expected) || data.config_fingerprint !== expected)
        throw new Error(UNCONFIRMED_INSTALLATION);
    return expected;
}

export async function installConfiguration(
    proposal: CandidateProposal, ports: Pick<ConfigurationPorts, 'install' | 'confirm'>,
): Promise<{ envelope: Envelope; fingerprint: string }> {
    if (!FINGERPRINT.test(proposal.fingerprint))
        throw new Error('Validated candidate fingerprint is missing');
    try {
        await ports.install(proposal.guard);
        const envelope = await ports.confirm(proposal.guard.candidateContent);
        return { envelope, fingerprint: confirmedFingerprint(envelope, proposal.fingerprint) };
    } catch {
        throw new Error(UNCONFIRMED_INSTALLATION);
    }
}
