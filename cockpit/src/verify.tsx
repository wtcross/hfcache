/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Verification (docs/cockpit.md §3): estimate first — it sizes the window
 * and is always safe; one revision on a targeted suspicion; the full read
 * through the shared REST operation flow (CP-04). The quarterly timer is
 * displayed and never enabled from here (CP-06).
 */

import React, { useEffect, useRef, useState } from 'react';

import { Alert } from '@patternfly/react-core/dist/esm/components/Alert/index.js';
import { Button } from "@patternfly/react-core/dist/esm/components/Button/index.js";
import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import {
    DescriptionList, DescriptionListDescription, DescriptionListGroup, DescriptionListTerm,
} from "@patternfly/react-core/dist/esm/components/DescriptionList/index.js";
import {
    ExpandableSection,
} from "@patternfly/react-core/dist/esm/components/ExpandableSection/index.js";
import { Label } from "@patternfly/react-core/dist/esm/components/Label/index.js";
import { TextInput } from "@patternfly/react-core/dist/esm/components/TextInput/index.js";
import { Stack, StackItem } from "@patternfly/react-core/dist/esm/layouts/Stack/index.js";

import { ManualFullJob } from './manual-job';
import { hostActionAllowed } from './api/profile';
import { UnitActivity } from './activity';
import { runHfcache, runHfcacheStreaming } from './api/hfcache';
import { connectionSnapshot, synchronizeConnection } from './api/connection';
import { currentOperationHost, submissionBlocked } from './api/operations';
import { VERIFY_SERVICE, VERIFY_TIMER } from './api/systemd';
import { DataSummary, EnvelopeAlert, Loading, QueryError, RecoveryHandles } from './components';
import { useObservationSignal, useOperationHandles, useUnitPoll, useConnection, useOperations, useHostProfile } from './hooks';
import { parseSelector, SelectorError } from './lib/command';
import { classifyEnvelope, Envelope } from './lib/envelope';
import { formatBytes, formatDuration, formatTimestamp } from './lib/format';
import { appendDisplayLine } from './lib/stream';
import { parseEstimate } from './lib/estimate-read';
import { normalizeFailure } from './lib/failure';

const Item = ({ term, children }: { term: string; children: React.ReactNode }) => (
    <DescriptionListGroup>
        <DescriptionListTerm>{term}</DescriptionListTerm>
        <DescriptionListDescription>{children}</DescriptionListDescription>
    </DescriptionListGroup>
);

const EstimateCard = () => {
    const connection = useConnection();
    const host = currentOperationHost();
    const origin = JSON.stringify([connection, host]);
    const [readyOrigin, setReadyOrigin] = useState('');
    const [observedOrigin, setObservedOrigin] = useState('');
    const [running, setRunning] = useState(false);
    const [result, setResult] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const revision = useRef(0);
    const pending = useRef(false);
    const mounted = useRef(true);
    useEffect(() => {
        mounted.current = true;
        return () => { mounted.current = false };
    }, []);
    useEffect(() => {
        revision.current += 1;
        setResult(null); setError(null); setObservedOrigin(''); setReadyOrigin(origin);
        return () => { revision.current += 1 };
    }, [origin]);
    const run = () => {
        if (pending.current || readyOrigin !== origin || !connection.administrative ||
            connection !== connectionSnapshot() || host !== currentOperationHost()) return;
        pending.current = true;
        const request = ++revision.current;
        const current = () => request === revision.current && connection === connectionSnapshot() && host === currentOperationHost();
        setRunning(true); setResult(null); setError(null);
        runHfcache(['verify', '--estimate'])
                .then(envelope => {
                    if (current()) { setObservedOrigin(origin); setResult(envelope) }
                }, failure => {
                    if (current()) { setObservedOrigin(origin); setError(normalizeFailure(failure, { stage: 'api-read' })) }
                })
                .finally(() => {
                    pending.current = false;
                    if (mounted.current) setRunning(false);
                });
    };
    const shown = observedOrigin === origin ? result : null;
    const parsed = parseEstimate(shown);
    const data = parsed.payload;
    return (
        <Card>
            <CardTitle>Estimate</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>
                        Sizes the maintenance window from retained metadata. Takes no archive
                        lock and performs no hashing or verification persistence. Metadata reads
                        do not prove integrity, an available execution lane or workload acceptance.
                    </StackItem>
                    <StackItem>
                        <Button variant="secondary" isDisabled={running || readyOrigin !== origin || !connection.administrative} onClick={run}>
                            Run verify --estimate
                        </Button>
                    </StackItem>
                    {running && <StackItem><Loading /></StackItem>}
                    {observedOrigin === origin && error !== null && <StackItem><QueryError error={error} /></StackItem>}
                    {shown !== null && !running && <StackItem><EnvelopeAlert envelope={shown} /></StackItem>}
                    {parsed.error !== null && <StackItem><QueryError error={parsed.error} /></StackItem>}
                    {data !== null && !running &&
                        <StackItem>
                            {parsed.partial && <Alert variant="warning" isInline title="Partial estimate metadata">Informational only; the request failed and grants no execution readiness.</Alert>}
                            <DescriptionList isHorizontal isCompact>
                                <Item term="Repositories">{data.repositories}</Item>
                                <Item term="Revisions">{data.revisions}</Item>
                                <Item term="Unique objects">{data.unique_objects}</Item>
                                <Item term="Unique bytes">{formatBytes(data.unique_bytes)}</Item>
                                <Item term="Unreadable objects">{data.unreadable_objects}</Item>
                                <Item term="Estimated duration">{formatDuration(data.estimated_duration_seconds)}</Item>
                                <Item term="Measured throughput">
                                    {data.measured_throughput_bytes_per_second === null
                                        ? 'unknown — never measured'
                                        : `${formatBytes(data.measured_throughput_bytes_per_second)}/s`}
                                </Item>
                                <Item term="Storage maintenance">{data.storage_maintenance}</Item>
                            </DescriptionList>
                        </StackItem>}
                </Stack>
            </CardBody>
        </Card>
    );
};

