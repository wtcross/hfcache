/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Offline baseline investigation, mounted in an owned Firefox profile.
 * The actual components, hooks, API adapter and runner execute. Only the bare
 * Cockpit process boundary is replaced; no shell, API or archive is contacted.
 * This is not default regression acceptance or a real Cockpit/PAM session.
 */

import React from '../../../../../cockpit/node_modules/react/index.js';
import { createRoot } from '../../../../../cockpit/node_modules/react-dom/client.js';

import { runHfcache } from '../../../../../cockpit/src/api/hfcache.ts';
import { QueryError } from '../../../../../cockpit/src/components.tsx';
import { Maintenance } from '../../../../../cockpit/src/maintenance.tsx';

const KEY = 'synthetic-original-key';
const ID = 'b'.repeat(32);
const TIMEOUT_MS = 15000;

declare global {
    interface Window {
        cprFixture: {
            spawn: (argv: string[], options: Record<string, unknown>) => unknown;
            calls: string[];
        };
    }
}

function envelope(): string {
    return JSON.stringify({
        schema_version: 1,
        command: 'prune',
        run_id: 'a'.repeat(32),
        started_at: '2026-10-19T12:00:00.000000Z',
        completed_at: '2026-10-19T12:00:01.000000Z',
        exit_code: 0,
        outcome: 'success',
        data: { planned: 0, fixture: 'synthetic dry run' },
        warnings: [],
        errors: [],
    }) + '\n';
}

function bridgeFailure(): Error {
    return Object.assign(new Error('reconnected'), {
        problem: 'reconnected', exit_status: null, exit_signal: null,
    });
}

function invariant(condition: unknown, description: string): asserts condition {
    if (!condition)
        throw new Error(description);
}

function normalizedText(node: Element): string {
    return node.textContent?.replace(/\s+/g, ' ').trim() ?? '';
}

async function until<T>(read: () => T | null | false, description: string): Promise<T> {
    const deadline = performance.now() + TIMEOUT_MS;
    while (performance.now() < deadline) {
        const value = read();
        if (value !== null && value !== false)
            return value;
        await new Promise(resolve => setTimeout(resolve, 20));
    }
    throw new Error('Timed out: ' + description);
}

function button(label: string, within: ParentNode = document): HTMLButtonElement | null {
    return [...within.querySelectorAll('button')].find(node => normalizedText(node) === label) ?? null;
}

function pruneCard(): Element | null {
    return document.querySelector('#maintenance .pf-v6-c-card');
}

function createBoundary(): void {
    const calls: string[] = [];
    const expected = ['prune --dry-run', 'prune --apply', 'config validate'];
    window.cprFixture = {
        calls,
        spawn(argv, options) {
            invariant(argv[0] === 'systemd-run', 'Actual adapter must retain transient systemd launcher');
            const separator = argv.indexOf('--');
            invariant(separator > 0 && argv[separator + 1] === '/usr/local/libexec/hfcache-client',
                      'Actual adapter must retain fixed client helper');
            invariant(argv.includes('--property=User=hfcache') && argv.includes('--property=Group=hfcache'),
                      'Actual adapter must retain service identity');
            invariant(options.superuser === 'require' && options.err === 'out',
                      'Actual adapter must retain privileged merged-stream boundary');
            const json = argv.indexOf('--json', separator);
            invariant(json > separator, 'Actual adapter must request JSON');
            const command = argv.slice(json + 1).join(' ');
            invariant(command === expected[calls.length], 'Unexpected command at controlled process boundary');
            calls.push(command);
            let receive: (chunk: string) => void = () => undefined;
            const completion = new Promise<void>((resolve, reject) => {
                setTimeout(() => {
                    if (command === 'prune --dry-run') {
                        receive(envelope());
                        resolve();
                    } else {
                        if (command === 'prune --apply')
                            receive(`Idempotency key: ${KEY}\nOperation: ${ID}\n`);
                        reject(bridgeFailure());
                    }
                }, 10);
            });
            return Object.assign(completion, {
                stream(callback: (chunk: string) => void) { receive = callback; return this },
                input() { throw new Error('Controlled process boundary accepts no candidate or host write') },
            });
        },
    };
}

