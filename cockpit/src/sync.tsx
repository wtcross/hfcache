/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Sync operations (docs/cockpit.md §3, §5): the full run through the
 * shipped unit (CP-04), the schedule through the timer alone (CP-05),
 * selector-restricted runs as page-spawned processes with the consequence
 * stated first (decision 89), and live activity from the journal's closed
 * event vocabulary.
 */

import React, { useState } from 'react';

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
import { startUnit, stopUnit, SYNC_SERVICE, SYNC_TIMER } from './api/systemd';
import { DataSummary, EnvelopeAlert, Loading, QueryError } from './components';
import { useHfcache, useUnitPoll } from './hooks';
import { Envelope } from './lib/envelope';
import { formatSelector } from './lib/command';
import { formatTimestamp } from './lib/format';

const Item = ({ term, children }: { term: string; children: React.ReactNode }) => (
    <DescriptionListGroup>
        <DescriptionListTerm>{term}</DescriptionListTerm>
        <DescriptionListDescription>{children}</DescriptionListDescription>
    </DescriptionListGroup>
);

const ConfirmModal = ({ title, confirmLabel, isOpen, onClose, onConfirm, children }: {
    title: string;
    confirmLabel: string;
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    children: React.ReactNode;
}) => (
    <Modal isOpen={isOpen} onClose={onClose} variant="small" aria-label={title}>
        <ModalHeader title={title} />
        <ModalBody>{children}</ModalBody>
        <ModalFooter>
            <Button variant="primary" onClick={onConfirm}>{confirmLabel}</Button>
            <Button variant="link" onClick={onClose}>Cancel</Button>
        </ModalFooter>
    </Modal>
);

/* After an interruption the contract surfaces reconciliation
 * (docs/cockpit.md §5): recover --dry-run is always safe. */
const RecoverHint = () => {
    const recover = useHfcache(['recover', '--dry-run']);
    return (
        <Card>
            <CardTitle>Reconciliation (recover --dry-run)</CardTitle>
            <CardBody>
                {recover.loading && <Loading />}
                {recover.error !== null && <QueryError error={recover.error} />}
                {recover.envelope !== null && !recover.loading &&
                    <Stack hasGutter>
                        <StackItem><EnvelopeAlert envelope={recover.envelope} /></StackItem>
                        <StackItem><DataSummary data={recover.envelope.data} /></StackItem>
                        <StackItem>
                            Applying an actionable plan is on the Maintenance tab; recovery never
                            guesses (AD-16).
                        </StackItem>
                    </Stack>}
            </CardBody>
        </Card>
    );
};

const ACTIVE_STATES = ['active', 'activating', 'reloading', 'deactivating'];

