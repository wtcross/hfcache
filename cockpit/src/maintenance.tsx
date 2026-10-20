/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Maintenance (docs/cockpit.md §3): prune and recover as dry-run-first
 * flows — one describes, the other performs, and neither is a default —
 * and repair as the one explicit republish (decision 89).
 */

import React, { useRef, useState } from 'react';

import { Button } from "@patternfly/react-core/dist/esm/components/Button/index.js";
import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import {
    ExpandableSection,
} from "@patternfly/react-core/dist/esm/components/ExpandableSection/index.js";
import {
    Modal, ModalBody, ModalFooter, ModalHeader,
} from "@patternfly/react-core/dist/esm/components/Modal/index.js";
import { TextInput } from "@patternfly/react-core/dist/esm/components/TextInput/index.js";
import { Flex, FlexItem } from "@patternfly/react-core/dist/esm/layouts/Flex/index.js";
import { Stack, StackItem } from "@patternfly/react-core/dist/esm/layouts/Stack/index.js";

import { runHfcache, runHfcacheStreaming } from './api/hfcache';
import { DataSummary, EnvelopeAlert, Loading, QueryError, RecoveryHandles } from './components';
import { useObservationSignal, useOperationHandles, useConnection, useOperations, useHostProfile } from './hooks';
import { hostActionAllowed } from './api/profile';
import { currentOperationHost, operationRegistry, submissionBlocked } from './api/operations';
import { connectionSnapshot, synchronizeConnection } from './api/connection';
import type { ConnectionSnapshot } from './api/connection';
import { sameOperationScope } from './lib/operation-registry';
import type { OperationScope } from './lib/operation-registry';
import { parseSelector, SelectorError } from './lib/command';
import { classifyEnvelope, Envelope } from './lib/envelope';
import { appendDisplayLine } from './lib/stream';

const DryRunApplyCard = ({ title, command, intro, applyWarning }: {
    title: string;
    command: 'prune' | 'recover';
    intro: string;
    applyWarning: string;
}) => {
    const [busy, setBusy] = useState(false);
    const [dryRun, setDryRun] = useState<Envelope | null>(null);
    const [applied, setApplied] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const [confirming, setConfirming] = useState(false);
    const observationSignal = useObservationSignal();
    const connection = useConnection();
    const host = currentOperationHost();
    const operations = useOperations();
    const profile = useHostProfile();
    const submitted = useRef(false);
    const consumed = useRef(false);
    const dryRunKey = useRef<string | null>(null);
    const [dryRunScope, setDryRunScope] = useState<Readonly<OperationScope> | null>(null);
    const [dryRunGeneration, setDryRunGeneration] = useState<number | null>(null);

    const run = (apply: boolean) => {
        if (synchronizeConnection() !== connection || host !== currentOperationHost()) return;
        if (!connection.administrative || !hostActionAllowed(apply ? 'archive' : 'control') || submitted.current || submissionBlocked() ||
            (apply && (consumed.current || error !== null || dryRun === null || !dryRunScope ||
                dryRunGeneration !== connectionSnapshot().generation || classifyEnvelope(dryRun) !== 'success')))
            return;
        submitted.current = true;
        if (apply)
            consumed.current = true;
        const signal = observationSignal();
        const generation = connectionSnapshot().generation;
        setConfirming(false);
        setBusy(true);
        setError(null);
        if (apply)
            setApplied(null);
        else {
            setDryRun(null);
            setDryRunScope(null);
            setDryRunGeneration(null);
            dryRunKey.current = null;
        }
        runHfcache([command, apply ? '--apply' : '--dry-run'], {
            signal,
            ...(apply && dryRunScope ? { requiredScope: dryRunScope } : {}),
            onNotice: notice => {
                if (!apply && notice.kind === 'key')
                    dryRunKey.current = notice.key;
            },
        })
                .then(envelope => {
                    if (signal.aborted)
                        return;
                    if (apply) {
                        setApplied(envelope);
                    } else {
                        setDryRun(envelope);
                        setApplied(null);
                        consumed.current = false;
                        const original = operationRegistry.snapshot().records.find(record => record.key === dryRunKey.current);
                        setDryRunScope(original?.scope ?? null);
                        setDryRunGeneration(generation);
                    }
                }, failure => { if (!signal.aborted) setError(failure as Error); })
                .finally(() => {
                    submitted.current = false;
                    if (!signal.aborted) setBusy(false);
                });
    };

    const uncertain = operations.blocked || error !== null ||
        [dryRun, applied].some(result => result !== null && classifyEnvelope(result) === 'observation');
    const previewFresh = dryRunGeneration === connection.generation && dryRunScope !== null &&
        operations.views.authority.generation === connection.generation && operations.views.authority.scope !== null &&
        sameOperationScope(dryRunScope, operations.views.authority.scope);
    const canApply = profile.permissions.archive && !uncertain && previewFresh && !consumed.current && applied === null && dryRun !== null && classifyEnvelope(dryRun) === 'success';

    return (
        <Card>
            <CardTitle>{title}</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>{intro}</StackItem>
                    {(!profile.permissions.control || !profile.permissions.archive) && <StackItem>{profile.reason}</StackItem>}
                    <StackItem>
                        <Flex>
                            <FlexItem>
                                <Button variant="secondary" isDisabled={busy || uncertain || !connection.administrative || !profile.permissions.control} onClick={() => run(false)}>
                                    Dry run
                                </Button>
                            </FlexItem>
                            <FlexItem>
                                <Button
                                    variant="danger"
                                    isDisabled={busy || !canApply || !connection.administrative}
                                    onClick={() => setConfirming(true)}
                                >
                                    Apply
                                </Button>
                            </FlexItem>
                            {busy && <FlexItem><Loading /></FlexItem>}
                        </Flex>
                    </StackItem>
                    {error !== null && <StackItem><QueryError error={error} /></StackItem>}
                    {dryRun !== null &&
                        <>
                            <StackItem><EnvelopeAlert envelope={dryRun} /></StackItem>
                            <StackItem><DataSummary data={dryRun.data} /></StackItem>
                            <StackItem>
                                <ExpandableSection toggleText="Dry-run detail">
                                    <pre className="hfcache-journal">
                                        {JSON.stringify(dryRun.data, null, 2)}
                                    </pre>
                                </ExpandableSection>
                            </StackItem>
                        </>}
                    {applied !== null &&
                        <>
                            <StackItem><EnvelopeAlert envelope={applied} /></StackItem>
                            <StackItem><DataSummary data={applied.data} /></StackItem>
                        </>}
                </Stack>

                <Modal
                    isOpen={confirming}
                    onClose={() => setConfirming(false)}
                    variant="small"
                    aria-label={`Apply ${command}`}
                >
                    <ModalHeader title={`Apply ${command}`} />
                    <ModalBody>{applyWarning}</ModalBody>
                    <ModalFooter>
                        <Button variant="danger" isDisabled={!connection.administrative || busy || !canApply} onClick={() => run(true)}>{`Run ${command} --apply`}</Button>
                        <Button variant="link" onClick={() => setConfirming(false)}>Cancel</Button>
                    </ModalFooter>
                </Modal>
            </CardBody>
        </Card>
    );
};