async function investigate(): Promise<Record<string, unknown>> {
    createBoundary();
    const maintenanceNode = document.getElementById('maintenance');
    const errorNode = document.getElementById('query-error');
    invariant(maintenanceNode && errorNode, 'Fixture mount points are missing');
    const maintenance = createRoot(maintenanceNode);
    const errorView = createRoot(errorNode);
    maintenance.render(<Maintenance />);
    const initial = await until(() => {
        const card = pruneCard();
        return card && button('Dry run', card);
    }, 'actual Maintenance mount');
    const cardBefore = pruneCard();
    invariant(cardBefore && button('Apply', cardBefore)?.disabled, 'Apply must begin disabled');
    initial.click();
    const apply = await until(() => {
        const card = pruneCard();
        const found = card && button('Apply', card);
        return found && !found.disabled ? found : null;
    }, 'successful Dry run enables actual Apply');
    apply.click();
    const confirmedApply = await until(() => button('Run prune --apply'), 'actual confirmation dialog');
    confirmedApply.click();
    await until(() => {
        const card = pruneCard();
        return card && normalizedText(card).includes(KEY) && normalizedText(card).includes('reconnected');
    }, 'actual QueryError after Apply loses process observation');
    const failedCard = pruneCard();
    invariant(failedCard, 'Actual maintenance card disappeared');
    const afterFailure = button('Apply', failedCard);
    invariant(afterFailure, 'Actual Apply button disappeared');
    const f05 = {
        finding: 'F05', evidenceLayer: 'actual mounted Maintenance and real adapter/runner; controlled Cockpit process',
        dryRunSucceeded: normalizedText(failedCard).includes('synthetic dry run'),
        originalKeyVisible: normalizedText(failedCard).includes(KEY),
        originalOperationVisible: normalizedText(failedCard).includes(ID),
        applyEnabledAfterUncertainFailure: !afterFailure.disabled,
        applySubmissions: window.cprFixture.calls.filter(command => command === 'prune --apply').length,
    };

    let caught: unknown;
    try {
        await runHfcache(['config', 'validate']);
    } catch (error) {
        caught = error;
    }
    invariant(caught instanceof Error, 'Synthetic validation interruption must reject through actual runner');
    const retained = caught as Error & { problem?: unknown; stage?: unknown };
    errorView.render(<QueryError error={caught} />);
    await until(() => normalizedText(errorNode).includes('reconnected'), 'actual standalone QueryError render');
    const f01 = {
        finding: 'F01', evidenceLayer: 'actual mounted QueryError and real validation adapter/runner; controlled Cockpit process',
        interruptedCommand: 'config validate',
        inputProblem: 'reconnected',
        retainedProblem: typeof retained.problem === 'string' ? retained.problem : null,
        retainedStage: typeof retained.stage === 'string' ? retained.stage : null,
        literalMessageVisible: normalizedText(errorNode).includes('reconnected'),
        genericObservationTitleVisible: normalizedText(errorNode).includes('hfcache response could not be observed'),
        genericAcceptedWorkWarningVisible: normalizedText(errorNode).includes('missing response does not cancel accepted server work'),
    };

    // Actual root-component unmount/remount, not Application's real tab control.
    maintenance.unmount();
    const remounted = createRoot(maintenanceNode);
    remounted.render(<Maintenance />);
    await until(() => pruneCard() && button('Dry run', pruneCard()!), 'actual Maintenance remount');
    const f04 = {
        finding: 'F04', evidenceLayer: 'actual Maintenance root unmount/remount; not real Application tab acceptance',
        originalHandleVisibleAfterRemount: normalizedText(maintenanceNode).includes(KEY),
        noAutomaticSubmissionOnRemount: window.cprFixture.calls.length === 3,
    };
    remounted.unmount();
    errorView.unmount();
    return {
        state: 'observed', realPamAcceptance: false, realApiOrShellCalls: false,
        processCalls: window.cprFixture.calls, observations: [f01, f05, f04],
    };
}

async function report(): Promise<void> {
    let result: Record<string, unknown>;
    try {
        result = await investigate();
    } catch (error) {
        result = {
            state: 'fixture-failed', realPamAcceptance: false, realApiOrShellCalls: false,
            message: error instanceof Error ? error.message.slice(0, 256) : 'Non-Error investigation failure',
            processCalls: window.cprFixture?.calls ?? [],
        };
    }
    await fetch('/result', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(result),
    });
}

void report();
