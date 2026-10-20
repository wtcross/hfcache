/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Bounded, offline investigation fixture for CPR-001's reviewed baseline.
 * Run before the owning repairs with:
 *   rtk node --experimental-strip-types docs/agents/plans/support/cockpit-rest-repair/baseline-reproduce.ts
 * This is not a default test, installed-host diagnosis, or component acceptance.
 * It imports the actual runner/pipeline; F05 only evaluates the exact baseline
 * component predicate, and tab evidence is explicitly a source inspection.
 */

import { readFileSync } from 'node:fs';

import { prepareConfiguration } from '../../../../../cockpit/src/lib/config-pipeline.ts';
import type { ConfigurationPorts } from '../../../../../cockpit/src/lib/config-pipeline.ts';
import { classifyEnvelope } from '../../../../../cockpit/src/lib/envelope.ts';
import type { Envelope } from '../../../../../cockpit/src/lib/envelope.ts';
import { runSpawned } from '../../../../../cockpit/src/lib/runner.ts';
import type { StreamProcess } from '../../../../../cockpit/src/lib/runner.ts';

const REVIEWED_BASELINE = 'dcc2c562b52304541d0cb85d20fc046072038e79';
const CONFIG = 'schema_version=1\n';
const KEY = 'synthetic-original-key';
const ID = 'b'.repeat(32);

function emit(value: Record<string, unknown>): void {
    const output = JSON.stringify(value);
    if (Buffer.byteLength(output, 'utf8') > 2048)
        throw new Error('Investigation output exceeds its bound');
    console.log(output);
}

function message(error: unknown): string {
    return error instanceof Error ? error.message.slice(0, 256) : 'non-Error rejection';
}

function noOutput(failure: unknown): StreamProcess {
    return Object.assign(Promise.reject(failure), { stream: () => undefined });
}

function failedValidation(): Envelope {
    return {
        schema_version: 1,
        command: 'config validate',
        run_id: 'a'.repeat(32),
        started_at: '2026-10-19T12:00:00.000000Z',
        completed_at: '2026-10-19T12:00:01.000000Z',
        exit_code: 10,
        outcome: 'failed',
        data: {},
        warnings: [],
        errors: [{ code: 'HFAPI003', message: 'Synthetic API refusal', repository: null }],
    };
}

emit({ fixture: 'CPR-001 offline baseline investigation', reviewedBaseline: REVIEWED_BASELINE });

for (const plain of [false, true]) {
    const fields = { problem: 'reconnected', exit_status: 17, exit_signal: 'TERM' };
    const failure = plain
        ? { message: 'reconnected', ...fields }
        : Object.assign(new Error('reconnected'), fields);
    try {
        await runSpawned(['synthetic-fixed-client'], () => noOutput(failure));
        emit({ finding: 'F01', input: plain ? 'plain object' : 'Error', result: 'unexpected resolution' });
    } catch (error) {
        const retained = error as Record<string, unknown>;
        emit({
            finding: 'F01', input: plain ? 'plain object' : 'Error',
            message: message(error), problem: retained.problem ?? null,
            exit_status: retained.exit_status ?? null, exit_signal: retained.exit_signal ?? null,
            workMayContinue: retained.workMayContinue ?? null,
        });
    }
}

const validation = failedValidation();
const calls: string[] = [];
const ports: ConfigurationPorts = {
    write: async () => { calls.push('write') },
    validate: async () => { calls.push('validate'); return validation },
    preview: async () => { calls.push('preview'); throw new Error('Preview must not run after refusal') },
    install: async () => { throw new Error('Investigation must never install') },
    confirm: async () => { throw new Error('Investigation must never confirm installation') },
};
try {
    const result = await prepareConfiguration({ installedContent: CONFIG, candidateContent: CONFIG }, ports);
    emit({ finding: 'F02', result: 'returned preparation', calls, blocked: result.blocked });
} catch (error) {
    emit({ finding: 'F02', message: message(error), calls, originalCode: validation.errors[0]?.code });
}

// This deliberately mirrors maintenance.tsx's baseline predicate, not its UI.
const dryRun: Envelope = { ...validation, command: 'prune', exit_code: 0, outcome: 'success', errors: [] };
const applied: Envelope | null = null;
const error = Object.assign(new Error('reconnected'), {
    idempotencyKey: KEY, operationId: ID, workMayContinue: true,
});
const uncertain = [dryRun, applied].some(result => result !== null && classifyEnvelope(result) === 'observation');
const canApply = !uncertain && dryRun !== null && classifyEnvelope(dryRun) === 'success';
emit({
    finding: 'F05', evidenceLayer: 'exact baseline predicate only; no mounted component',
    caughtErrorRetainsKey: error.idempotencyKey === KEY,
    caughtErrorRetainsOperation: error.operationId === ID, uncertain, canApply,
});

const source = (relative: string): string => readFileSync(new URL(relative, import.meta.url), 'utf8');
const app = source('../../../../../cockpit/src/app.tsx');
const hooks = source('../../../../../cockpit/src/hooks.ts');
const maintenance = source('../../../../../cockpit/src/maintenance.tsx');
emit({
    finding: 'F04', evidenceLayer: 'source checks only; no mounted component lifecycle',
    tabsMountOnEnter: /\bmountOnEnter\b/.test(app),
    tabsUnmountOnExit: /\bunmountOnExit\b/.test(app),
    handlesAreHookLocalState: /useState<OperationEvidence>\(\{ workMayContinue: false \}\)/.test(hooks),
    applyPredicateMatchesBaseline: maintenance.includes(
        "const uncertain = [dryRun, applied].some(result => result !== null && classifyEnvelope(result) === 'observation');",
    ) && maintenance.includes(
        "const canApply = !uncertain && dryRun !== null && classifyEnvelope(dryRun) === 'success';",
    ),
});