const RepairCard = () => {
    const [selectorText, setSelectorText] = useState('');
    const [reason, setReason] = useState('');
    const [confirmation, setConfirmation] = useState<{ host: string; connection: ConnectionSnapshot } | null>(null);
    const [running, setRunning] = useState(false);
    const [feed, setFeed] = useState<string[]>([]);
    const [result, setResult] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const observationSignal = useObservationSignal();
    const connection = useConnection();
    const host = currentOperationHost();
    const operations = useOperations();
    const profile = useHostProfile();
    const submitted = useRef(false);
    const { handles, reset: resetHandles, onNotice } = useOperationHandles();
    const confirmationReady = confirmation?.connection === connection && confirmation.host === host;

    let validationError: string | null = null;
    if (selectorText !== '') {
        try {
            const selector = parseSelector(selectorText);
            if (selector.sha === undefined)
                validationError = 'repair takes TYPE:ID@SHA with the full 40-character commit SHA';
        } catch (failure) {
            validationError = failure instanceof SelectorError ? failure.message : String(failure);
        }
    }

    const run = () => {
        if (synchronizeConnection() !== connection || host !== currentOperationHost()) return;
        if (!confirmationReady || !connectionSnapshot().administrative || !hostActionAllowed('archive') || submitted.current || submissionBlocked())
            return;
        try {
            if (parseSelector(selectorText).sha === undefined)
                return;
        } catch { return }
        submitted.current = true;
        const signal = observationSignal();
        setConfirmation(null);
        setRunning(true);
        setFeed([]);
        setResult(null);
        setError(null);
        resetHandles();
        const command = reason === ''
            ? ['repair', selectorText]
            : ['repair', selectorText, '--reason', reason];
        runHfcacheStreaming(command, {
            signal,
            onNotice,
            onLine: line => setFeed(previous => appendDisplayLine(previous, line, 100)),
        })
                .then(envelope => { if (!signal.aborted) setResult(envelope); },
                      failure => { if (!signal.aborted) setError(failure as Error); })
                .finally(() => {
                    submitted.current = false;
                    if (!signal.aborted) setRunning(false);
                });
    };

    const uncertain = operations.blocked || (result !== null && classifyEnvelope(result) === 'observation') ||
        (error !== null && (handles.idempotencyKey !== undefined || handles.operationId !== undefined));

    return (
        <Card>
            <CardTitle>Repair a damaged revision</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>
                        The explicit republish for a revision a verification found damaged: the
                        exact SHA is re-downloaded in isolation, verified against the
                        <strong> original</strong> manifest, and only then switched in. If any
                        expected digest differs, repair stops without changing the published
                        revision (AD-13). Copy the SHA from the verification finding.
                    </StackItem>
                    <StackItem>
                        <TextInput
                            id="repair-selector"
                            aria-label="Revision selector"
                            placeholder="model:organization/name@0123456789abcdef0123456789abcdef01234567"
                            value={selectorText}
                            validated={validationError === null ? 'default' : 'error'}
                            onChange={(_event, value) => setSelectorText(value)}
                        />
                        {validationError !== null &&
                            <div className="hfcache-field-error">{validationError}</div>}
                    </StackItem>
                    <StackItem>
                        <TextInput
                            id="repair-reason"
                            aria-label="Reason"
                            placeholder="--reason (recorded in the audit trail; optional)"
                            value={reason}
                            onChange={(_event, value) => setReason(value)}
                        />
                    </StackItem>
                    <StackItem>
                        <Button
                            variant="danger"
                            isDisabled={running || uncertain || !connection.administrative || !profile.permissions.archive || selectorText === '' || validationError !== null}
                            onClick={() => setConfirmation({ host, connection })}
                        >
                            Repair…
                        </Button>
                    </StackItem>
                    {running && <StackItem><Loading /></StackItem>}
                    {!profile.permissions.archive && <StackItem>{profile.reason}</StackItem>}
                    <StackItem><RecoveryHandles evidence={handles} /></StackItem>
                    {feed.length > 0 &&
                        <StackItem>
                            <ExpandableSection toggleText="Command log">
                                <pre className="hfcache-journal">{feed.join('\n')}</pre>
                            </ExpandableSection>
                        </StackItem>}
                    {error !== null && <StackItem><QueryError error={error} /></StackItem>}
                    {result !== null &&
                        <>
                            <StackItem><EnvelopeAlert envelope={result} /></StackItem>
                            <StackItem><DataSummary data={result.data} /></StackItem>
                        </>}
                </Stack>

                <Modal
                    isOpen={confirmationReady}
                    onClose={() => setConfirmation(null)}
                    variant="small"
                    aria-label="Start repair"
                >
                    <ModalHeader title={`Repair ${selectorText}`} />
                    <ModalBody>
                        Downloads that revision again and publishes a replacement instance; the
                        superseded instance stays readable for the configured grace period (at
                        least seven days). The transient API client observes server execution;
                        closing this view does not cancel accepted repair. Retain the key and
                        operation ID and observe that result before submitting again or
                        considering recovery. The executor holds the single archive lock.
                    </ModalBody>
                    <ModalFooter>
                        <Button variant="danger" isDisabled={!confirmationReady || !connection.administrative || !profile.permissions.archive || running || uncertain || validationError !== null || selectorText === ''} onClick={run}>Start repair</Button>
                        <Button variant="link" onClick={() => setConfirmation(null)}>Cancel</Button>
                    </ModalFooter>
                </Modal>
            </CardBody>
        </Card>
    );
};

