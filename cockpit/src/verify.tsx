/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Verification (docs/cockpit.md §3): estimate first — it sizes the window
 * and is always safe; one revision on a targeted suspicion; the full read
 * only through hfcache-verify.service (CP-04). The quarterly timer is
 * displayed and never enabled from here (CP-06).
 */

import React, { useState } from 'react';

import { Button } from "@patternfly/react-core/dist/esm/components/Button/index.js";
import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import {
    DescriptionList, DescriptionListDescription, DescriptionListGroup, DescriptionListTerm,
} from "@patternfly/react-core/dist/esm/components/DescriptionList/index.js";
import {
    ExpandableSection,
} from "@patternfly/react-core/dist/esm/components/ExpandableSection/index.js";
import { Label } from "@patternfly/react-core/dist/esm/components/Label/index.js";
import {
    Modal, ModalBody, ModalFooter, ModalHeader,
} from "@patternfly/react-core/dist/esm/components/Modal/index.js";
import { TextInput } from "@patternfly/react-core/dist/esm/components/TextInput/index.js";
import { Flex, FlexItem } from "@patternfly/react-core/dist/esm/layouts/Flex/index.js";
import { Stack, StackItem } from "@patternfly/react-core/dist/esm/layouts/Stack/index.js";

import { UnitActivity } from './activity';
import { runHfcache, runHfcacheStreaming } from './api/hfcache';
import { startUnit, VERIFY_SERVICE, VERIFY_TIMER } from './api/systemd';
import { DataSummary, EnvelopeAlert, Loading, QueryError, RecoveryHandles } from './components';
import { useObservationSignal, useOperationHandles, useUnitPoll } from './hooks';
import { parseSelector, SelectorError } from './lib/command';
import { classifyEnvelope, Envelope } from './lib/envelope';
import { formatBytes, formatDuration, formatTimestamp } from './lib/format';
import { appendDisplayLine } from './lib/stream';

const Item = ({ term, children }: { term: string; children: React.ReactNode }) => (
    <DescriptionListGroup>
        <DescriptionListTerm>{term}</DescriptionListTerm>
        <DescriptionListDescription>{children}</DescriptionListDescription>
    </DescriptionListGroup>
);

interface EstimateData {
    repositories?: number;
    revisions?: number;
    unique_objects?: number;
    unique_bytes?: number;
    unreadable_objects?: number;
    measured_throughput_bytes_per_second?: number | null;
    estimated_duration_seconds?: number | null;
    storage_maintenance?: string;
}

const EstimateCard = () => {
    const [running, setRunning] = useState(false);
    const [result, setResult] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);

    const run = () => {
        setRunning(true);
        setError(null);
        runHfcache(['verify', '--estimate'])
                .then(envelope => setResult(envelope), failure => setError(failure as Error))
                .finally(() => setRunning(false));
    };

    const data = (result?.data ?? {}) as EstimateData;

    return (
        <Card>
            <CardTitle>Estimate</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>
                        Sizes the maintenance window from retained metadata. Takes no archive
                        lock and performs no hashing or verification persistence.
                    </StackItem>
                    <StackItem>
                        <Button variant="secondary" isDisabled={running} onClick={run}>
                            Run verify --estimate
                        </Button>
                    </StackItem>
                    {running && <StackItem><Loading /></StackItem>}
                    {error !== null && <StackItem><QueryError error={error} /></StackItem>}
                    {result !== null && !running &&
                        <StackItem>
                            <DescriptionList isHorizontal isCompact>
                                <Item term="Repositories">{data.repositories ?? '—'}</Item>
                                <Item term="Revisions">{data.revisions ?? '—'}</Item>
                                <Item term="Unique objects">{data.unique_objects ?? '—'}</Item>
                                <Item term="Unique bytes">{formatBytes(data.unique_bytes)}</Item>
                                <Item term="Estimated duration">
                                    {formatDuration(data.estimated_duration_seconds)}
                                </Item>
                                <Item term="Measured throughput">
                                    {data.measured_throughput_bytes_per_second == null
                                        ? 'unknown'
                                        : `${formatBytes(data.measured_throughput_bytes_per_second)}/s`}
                                </Item>
                                <Item term="Storage maintenance">{data.storage_maintenance ?? '—'}</Item>
                            </DescriptionList>
                        </StackItem>}
                </Stack>
            </CardBody>
        </Card>
    );
};

const ACTIVE_STATES = ['active', 'activating', 'reloading', 'deactivating'];

