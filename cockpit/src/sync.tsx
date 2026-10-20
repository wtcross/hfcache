/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Sync operations (docs/cockpit.md §3, §5): the full run through the
 * shared REST operation flow (CP-04), the schedule through the timer alone (CP-05),
 * selector-restricted runs through the API-backed CLI, with observation
 * lifetime distinct from accepted execution (ADR122).
 */

import React, { useEffect, useRef, useState } from 'react';

import { Alert } from "@patternfly/react-core/dist/esm/components/Alert/index.js";
import { Button } from "@patternfly/react-core/dist/esm/components/Button/index.js";
import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import { Checkbox } from "@patternfly/react-core/dist/esm/components/Checkbox/index.js";
import {
    DescriptionList, DescriptionListDescription, DescriptionListGroup, DescriptionListTerm,
} from "@patternfly/react-core/dist/esm/components/DescriptionList/index.js";
import { Label } from "@patternfly/react-core/dist/esm/components/Label/index.js";
import {
    Modal, ModalBody, ModalFooter, ModalHeader,
} from "@patternfly/react-core/dist/esm/components/Modal/index.js";
import { Flex, FlexItem } from "@patternfly/react-core/dist/esm/layouts/Flex/index.js";
import { Stack, StackItem } from "@patternfly/react-core/dist/esm/layouts/Stack/index.js";

import { UnitActivity } from './activity';
import { ManualFullJob } from './manual-job';
import { hostActionAllowed, hostActionReason } from './api/profile';
import { ScheduleEditor } from './schedule';
import { runHfcacheStreaming } from './api/hfcache';
import { connectionSnapshot } from './api/connection';
import { currentOperationHost, submissionBlocked } from './api/operations';
import { startUnit, stopUnit, SYNC_SERVICE, SYNC_TIMER } from './api/systemd';
import { DataSummary, EnvelopeAlert, Loading, QueryError, RecoveryHandles } from './components';
import { useHfcache, useObservationSignal, useOperationHandles, useUnitPoll, useConnection, useOperations, useHostProfile } from './hooks';
import { classifyEnvelope, Envelope } from './lib/envelope';
import { formatSelector, parseSelector } from './lib/command';
import { formatTimestamp } from './lib/format';
import { appendDisplayLine } from './lib/stream';
import { parseStatus } from './lib/read-results';

const Item = ({ term, children }: { term: string; children: React.ReactNode }) => (
    <DescriptionListGroup>
        <DescriptionListTerm>{term}</DescriptionListTerm>
        <DescriptionListDescription>{children}</DescriptionListDescription>
    </DescriptionListGroup>
);

const ConfirmModal = ({ title, confirmLabel, isOpen, onClose, onConfirm, children, disabled = false }: {
    title: string;
    confirmLabel: string;
    isOpen: boolean;
    disabled?: boolean;
    onClose: () => void;
    onConfirm: () => void;
    children: React.ReactNode;
}) => {
    const connection = useConnection();
    return (
        <Modal isOpen={isOpen} onClose={onClose} variant="small" aria-label={title}>
            <ModalHeader title={title} />
            <ModalBody>{children}</ModalBody>
            <ModalFooter>
                <Button variant="primary" isDisabled={disabled || !connection.administrative} onClick={onConfirm}>{confirmLabel}</Button>
                <Button variant="link" onClick={onClose}>Cancel</Button>
            </ModalFooter>
        </Modal>
    );
};

const ACTIVE_STATES = ['active', 'activating', 'reloading', 'deactivating'];

