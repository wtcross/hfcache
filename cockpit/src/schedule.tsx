/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The schedule editor (docs/cockpit.md §7): a managed drop-in, calendar
 * expressions validated by systemd-analyze before writing, and the shipped
 * semantics surfaced beside the controls because they are the contract the
 * schedule lives in.
 */

import React, { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import cockpit from 'cockpit';

import { Alert } from "@patternfly/react-core/dist/esm/components/Alert/index.js";
import { Button } from "@patternfly/react-core/dist/esm/components/Button/index.js";
import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import {
    DescriptionList, DescriptionListDescription, DescriptionListGroup, DescriptionListTerm,
} from "@patternfly/react-core/dist/esm/components/DescriptionList/index.js";
import {
    Modal, ModalBody, ModalFooter, ModalHeader,
} from "@patternfly/react-core/dist/esm/components/Modal/index.js";
import { TextInput } from "@patternfly/react-core/dist/esm/components/TextInput/index.js";
import { Flex, FlexItem } from "@patternfly/react-core/dist/esm/layouts/Flex/index.js";
import { Stack, StackItem } from "@patternfly/react-core/dist/esm/layouts/Stack/index.js";

import { checkCalendar, readDropIn, removeDropIn, writeDropIn } from './api/schedule';
import { daemonReload, restartUnit, SYNC_TIMER, unitState, UnitState } from './api/systemd';
import { QueryError } from './components';
import { useConnection, useHostProfile } from './hooks';
import { hostActionAllowed, hostActionReason } from './api/profile';
import { assertSession, captureSession, connectionSnapshot, synchronizeConnection } from './api/connection';
import { normalizeFailure } from './lib/failure';
import { AcknowledgedHostChangeError, HostProfileError } from './lib/host-profile';
import { CalendarCheck, parseDropIn, renderDropIn } from './lib/schedule';
import { MAX_SCHEDULE_ATTEMPTS, scheduleSession, ScheduleSessionError } from './lib/schedule-session';
import type { ScheduleAttempt } from './lib/schedule-session';

const Item = ({ term, children }: { term: string; children: React.ReactNode }) => (
    <DescriptionListGroup>
        <DescriptionListTerm>{term}</DescriptionListTerm>
        <DescriptionListDescription>{children}</DescriptionListDescription>
    </DescriptionListGroup>
);

interface ScheduleInspection {
    matches: boolean;
    unit: UnitState;
    generation: number;
    host: string;
}

function knownTimer(state: UnitState): boolean {
    return ['active', 'inactive', 'failed'].includes(state.activeState) &&
        ['enabled', 'enabled-runtime', 'disabled', 'static', 'linked', 'linked-runtime'].includes(state.unitFileState);
}

export const ScheduleEditor = ({ onApplied }: { onApplied: () => void }) => {
    const connection = useConnection();
    const profile = useHostProfile();
    const allowed = profile.permissions.schedule;
    const submitted = useRef(false);
    const checkRevision = useRef(0);
    const attempts = useSyncExternalStore(scheduleSession.subscribe, scheduleSession.snapshot);
    const attempted = attempts.find(attempt => attempt.host === cockpit.transport.host) ?? null;
    const capacityBlocked = attempted === null && attempts.length >= MAX_SCHEDULE_ATTEMPTS;
    const [inspection, setInspection] = useState<ScheduleInspection | null>(null);
    const [inspectionError, setInspectionError] = useState<Error | null>(null);
    const [current, setCurrent] = useState<string | null>(null);
    const [onCalendar, setOnCalendar] = useState('');
    const [delay, setDelay] = useState('');
    const [checked, setChecked] = useState<CalendarCheck | null>(null);
    const [checkError, setCheckError] = useState<Error | null>(null);
    const [confirming, setConfirming] = useState<'apply' | 'reset' | null>(null);
    const [localBusy, setBusy] = useState(false);
    const busy = localBusy || attempted?.state === 'pending';
    const [localActionError, setActionError] = useState<Error | null>(null);
    const actionError = attempted?.error ?? localActionError;
    const [localRestrictionReason, setRestrictionReason] = useState<string | null>(null);
    const restrictionReason = attempted?.restrictionReason ?? localRestrictionReason;
    const [readError, setReadError] = useState<Error | null>(null);
    const [readRevision, setReadRevision] = useState(0);
    const [observedOrigin, setObservedOrigin] = useState('');
    const host = cockpit.transport.host;
    const readOrigin = JSON.stringify([host, connection.generation, connection.administrative, readRevision]);
    const fresh = connection.administrative && observedOrigin === readOrigin;

    const load = useCallback(() => {
        setReadRevision(value => value + 1);
    }, []);

    useEffect(() => {
        let cancelled = false;
        setCurrent(null);
        setObservedOrigin('');
        setReadError(null);
        if (connection.administrative && synchronizeConnection().generation === connection.generation) {
            const generation = connection.generation;
            readDropIn().then(content => {
                if (cancelled || generation !== connectionSnapshot().generation || host !== cockpit.transport.host)
                    return;
                setCurrent(content);
                if (content !== null) {
                    const parsed = parseDropIn(content);
                    setOnCalendar(parsed.onCalendar ?? '');
                    setDelay(parsed.randomizedDelaySec ?? '');
                }
                setObservedOrigin(readOrigin);
            }, failure => {
                if (!cancelled && generation === connectionSnapshot().generation && host === cockpit.transport.host)
                    setReadError(normalizeFailure(failure, { stage: 'schedule-read' }));
            });
        }
        return () => {
            cancelled = true;
        };
    }, [connection.generation, connection.administrative, readOrigin, host]);
    useEffect(() => {
        checkRevision.current += 1;
        setChecked(null);
        setConfirming(null);
        setInspection(null);
    }, [connection.generation]);

    const check = () => {
        if (synchronizeConnection() !== connection || host !== cockpit.transport.host) return;
        const revision = ++checkRevision.current;
        const generation = connectionSnapshot().generation;
        setChecked(null);
        setCheckError(null);
        checkCalendar(onCalendar)
                .then(result => {
                    if (revision === checkRevision.current && generation === connectionSnapshot().generation)
                        setChecked(result);
                }, failure => {
                    if (revision === checkRevision.current && generation === connectionSnapshot().generation)
                        setCheckError(failure as Error);
                });
    };

    const applySchedule = async (write: boolean, attempt: Readonly<ScheduleAttempt>) => {
        const generation = captureSession('schedule-write');
        const host = cockpit.transport.host;
        if (attempt.host !== host)
            throw new HostProfileError();
        let acknowledged = false;
        try {
            if (write)
                await writeDropIn(onCalendar, delay === '' ? null : delay);
            else
                await removeDropIn();
            acknowledged = true;
            assertSession(generation, 'schedule-write', true);
            if (host !== cockpit.transport.host)
                throw new HostProfileError();
            await daemonReload();
            assertSession(generation, 'schedule-write', true);
            const state = await unitState(SYNC_TIMER);
            assertSession(generation, 'schedule-write', true);
            if (host !== cockpit.transport.host)
                throw new HostProfileError();
            if (state.activeState === 'active')
                await restartUnit(SYNC_TIMER);
        } catch (failure) {
            throw acknowledged ? new AcknowledgedHostChangeError(failure, 'schedule-write') : failure;
        }
    };

    const uncertain = attempted?.state === 'uncertain';
    const inspected = inspection !== null && inspection.matches && knownTimer(inspection.unit) &&
        inspection.generation === connection.generation && inspection.host === cockpit.transport.host && connection.administrative;

    const inspect = async () => {
        if (!uncertain || busy || !attempted || !connectionSnapshot().administrative)
            return;
        const attempt = attempted;
        const generation = captureSession('schedule-read');
        const host = cockpit.transport.host;
        setBusy(true);
        setInspection(null);
        setInspectionError(null);
        try {
            if (attempt.host !== host)
                throw new HostProfileError();
            const content = await readDropIn();
            const unit = await unitState(SYNC_TIMER);
            assertSession(generation, 'schedule-read');
            if (host !== cockpit.transport.host || !scheduleSession.snapshot().some(record => record.id === attempt.id))
                throw new HostProfileError();
            setInspection({ matches: content === attempt.expected, unit, generation, host });
            setCurrent(content);
            setObservedOrigin(readOrigin);
        } catch (failure) {
            setInspectionError(failure as Error);
        } finally {
            setBusy(false);
        }
    };

    const acknowledge = () => {
        if (synchronizeConnection() !== connection || host !== cockpit.transport.host) return;
        if (!uncertain || !inspected || busy || !inspection ||
            !attempted || inspection.host !== cockpit.transport.host || attempted.host !== inspection.host ||
            inspection.generation !== connectionSnapshot().generation || !connectionSnapshot().administrative)
            return;
        checkRevision.current += 1;
        setChecked(null);
        setActionError(actionError);
        setRestrictionReason(restrictionReason);
        scheduleSession.acknowledge(attempted);
    };

    const act = (write: boolean) => {
        if (synchronizeConnection() !== connection || host !== cockpit.transport.host) return;
        if (!fresh || attempted !== null || capacityBlocked || busy || submitted.current || !hostActionAllowed('schedule'))
            return;
        let attempt: Readonly<ScheduleAttempt>;
        try {
            attempt = scheduleSession.begin(cockpit.transport.host,
                                            write ? renderDropIn(onCalendar, delay === '' ? null : delay) : null);
        } catch (failure) {
            setActionError(failure as Error);
            return;
        }
        submitted.current = true;
        setInspection(null);
        setInspectionError(null);
        setConfirming(null);
        setBusy(true);
        setActionError(null);
        setRestrictionReason(null);
        applySchedule(write, attempt)
                .then(() => {
                    scheduleSession.complete(attempt);
                    setChecked(null);
                    load();
                    onApplied();
                }, failure => {
                    scheduleSession.fail(attempt, failure);
                    setActionError(failure as Error);
                    setRestrictionReason(failure instanceof AcknowledgedHostChangeError ? failure.restrictionReason : null);
                })
                .finally(() => {
                    submitted.current = false;
                    setBusy(false);
                });
    };

    return (
        <Card>
            <CardTitle>Schedule</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    {!allowed &&
                        <StackItem><Alert variant="warning" isInline title={hostActionReason('schedule')} /></StackItem>}
                    <StackItem>
                        <DescriptionList isHorizontal isCompact>
                            <Item term="Shipped schedule">
                                <code>OnCalendar=*-*-* 02:00:00</code> local time (chosen against the
                                NAS maintenance windows), <code>RandomizedDelaySec=30m</code>,
                                <code>Persistent=true</code>
                            </Item>
                            <Item term="Override">
                                {!fresh
                                    ? 'unavailable — obtain a fresh schedule read before changing it'
                                    : current === null
                                        ? 'none — the shipped schedule is in effect'
                                        : 'managed drop-in active (50-cockpit.conf)'}
                            </Item>
                            <Item term="Semantics">
                                Persistent replays an elapse missed while the host was down; an
                                elapse during a running sync merges into it and the day is skipped —
                                designed observation semantics (AD-02/AD-03), not a fault.
                            </Item>
                        </DescriptionList>
                    </StackItem>
                    {readError !== null && <StackItem><QueryError error={readError} /></StackItem>}
                    <StackItem>
                        <Flex>
                            <FlexItem grow={{ default: 'grow' }}>
                                <TextInput
                                    id="schedule-oncalendar"
                                    aria-label="OnCalendar expression"
                                    placeholder="*-*-* 02:00:00"
                                    value={onCalendar}
                                    isDisabled={!allowed || busy}
                                    onChange={(_event, value) => {
                                        checkRevision.current += 1;
                                        setOnCalendar(value);
                                        setChecked(null);
                                    }}
                                />
                            </FlexItem>
                            <FlexItem>
                                <TextInput
                                    id="schedule-delay"
                                    aria-label="RandomizedDelaySec"
                                    placeholder="RandomizedDelaySec (optional, e.g. 30m)"
                                    value={delay}
                                    isDisabled={!allowed || busy}
                                    onChange={(_event, value) => {
                                        checkRevision.current += 1;
                                        setChecked(null);
                                        setDelay(value);
                                    }}
                                />
                            </FlexItem>
                            <FlexItem>
                                <Button
                                    variant="secondary"
                                    isDisabled={onCalendar === '' || busy || !fresh || !allowed}
                                    onClick={check}
                                >
                                    Check calendar
                                </Button>
                            </FlexItem>
                            <FlexItem>
                                <Button
                                    variant="primary"
                                    isDisabled={checked === null || busy || uncertain || capacityBlocked || !fresh || !allowed}
                                    onClick={() => setConfirming('apply')}
                                >
                                    Apply override
                                </Button>
                            </FlexItem>
                            <FlexItem>
                                <Button
                                    variant="link"
                                    isDisabled={current === null || busy || uncertain || capacityBlocked || !fresh || !allowed}
                                    onClick={() => setConfirming('reset')}
                                >
                                    Reset to shipped schedule
                                </Button>
                            </FlexItem>
                        </Flex>
                    </StackItem>
                    {checkError !== null && <StackItem><QueryError error={checkError} /></StackItem>}
                    {checked !== null &&
                        <StackItem>
                            <Alert
                                variant="info"
                                isInline
                                title={`Normalized: ${checked.normalized ?? '?'} — next elapse ${checked.next ?? '?'}`}
                            />
                        </StackItem>}
                    {actionError instanceof ScheduleSessionError
                        ? <StackItem><Alert variant="warning" isInline title={actionError.message} /></StackItem>
                        : actionError !== null && <StackItem><QueryError error={actionError} /></StackItem>}
                    {capacityBlocked && <StackItem>Schedule recovery memory is full. Preserve and reconcile the retained attempts before another change.</StackItem>}
                    {restrictionReason && <StackItem>{restrictionReason}</StackItem>}
                    {uncertain &&
                        <StackItem>
                            <Alert variant="warning" isInline title="Schedule change requires read-only reconciliation">
                                A host change may have completed before the later failure. Preserve the original error.
                                Inspect the captured drop-in state and fixed timer before another deliberate change.
                            </Alert>
                            <Button isDisabled={busy || !connection.administrative} onClick={() => { inspect() }}>
                                Inspect changed schedule
                            </Button>
                        </StackItem>}
                    {inspectionError && <StackItem><QueryError error={inspectionError} /></StackItem>}
                    {inspection &&
                        <StackItem>
                            <p>Stored drop-in: {inspection.matches ? 'matches the captured attempt' : 'changed or unavailable'}.
                                Timer: {knownTimer(inspection.unit) ? `${inspection.unit.activeState}, ${inspection.unit.unitFileState}` : 'unavailable or masked'}.
                            </p>
                            <p>This inspection does not establish the loaded calendar or success of the earlier reload/restart.
                                Resolve manager application through the operator runbook. Inspection and acknowledgement perform no reload or restart.
                            </p>
                            {uncertain &&
                                <Button isDisabled={busy || !inspected} onClick={acknowledge}>
                                    Acknowledge inspected schedule
                                </Button>}
                        </StackItem>}
                </Stack>

                <Modal
                    isOpen={confirming !== null}
                    onClose={() => setConfirming(null)}
                    variant="small"
                    aria-label="Confirm schedule change"
                >
                    <ModalHeader
                        title={confirming === 'apply' ? 'Apply schedule override' : 'Reset to shipped schedule'}
                    />
                    <ModalBody>
                        Writes only the managed drop-in — the shipped unit file is never edited
                        (CP-12) — then reloads systemd and restarts the timer to apply. If the
                        new calendar already elapsed while the timer was stopped, Persistent=true
                        fires one run immediately on restart.
                    </ModalBody>
                    <ModalFooter>
                        <Button variant="primary" isDisabled={busy || uncertain || capacityBlocked || !fresh || !allowed} onClick={() => act(confirming === 'apply')}>
                            {confirming === 'apply' ? 'Write drop-in and apply' : 'Remove drop-in and apply'}
                        </Button>
                        <Button variant="link" onClick={() => setConfirming(null)}>Cancel</Button>
                    </ModalFooter>
                </Modal>
            </CardBody>
        </Card>
    );
};