const ACTIVE_STATES = ['active', 'activating', 'reloading', 'deactivating'];

const ScheduledVerifyCard = () => {
    const service = useUnitPoll(VERIFY_SERVICE);
    const running = ACTIVE_STATES.includes(service.state?.activeState ?? '');
    return (
        <Card>
            <CardTitle>Scheduled verification observer</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>System service state and journals describe the scheduled observer only. They do not establish the result of a manual server operation.</StackItem>
                    {service.loading && <StackItem><Loading /></StackItem>}
                    {service.error !== null && <StackItem><QueryError error={service.error} /></StackItem>}
                    {!service.loading && service.state === null && <StackItem>Scheduled observer state is unavailable.</StackItem>}
                    {service.state !== null &&
                    <StackItem>
                        <Label isCompact color={running ? 'blue' : 'grey'}>{service.state.activeState}</Label>
                        {' '}observer process result: {service.result?.result ?? '…'}
                        {service.result !== null && ` (exit ${service.result.execMainStatus})`}
                    </StackItem>}
                    {running && <StackItem><UnitActivity unit={VERIFY_SERVICE} /></StackItem>}
                </Stack>
            </CardBody>
        </Card>
    );
};

const RevisionVerifyCard = () => {
    const profile = useHostProfile();
    const connection = useConnection();
    const host = currentOperationHost();
    const operations = useOperations();
    const [selectorText, setSelectorText] = useState('');
    const [running, setRunning] = useState(false);
    const [feed, setFeed] = useState<string[]>([]);
    const [result, setResult] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const observationSignal = useObservationSignal();
    const { handles, reset: resetHandles, onNotice } = useOperationHandles();
    const submitted = useRef(false);

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
        if (synchronizeConnection() !== connection || host !== currentOperationHost()) return;
        if (submitted.current || running || submissionBlocked() || !connectionSnapshot().administrative || !hostActionAllowed('archive') || selectorText === '')
            return;
        try {
            if (parseSelector(selectorText).sha === undefined)
                return;
        } catch { return }
        submitted.current = true;
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
                .finally(() => {
                    submitted.current = false;
                    if (!signal.aborted) setRunning(false);
                });
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
                            isDisabled={running || uncertain || operations.blocked || !connection.administrative ||
                                !profile.permissions.archive || selectorText === '' || validationError !== null}
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
                {timer.loading && <Loading />}
                {timer.error !== null && <QueryError error={timer.error} />}
                {!timer.loading && timer.state === null && <p>Scheduled verification timer state is unavailable.</p>}
                <DescriptionList isHorizontal isCompact>
                    <Item term="hfcache-verify.timer">
                        <Label isCompact color="grey">{timer.state?.unitFileState ?? 'unavailable'}</Label>
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
        <StackItem><ManualFullJob mode="verify-full" /></StackItem>
        <StackItem><ScheduledVerifyCard /></StackItem>
        <StackItem><RevisionVerifyCard /></StackItem>
        <StackItem><VerifyTimerCard /></StackItem>
    </Stack>
);
