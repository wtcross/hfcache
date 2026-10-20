/* SPDX-License-Identifier: LGPL-2.1-or-later
 * One bounded editor session in application memory. Never browser storage.
 * Async observation survives tab unmount; a full reload owns no staged file.
 */
import type { ConfigDocument } from './config.ts';
import type { CandidateGuard, CandidateInspection } from './candidate-guard.ts';
import type { CandidatePreparation, CandidateProposal, ConfigurationEvidence } from './config-pipeline.ts';
import type { Envelope } from './envelope.ts';

export interface ConfigurationState {
    initialized: boolean;
    loading: boolean;
    installedText: string | null;
    loadError: Error | null;
    mode: 'form' | 'text';
    document: ConfigDocument | null;
    text: string;
    fieldErrors: Record<string, string>;
    phase: 'idle' | 'checking' | 'ready' | 'installing' | 'confirming' | 'inspecting' | 'discarding' | 'done';
    validation: Envelope | null;
    plan: Envelope | null;
    confirmation: Envelope | null;
    fingerprint: string | null;
    pipelineError: Error | null;
    reconciliationError: Error | null;
    localError: string | null;
    preparation: CandidatePreparation | null;
    proposal: CandidateProposal | null;
    diskGuard: Readonly<CandidateGuard> | null;
    uncertainty: 'candidate' | 'install' | null;
    previewUncertain: boolean;
    inspection: CandidateInspection | null;
    inspectedGeneration: number | null;
    confirmed: boolean;
    generation: number | null;
    connectionChanged: boolean;
    draftRevision: number;
    guardRevision: number | null;
    evidence: readonly ConfigurationEvidence[];
}

export function createConfigurationSession() {
    let state: ConfigurationState = {
        initialized: false,
        loading: false,
        installedText: null,
        loadError: null,
        mode: 'form',
        document: null,
        text: '',
        fieldErrors: {},
        phase: 'idle',
        validation: null,
        plan: null,
        confirmation: null,
        fingerprint: null,
        pipelineError: null,
        reconciliationError: null,
        localError: null,
        preparation: null,
        proposal: null,
        diskGuard: null,
        uncertainty: null,
        previewUncertain: false,
        inspection: null,
        inspectedGeneration: null,
        confirmed: false,
        generation: null,
        connectionChanged: false,
        draftRevision: 0,
        guardRevision: null,
        evidence: [],
    };
    const listeners = new Set<() => void>();
    return {
        snapshot: () => state,
        subscribe: (listener: () => void) => {
            listeners.add(listener);
            return () => { listeners.delete(listener) };
        },
        patch: (patch: Partial<ConfigurationState>) => {
            state = { ...state, ...patch };
            for (const listener of listeners)
                listener();
        },
    };
}

export type ConfigurationSession = ReturnType<typeof createConfigurationSession>;
export const configurationSession = createConfigurationSession();