const SyncControls = ({ onObserverState }: { onObserverState: (stopped: boolean) => void }) => {
    const service = useUnitPoll(SYNC_SERVICE);
    const timer = useUnitPoll(SYNC_TIMER);
    const profile = useHostProfile();
    const [confirming, setConfirming] = useState<'stop' | 'pause' | null>(null);
    const [actionError, setActionError] = useState<Error | null>(null);

    const running = ACTIVE_STATES.includes(service.state?.activeState ?? '');
    const serviceAvailable = service.state !== null && service.state.activeState !== 'unknown';
    const timerAvailable = timer.state !== null && timer.state.activeState !== 'unknown';
    const timerActive = ACTIVE_STATES.includes(timer.state?.activeState ?? '');

    const act = (action: Promise<unknown>, observerStopped?: boolean) => {
        setConfirming(null);
        setActionError(null);
        action
                .then(() => {
                    service.refresh();
                    timer.refresh();
                    if (observerStopped !== undefined)
                        onObserverState(observerStopped);
                })
                .catch(failure => setActionError(failure as Error));
    };

    return (
        <Card>
            <CardTitle>Scheduled sync observer</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>System service state and journals describe the scheduled observer only. They do not establish the result of a manual server operation.</StackItem>
                    {!profile.permissions.schedule && <StackItem><Alert variant="warning" isInline title="Schedule changes unavailable">{profile.reason}</Alert></StackItem>}
                    {running && !profile.permissions.observer && <StackItem>{hostActionReason('observer')}</StackItem>}
                    {actionError !== null && <StackItem><QueryError error={actionError} /></StackItem>}
                    {service.error !== null && <StackItem><QueryError error={service.error} /></StackItem>}
                    {timer.error !== null && <StackItem><QueryError error={timer.error} /></StackItem>}
                    <StackItem>
                        <DescriptionList isHorizontal isCompact>
                            <Item term="hfcache-sync.service">
                                <Label isCompact color={running ? 'blue' : 'grey'}>
                                    {service.state?.activeState ?? '…'}
                                </Label>
                                {' '}observer process result: {service.result?.result ?? '…'}
                                {service.result !== null && ` (exit ${service.result.execMainStatus})`}
                            </Item>
                            <Item term="hfcache-sync.timer">
                                <Label isCompact color={timerActive ? 'green' : 'orange'}>
                                    {!timerAvailable ? 'unavailable' : timerActive ? 'scheduled' : 'paused'}
                                </Label>
                                {' '}{timer.state?.unitFileState ?? '…'};
                                next {formatTimestamp(timer.timer?.nextElapse?.toISOString())},
                                last {formatTimestamp(timer.timer?.lastTrigger?.toISOString())}
                            </Item>
                        </DescriptionList>
                    </StackItem>
                    <StackItem>
                        <Flex>
                            <FlexItem>
                                <Button
                                    variant="danger"
                                    isDisabled={!running || !serviceAvailable || !profile.permissions.observer}
                                    onClick={() => setConfirming('stop')}
                                >
                                    Stop scheduled sync observer
                                </Button>
                            </FlexItem>
                            <FlexItem>
                                {timerAvailable && timerActive &&
                                    <Button variant="secondary" isDisabled={!profile.permissions.schedule} onClick={() => setConfirming('pause')}>Pause schedule</Button>}
                                {timerAvailable && !timerActive &&
                                    <Button variant="secondary" isDisabled={!profile.permissions.schedule} onClick={() => { if (hostActionAllowed('schedule')) act(startUnit(SYNC_TIMER)); }}>Resume schedule</Button>}
                            </FlexItem>
                        </Flex>
                    </StackItem>
                    {running && <StackItem><UnitActivity unit={SYNC_SERVICE} /></StackItem>}
                </Stack>

                <ConfirmModal
                    title="Stop the scheduled sync observer"
                    confirmLabel="Stop observer"
                    disabled={!serviceAvailable || !profile.permissions.observer}
                    isOpen={confirming === 'stop'}
                    onClose={() => setConfirming(null)}
                    onConfirm={() => { if (serviceAvailable && hostActionAllowed('observer')) act(stopUnit(SYNC_SERVICE), true); }}
                >
                    Stops hfcache-sync.service, the API observer. Accepted server work may
                    continue. Its pending handle is retained separately from manual jobs.
                    This does not cancel execution or prove
                    that recovery or a release switch is safe.
                </ConfirmModal>
                <ConfirmModal
                    title="Pause the schedule"
                    confirmLabel="Stop hfcache-sync.timer"
                    disabled={!timerAvailable || !profile.permissions.schedule}
                    isOpen={confirming === 'pause'}
                    onClose={() => setConfirming(null)}
                    onConfirm={() => { if (timerAvailable && hostActionAllowed('schedule')) act(stopUnit(SYNC_TIMER)); }}
                >
                    Stops the timer only — the mount and hfcache.target are untouched (CP-05).
                    Resume from here; a Persistent timer whose calendar elapsed while stopped
                    fires once on resume.
                </ConfirmModal>
            </CardBody>
        </Card>
    );
};