const SyncControls = ({ onStopped }: { onStopped: () => void }) => {
    const service = useUnitPoll(SYNC_SERVICE);
    const timer = useUnitPoll(SYNC_TIMER);
    const [confirming, setConfirming] = useState<'start' | 'stop' | 'pause' | null>(null);
    const [actionError, setActionError] = useState<Error | null>(null);

    const running = ACTIVE_STATES.includes(service.state?.activeState ?? '');
    const timerActive = ACTIVE_STATES.includes(timer.state?.activeState ?? '');

    const act = (action: Promise<unknown>, thenStopped = false) => {
        setConfirming(null);
        setActionError(null);
        action
                .then(() => {
                    service.refresh();
                    timer.refresh();
                    if (thenStopped)
                        onStopped();
                })
                .catch(failure => setActionError(failure as Error));
    };

    return (
        <Card>
            <CardTitle>Synchronization</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    {actionError !== null && <StackItem><QueryError error={actionError} /></StackItem>}
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
                                    {timerActive ? 'scheduled' : 'paused'}
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
                                    isDisabled={running}
                                    onClick={() => setConfirming('start')}
                                >
                                    Sync now
                                </Button>
                            </FlexItem>
                            <FlexItem>
                                <Button
                                    variant="danger"
                                    isDisabled={!running}
                                    onClick={() => setConfirming('stop')}
                                >
                                    Stop running sync
                                </Button>
                            </FlexItem>
                            <FlexItem>
                                {timerActive &&
                                    <Button variant="secondary" onClick={() => setConfirming('pause')}>Pause schedule</Button>}
                                {!timerActive &&
                                    <Button variant="secondary" onClick={() => act(startUnit(SYNC_TIMER))}>Resume schedule</Button>}
                            </FlexItem>
                        </Flex>
                    </StackItem>
                    {running && <StackItem><UnitActivity unit={SYNC_SERVICE} /></StackItem>}
                </Stack>

                <ConfirmModal
                    title="Start a full sync"
                    confirmLabel="Start hfcache-sync.service"
                    isOpen={confirming === 'start'}
                    onClose={() => setConfirming(null)}
                    onConfirm={() => act(startUnit(SYNC_SERVICE))}
                >
                    This runs the production unit — the same sandbox, identity, and journal the
                    02:00 timer uses. A first sync of a large repository legitimately takes hours
                    and is never killed for being long.
                </ConfirmModal>
                <ConfirmModal
                    title="Stop the running sync"
                    confirmLabel="Stop"
                    isOpen={confirming === 'stop'}
                    onClose={() => setConfirming(null)}
                    onConfirm={() => act(stopUnit(SYNC_SERVICE), true)}
                >
                    Everything already published stays published: each repository is its own
                    transaction. Partial downloads resume from the cache on the next run (AD-09),
                    and reconciliation handles the rest — it runs below after the stop.
                </ConfirmModal>
                <ConfirmModal
                    title="Pause the schedule"
                    confirmLabel="Stop hfcache-sync.timer"
                    isOpen={confirming === 'pause'}
                    onClose={() => setConfirming(null)}
                    onConfirm={() => act(stopUnit(SYNC_TIMER))}
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

const SelectorSync = ({ onInterrupted }: { onInterrupted: () => void }) => {
    const status = useHfcache(['status']);
    const [selected, setSelected] = useState<Record<string, boolean>>({});
    const [confirming, setConfirming] = useState(false);
    const [running, setRunning] = useState(false);
    const [feed, setFeed] = useState<string[]>([]);
    const [result, setResult] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);

    const repositories = (((status.envelope?.data ?? {}) as { repositories?: StatusRepositoryLite[] })
            .repositories ?? []).filter(repository => repository.managed && repository.enabled);
    const selectors = repositories
            .map(repository => formatSelector({ type: repository.repository_type, id: repository.repository_id }))
            .filter(selector => selected[selector] === true);

    const run = () => {
        setConfirming(false);
        setRunning(true);
        setFeed([]);
        setResult(null);
        setError(null);
        runHfcacheStreaming(['sync', ...selectors], {
            onLine: line => setFeed(previous => [...previous, line].slice(-200)),
        })
                .then(envelope => setResult(envelope),
                      failure => {
                          setError(failure as Error);
                          onInterrupted();
                      })
                .finally(() => setRunning(false));
    };

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
                            isDisabled={running || selectors.length === 0}
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
                                title="Running as a page process — keep this tab open"
                            />
                        </StackItem>}
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
                    isOpen={confirming}
                    onClose={() => setConfirming(false)}
                    onConfirm={run}
                >
                    This run is a page process, not a unit: closing the tab interrupts it.
                    Interruption is a designed crash shape — per-repository transactions,
                    resumable downloads (AD-09) — and reconciliation is surfaced afterwards,
                    but the full-archive run belongs to the unit above (CP-04).
                </ConfirmModal>
            </CardBody>
        </Card>
    );
};

export const SyncOperations = () => {
    const [showRecover, setShowRecover] = useState(false);
    const [scheduleGeneration, setScheduleGeneration] = useState(0);

    return (
        <Stack hasGutter>
            <StackItem>
                <SyncControls
                    key={scheduleGeneration}
                    onStopped={() => setShowRecover(true)}
                />
            </StackItem>
            <StackItem>
                <ScheduleEditor onApplied={() => setScheduleGeneration(value => value + 1)} />
            </StackItem>
            <StackItem><SelectorSync onInterrupted={() => setShowRecover(true)} /></StackItem>
            {showRecover && <StackItem><RecoverHint /></StackItem>}
        </Stack>
    );
};