export const Maintenance = () => (
    <Stack hasGutter>
        <StackItem>
            <DryRunApplyCard
                title="Retention (prune)"
                command="prune"
                intro={'Retention normally runs inside sync: a publication beyond the configured limit rotates the ' +
                    'oldest non-current one out (AD-04). This exists to inspect the plan and to ' +
                    'finish a deferred rotation or apply a lower limit. Each invocation removes at most one ' +
                    'revision per repository; review and repeat until no eligible excess remains.'}
                applyWarning={'The server recomputes and validates a fresh plan under the archive ' +
                    'lock; a preview grants no apply authority. Changed queued policy refuses. ' +
                    'Where a prune can fail leaving more or less data, it leaves more (TX-06).'}
            />
        </StackItem>
        <StackItem>
            <DryRunApplyCard
                title="Recovery (recover)"
                command="recover"
                intro={'Reconciles unfinished transaction journals. The dry run is always safe, ' +
                    'including on an archive that has stopped accepting writes; blocked states ' +
                    'carry their HFTXN codes and stop every mutating command until resolved.'}
                applyWarning={'Executes only a fully validated plan and is idempotent — running it ' +
                    'twice is harmless. Recovery never replaces an expected digest, never picks a ' +
                    'revision by modification time, and never deletes unknown data (AD-16).'}
            />
        </StackItem>
        <StackItem><RepairCard /></StackItem>
    </Stack>
);
