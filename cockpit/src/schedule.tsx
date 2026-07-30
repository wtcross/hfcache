/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The schedule editor (docs/cockpit.md §7): a managed drop-in, calendar
 * expressions validated by systemd-analyze before writing, and the shipped
 * semantics surfaced beside the controls because they are the contract the
 * schedule lives in.
 */

import React, { useCallback, useEffect, useState } from 'react';

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
import { daemonReload, restartUnit, SYNC_TIMER, unitState } from './api/systemd';
import { QueryError } from './components';
import { CalendarCheck, parseDropIn } from './lib/schedule';

const Item = ({ term, children }: { term: string; children: React.ReactNode }) => (
    <DescriptionListGroup>
        <DescriptionListTerm>{term}</DescriptionListTerm>
        <DescriptionListDescription>{children}</DescriptionListDescription>
    </DescriptionListGroup>
);

export const ScheduleEditor = ({ onApplied }: { onApplied: () => void }) => {
    const [current, setCurrent] = useState<string | null>(null);
    const [onCalendar, setOnCalendar] = useState('');
    const [delay, setDelay] = useState('');
    const [checked, setChecked] = useState<CalendarCheck | null>(null);
    const [checkError, setCheckError] = useState<Error | null>(null);
    const [confirming, setConfirming] = useState<'apply' | 'reset' | null>(null);
    const [busy, setBusy] = useState(false);
    const [actionError, setActionError] = useState<Error | null>(null);

    const load = useCallback(() => {
        readDropIn().then(content => {
            setCurrent(content);
            if (content !== null) {
                const parsed = parseDropIn(content);
                setOnCalendar(parsed.onCalendar ?? '');
                setDelay(parsed.randomizedDelaySec ?? '');
            }
        }, () => setCurrent(null));
    }, []);

    useEffect(load, [load]);

    const check = () => {
        setChecked(null);
        setCheckError(null);
        checkCalendar(onCalendar)
                .then(result => setChecked(result), failure => setCheckError(failure as Error));
    };

    const applySchedule = async (write: boolean) => {
        if (write)
            await writeDropIn(onCalendar, delay === '' ? null : delay);
        else
            await removeDropIn();
        await daemonReload();
        const state = await unitState(SYNC_TIMER);
        if (state.activeState === 'active')
            await restartUnit(SYNC_TIMER);
    };

    const act = (write: boolean) => {
        setConfirming(null);
        setBusy(true);
        setActionError(null);
        applySchedule(write)
                .then(() => {
                    setChecked(null);
                    load();
                    onApplied();
                }, failure => setActionError(failure as Error))
                .finally(() => setBusy(false));
    };

    return (
        <Card>
            <CardTitle>Schedule</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>
                        <DescriptionList isHorizontal isCompact>
                            <Item term="Shipped schedule">
                                <code>OnCalendar=*-*-* 02:00:00</code> local time (chosen against the
                                NAS maintenance windows), <code>RandomizedDelaySec=30m</code>,
                                <code>Persistent=true</code>
                            </Item>
                            <Item term="Override">
                                {current === null
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
                    <StackItem>
                        <Flex>
                            <FlexItem grow={{ default: 'grow' }}>
                                <TextInput
                                    id="schedule-oncalendar"
                                    aria-label="OnCalendar expression"
                                    placeholder="*-*-* 02:00:00"
                                    value={onCalendar}
                                    onChange={(_event, value) => {
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
                                    onChange={(_event, value) => setDelay(value)}
                                />
                            </FlexItem>
                            <FlexItem>
                                <Button
                                    variant="secondary"
                                    isDisabled={onCalendar === '' || busy}
                                    onClick={check}
                                >
                                    Check calendar
                                </Button>
                            </FlexItem>
                            <FlexItem>
                                <Button
                                    variant="primary"
                                    isDisabled={checked === null || busy}
                                    onClick={() => setConfirming('apply')}
                                >
                                    Apply override
                                </Button>
                            </FlexItem>
                            <FlexItem>
                                <Button
                                    variant="link"
                                    isDisabled={current === null || busy}
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
                    {actionError !== null && <StackItem><QueryError error={actionError} /></StackItem>}
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
                        <Button variant="primary" onClick={() => act(confirming === 'apply')}>
                            {confirming === 'apply' ? 'Write drop-in and apply' : 'Remove drop-in and apply'}
                        </Button>
                        <Button variant="link" onClick={() => setConfirming(null)}>Cancel</Button>
                    </ModalFooter>
                </Modal>
            </CardBody>
        </Card>
    );
};