const SelectorSync = () => {
    const profile = useHostProfile();
    const status = useHfcache(['status']);
    const connection = useConnection();
    const operations = useOperations();
    const [selected, setSelected] = useState<Record<string, boolean>>({});
    const [confirming, setConfirming] = useState<Envelope | null>(null);
    const [running, setRunning] = useState(false);
    const [feed, setFeed] = useState<string[]>([]);
    const [result, setResult] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const { handles, reset: resetHandles, onNotice } = useOperationHandles();
    const observationSignal = useObservationSignal();
    const submitted = useRef(false);
    const host = currentOperationHost();

    const parsed = status.envelope === null ? null : parseStatus(status.envelope);
    const statusReady = !status.loading && status.error === null && status.envelope?.exit_code === 0 &&
        parsed?.error === null && parsed.payload?.repositories !== undefined && !parsed.partial;
    const repositories = (parsed?.payload?.repositories ?? [])
            .filter(repository => repository.managed && repository.enabled === true);
    const selectors = (statusReady ? repositories : [])
            .map(repository => formatSelector({ type: repository.repository_type, id: repository.repository_id }))
            .filter(selector => selected[selector] === true);
    const confirmationReady = confirming !== null && confirming === status.envelope && statusReady;
    useEffect(() => { setSelected({}); setConfirming(null) }, [status.envelope, connection, host]);

    const run = () => {
        if (submitted.current || running || submissionBlocked() || !connectionSnapshot().administrative ||
            connectionSnapshot() !== connection || host !== currentOperationHost() ||
            !hostActionAllowed('archive') || !confirmationReady || selectors.length === 0)
            return;
        try {
            for (const value of selectors) {
                if (parseSelector(value).sha !== undefined)
                    return;
            }
        } catch { return }
        submitted.current = true;
        const signal = observationSignal();
        setConfirming(null);
        setRunning(true);
        setFeed([]);
        setResult(null);
        setError(null);
        resetHandles();
        runHfcacheStreaming(['sync', ...selectors], {
            signal,
            onLine: line => setFeed(previous => appendDisplayLine(previous, line)),
            onNotice,
        })
                .then(envelope => { if (!signal.aborted) setResult(envelope); },
                      failure => {
                          if (!signal.aborted)
                              setError(failure as Error);
                      })
                .finally(() => {
                    submitted.current = false;
                    if (!signal.aborted) setRunning(false);
                });
    };

    const uncertain = (result !== null && classifyEnvelope(result) === 'observation') ||
        (error !== null && (handles.idempotencyKey !== undefined || handles.operationId !== undefined));

    return (
        <Card>
            <CardTitle>Sync selected repositories</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    {status.loading && <StackItem><Loading /></StackItem>}
                    {status.error !== null && <StackItem><QueryError error={status.error} /></StackItem>}
                    {status.envelope !== null && !status.loading && <StackItem><EnvelopeAlert envelope={status.envelope} /></StackItem>}
                    {parsed?.error && <StackItem><QueryError error={parsed.error} /></StackItem>}
                    {parsed?.partial && parsed.payload?.repositories !== undefined && <StackItem><Alert variant="warning" isInline title="Partial repository status">Validated rows from a failed read are informational. Refresh successfully before selecting a sync operation.</Alert></StackItem>}
                    {!status.loading && !statusReady && <StackItem><Alert variant="warning" isInline title="Repository selection unavailable">A fresh, successful and validated repository status is required.</Alert></StackItem>}
                    {statusReady && repositories.length === 0 && <StackItem>No enabled managed repositories in this status response.</StackItem>}
                    <StackItem><Button variant="link" isDisabled={status.loading || !connection.administrative} onClick={() => status.refresh()}>Refresh repository selection</Button></StackItem>
                    <StackItem>
                        {repositories.map(repository => {
                            const selector = formatSelector({
                                type: repository.repository_type,
                                id: repository.repository_id,
                            });
                            return (
                                <Checkbox
                                    key={selector}
                                    id={`select-${selector}`}
                                    label={selector}
                                    isDisabled={!statusReady || running}
                                    isChecked={selected[selector] === true}
                                    onChange={(_event, checked) =>
                                        setSelected(previous => ({ ...previous, [selector]: checked }))}
                                />
                            );
                        })}
                    </StackItem>
                    <StackItem>
                        <Button
                            variant="secondary"
                            isDisabled={running || uncertain || operations.blocked || !connection.administrative ||
                                !profile.permissions.archive || !statusReady || selectors.length === 0}
                            onClick={() => { if (statusReady) setConfirming(status.envelope); }}
                        >
                            Sync selected ({selectors.length})
                        </Button>
                    </StackItem>
                    {running &&
                        <StackItem>
                            <Alert
                                variant="info"
                                isInline
                                title="Observing a server operation"
                            >Closing this view stops its display; accepted work continues. Retain
                                the key and operation ID to reconnect.
                            </Alert>
                        </StackItem>}
                    <StackItem><RecoveryHandles evidence={handles} /></StackItem>
                    {feed.length > 0 &&
                        <StackItem>
                            <pre className="hfcache-journal">{feed.join('\n')}</pre>
                        </StackItem>}
                    {error !== null && <StackItem><QueryError error={error} /></StackItem>}
                    {result !== null &&
                        <>
                            <StackItem><EnvelopeAlert envelope={result} /></StackItem>
                            <StackItem><DataSummary data={result.data} /></StackItem>
                        </>}
                </Stack>

                <ConfirmModal
                    title={`Sync ${selectors.length} selected`}
                    confirmLabel="Start selector sync"
                    disabled={running || uncertain || operations.blocked || !profile.permissions.archive || !confirmationReady || selectors.length === 0}
                    isOpen={confirming !== null}
                    onClose={() => setConfirming(null)}
                    onConfirm={run}
                >
                    The transient CLI client submits one operation to the API and observes it.
                    Closing this view or losing the connection does not cancel accepted work.
                    Retain its key and operation ID and observe that operation before submitting
                    again. The full-archive run uses the manual REST job above.
                </ConfirmModal>
            </CardBody>
        </Card>
    );
};

export const SyncOperations = () => {
    const [observerStopped, setObserverStopped] = useState(false);
    const [scheduleGeneration, setScheduleGeneration] = useState(0);

    return (
        <Stack hasGutter>
            <StackItem><ManualFullJob mode="sync" /></StackItem>
            <StackItem>
                <SyncControls
                    key={scheduleGeneration}
                    onObserverState={setObserverStopped}
                />
            </StackItem>
            <StackItem>
                <ScheduleEditor onApplied={() => setScheduleGeneration(value => value + 1)} />
            </StackItem>
            <StackItem><SelectorSync /></StackItem>
            {observerStopped &&
                <StackItem>
                    <Alert variant="info" isInline title="The sync observer stopped">
                        Accepted server work may continue. Preserve the pending handle and inspect
                        its journal independently of manual jobs. A stopped client does not
                        establish that the archive is idle.
                    </Alert>
                </StackItem>}
        </Stack>
    );
};