const FullVerifyCard = () => {
    const service = useUnitPoll(VERIFY_SERVICE);
    const [confirming, setConfirming] = useState(false);
    const [actionError, setActionError] = useState<Error | null>(null);

    const running = ACTIVE_STATES.includes(service.state?.activeState ?? '');

    const start = () => {
        setConfirming(false);
        setActionError(null);
        startUnit(VERIFY_SERVICE)
                .then(() => service.refresh(), failure => setActionError(failure as Error));
    };

    return (
        <Card>
            <CardTitle>Full verification</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>
                        Re-reads every unique retained object against its manifest, offline —
                        the private server executor has Hub networking disabled. The installed
                        service observes its operation. Exit 40 means the archive
                        may be corrupt: findings are never repaired from here (AD-13).
                    </StackItem>
                    {actionError !== null && <StackItem><QueryError error={actionError} /></StackItem>}
                    <StackItem>
                        <Flex>
                            <FlexItem>
                                <Label isCompact color={running ? 'blue' : 'grey'}>
                                    {service.state?.activeState ?? '…'}
                                </Label>
                                {' '}last result: {service.result?.result ?? '…'}
                                {service.result !== null && ` (exit ${service.result.execMainStatus})`}
                            </FlexItem>
                            <FlexItem>
                                <Button
                                    variant="primary"
                                    isDisabled={running}
                                    onClick={() => setConfirming(true)}
                                >
                                    Run full verification
                                </Button>
                            </FlexItem>
                        </Flex>
                    </StackItem>
                    {running && <StackItem><UnitActivity unit={VERIFY_SERVICE} /></StackItem>}
                </Stack>

                <Modal
                    isOpen={confirming}
                    onClose={() => setConfirming(false)}
                    variant="small"
                    aria-label="Start full verification"
                >
                    <ModalHeader title="Start full verification" />
                    <ModalBody>
                        Runs hfcache-verify.service (CP-04). It shares the one application lock
                        with sync, prune, and repair. The server's configured queue/lock budget
                        applies before execution; a stopped client does not cancel accepted
                        verification. Run the estimate first and check it does not overlap
                        storage maintenance (HFWRN010).
                    </ModalBody>
                    <ModalFooter>
                        <Button variant="primary" onClick={start}>Start hfcache-verify.service</Button>
                        <Button variant="link" onClick={() => setConfirming(false)}>Cancel</Button>
                    </ModalFooter>
                </Modal>
            </CardBody>
        </Card>
    );
};

const RevisionVerifyCard = () => {
    const [selectorText, setSelectorText] = useState('');
    const [running, setRunning] = useState(false);
    const [feed, setFeed] = useState<string[]>([]);
    const [result, setResult] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const observationSignal = useObservationSignal();
    const { handles, reset: resetHandles, onNotice } = useOperationHandles();

    let validationError: string | null = null;
    if (selectorText !== '') {
        try {
            const selector = parseSelector(selectorText);
            if (selector.sha === undefined)
                validationError = 'a revision verify needs TYPE:ID@SHA with the full 40-character commit SHA';
        } catch (failure) {
            validationError = failure instanceof SelectorError ? failure.message : String(failure);
        }
    }

    const run = () => {
        const signal = observationSignal();
        setRunning(true);
        setFeed([]);
        setResult(null);
        setError(null);
        resetHandles();
        runHfcacheStreaming(['verify', '--revision', selectorText], {
            signal,
            onNotice,
            onLine: line => setFeed(previous => appendDisplayLine(previous, line, 100)),
        })
                .then(envelope => { if (!signal.aborted) setResult(envelope); },
                      failure => { if (!signal.aborted) setError(failure as Error); })
                .finally(() => { if (!signal.aborted) setRunning(false); });
    };

    const uncertain = (result !== null && classifyEnvelope(result) === 'observation') ||
        (error !== null && (handles.idempotencyKey !== undefined || handles.operationId !== undefined));

    return (
        <Card>
            <CardTitle>Verify one revision</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>
                        The mode for a targeted suspicion. Reads that one revision's bytes in
                        the offline server executor. Closing the tab detaches this view;
                        accepted verification may still persist its report and catalog. Retain
                        the operation handles to reconnect. Copy the full SHA from the
                        Repositories tab.
                    </StackItem>
                    <StackItem>
                        <TextInput
                            id="verify-revision-selector"
                            aria-label="Revision selector"
                            placeholder="model:organization/name@0123456789abcdef0123456789abcdef01234567"
                            value={selectorText}
                            validated={validationError === null ? 'default' : 'error'}
                            onChange={(_event, value) => setSelectorText(value)}
                        />
                        {validationError !== null &&
                            <div className="hfcache-issue-guidance">{validationError}</div>}
                    </StackItem>
                    <StackItem>
                        <Button
                            variant="secondary"
                            isDisabled={running || uncertain || selectorText === '' || validationError !== null}
                            onClick={run}
                        >
                            Run verify --revision
                        </Button>
                    </StackItem>
                    {running && <StackItem><Loading /></StackItem>}
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
            </CardBody>
        </Card>
    );
};

const VerifyTimerCard = () => {
    const timer = useUnitPoll(VERIFY_TIMER, 30000);
    return (
        <Card>
            <CardTitle>Quarterly timer — display only</CardTitle>
            <CardBody>
                <DescriptionList isHorizontal isCompact>
                    <Item term="hfcache-verify.timer">
                        <Label isCompact color="grey">{timer.state?.unitFileState ?? '…'}</Label>
                    </Item>
                    <Item term="Next elapse">
                        {formatTimestamp(timer.timer?.nextElapse?.toISOString())}
                    </Item>
                    <Item term="Why display only">
                        Installed and disabled pending confirmation that the quarterly calendar
                        does not overlap NAS scrub, SMART, or replication windows — an operator
                        decision (handoff item 8). The plugin never enables it (CP-06);
                        evaluate a calendar with systemd-analyze, then enable it deliberately
                        from a shell.
                    </Item>
                </DescriptionList>
            </CardBody>
        </Card>
    );
};

export const Verification = () => (
    <Stack hasGutter>
        <StackItem><EstimateCard /></StackItem>
        <StackItem><FullVerifyCard /></StackItem>
        <StackItem><RevisionVerifyCard /></StackItem>
        <StackItem><VerifyTimerCard /></StackItem>
    </Stack>
);
