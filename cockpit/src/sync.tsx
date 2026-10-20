/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Sync operations (docs/cockpit.md §3, §5): the full run through the
 * shipped unit (CP-04), the schedule through the timer alone (CP-05),
 * selector-restricted runs through the API-backed CLI, with observation
 * lifetime distinct from accepted execution (ADR122).
 */

import React, { useRef, useState } from 'react';

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
import { ScheduleEditor } from './schedule';
import { runHfcacheStreaming } from './api/hfcache';
import { connectionSnapshot } from './api/connection';
import { submissionBlocked } from './api/operations';
import { startUnit, stopUnit, SYNC_SERVICE, SYNC_TIMER } from './api/systemd';
import { DataSummary, EnvelopeAlert, Loading, QueryError, RecoveryHandles } from './components';
import { useHfcache, useObservationSignal, useOperationHandles, useUnitPoll, useConnection, useOperations } from './hooks';
import { classifyEnvelope, Envelope } from './lib/envelope';
import { formatSelector, parseSelector } from './lib/command';
import { formatTimestamp } from './lib/format';
import { appendDisplayLine } from './lib/stream';

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
    const [confirming, setConfirming] = useState<'start' | 'stop' | 'pause' | null>(null);
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
            <CardTitle>Synchronization</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    {actionError !== null && <StackItem><QueryError error={actionError} /></StackItem>}
                    {service.error !== null && <StackItem><QueryError error={service.error} /></StackItem>}
                    {timer.error !== null && <StackItem><QueryError error={timer.error} /></StackItem>}
                    <StackItem>
                        <DescriptionList isHorizontal isCompact>
                            <Item term="hfcache-sync.service">
                                <Label isCompact color={running ? 'blue' : 'grey'}>
                                    {service.state?.activeState ?? '…'}
                                </Label>
                                {' '}last result: {service.result?.result ?? '…'}
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
                                    variant="primary"
                                    isDisabled={running || !serviceAvailable}
                                    onClick={() => setConfirming('start')}
                                >
                                    Start / resume full sync
                                </Button>
                            </FlexItem>
                            <FlexItem>
                                <Button
                                    variant="danger"
                                    isDisabled={!running || !serviceAvailable}
                                    onClick={() => setConfirming('stop')}
                                >
                                    Stop observing full sync
                                </Button>
                            </FlexItem>
                            <FlexItem>
                                {timerAvailable && timerActive &&
                                    <Button variant="secondary" onClick={() => setConfirming('pause')}>Pause schedule</Button>}
                                {timerAvailable && !timerActive &&
                                    <Button variant="secondary" onClick={() => act(startUnit(SYNC_TIMER))}>Resume schedule</Button>}
                            </FlexItem>
                        </Flex>
                    </StackItem>
                    {running && <StackItem><UnitActivity unit={SYNC_SERVICE} /></StackItem>}
                </Stack>

                <ConfirmModal
                    title="Start a full sync"
                    confirmLabel="Start hfcache-sync.service"
                    disabled={!serviceAvailable}
                    isOpen={confirming === 'start'}
                    onClose={() => setConfirming(null)}
                    onConfirm={() => { if (serviceAvailable) act(startUnit(SYNC_SERVICE), false); }}
                >
                    Starts the installed API client used by the 02:00 timer. It resumes a
                    retained operation, or submits one sync when no pending handle exists.
                    The server executes accepted work; a large repository can take hours.
                </ConfirmModal>
                <ConfirmModal
                    title="Stop observing the full sync"
                    confirmLabel="Stop observer"
                    disabled={!serviceAvailable}
                    isOpen={confirming === 'stop'}
                    onClose={() => setConfirming(null)}
                    onConfirm={() => { if (serviceAvailable) act(stopUnit(SYNC_SERVICE), true); }}
                >
                    Stops hfcache-sync.service, the API observer. Accepted server work may
                    continue. Its pending handle is retained; starting the service again
                    observes the existing operation. This does not cancel execution or prove
                    that recovery or a release switch is safe.
                </ConfirmModal>
                <ConfirmModal
                    title="Pause the schedule"
                    confirmLabel="Stop hfcache-sync.timer"
                    disabled={!timerAvailable}
                    isOpen={confirming === 'pause'}
                    onClose={() => setConfirming(null)}
                    onConfirm={() => { if (timerAvailable) act(stopUnit(SYNC_TIMER)); }}
                >
                    Stops the timer only — the mount and hfcache.target are untouched (CP-05).
                    Resume from here; a Persistent timer whose calendar elapsed while stopped
                    fires once on resume.
                </ConfirmModal>
            </CardBody>
        </Card>
    );
};

interface StatusRepositoryLite {
    repository_id: string;
    repository_type: 'model' | 'dataset';
    enabled: boolean;
    managed: boolean;
}

const SelectorSync = () => {
    const status = useHfcache(['status']);
    const connection = useConnection();
    const operations = useOperations();
    const [selected, setSelected] = useState<Record<string, boolean>>({});
    const [confirming, setConfirming] = useState(false);
    const [running, setRunning] = useState(false);
    const [feed, setFeed] = useState<string[]>([]);
    const [result, setResult] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const { handles, reset: resetHandles, onNotice } = useOperationHandles();
    const observationSignal = useObservationSignal();
    const submitted = useRef(false);

    const statusReady = !status.loading && status.error === null && status.envelope?.exit_code === 0;
    const observed = ((status.envelope?.data ?? {}) as { repositories?: StatusRepositoryLite[] }).repositories;
    const repositories = (statusReady && Array.isArray(observed) ? observed : []).filter(repository => {
        if (!repository || repository.managed !== true || repository.enabled !== true)
            return false;
        try {
            parseSelector(formatSelector({ type: repository.repository_type, id: repository.repository_id }));
            return true;
        } catch { return false }
    });
    const selectors = repositories
            .map(repository => formatSelector({ type: repository.repository_type, id: repository.repository_id }))
            .filter(selector => selected[selector] === true);

    const run = () => {
        if (submitted.current || running || submissionBlocked() || !connectionSnapshot().administrative ||
            !statusReady || selectors.length === 0)
            return;
        try {
            for (const value of selectors) {
                if (parseSelector(value).sha !== undefined)
                    return;
            }
        } catch { return }
        submitted.current = true;
        const signal = observationSignal();
        setConfirming(false);
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
                                !statusReady || selectors.length === 0}
                            onClick={() => setConfirming(true)}
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
                    disabled={running || uncertain || operations.blocked || !statusReady || selectors.length === 0}
                    isOpen={confirming}
                    onClose={() => setConfirming(false)}
                    onConfirm={run}
                >
                    The transient CLI client submits one operation to the API and observes it.
                    Closing this view or losing the connection does not cancel accepted work.
                    Retain its key and operation ID and observe that operation before submitting
                    again. The full-archive run belongs to the installed service above (CP-04).
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
                        its journal; start hfcache-sync.service to resume observation. A stopped
                        client does not establish that the archive is idle.
                    </Alert>
                </StackItem>}
        </Stack>
    );
};
