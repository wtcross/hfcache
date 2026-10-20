/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Manual full jobs use the same scoped REST operation flow as selected jobs.
 */
import React, { useEffect, useRef, useState } from 'react';

import { Alert } from '@patternfly/react-core/dist/esm/components/Alert/index.js';
import { Button } from '@patternfly/react-core/dist/esm/components/Button/index.js';
import { Card, CardBody, CardTitle } from '@patternfly/react-core/dist/esm/components/Card/index.js';
import { Modal, ModalBody, ModalFooter, ModalHeader } from '@patternfly/react-core/dist/esm/components/Modal/index.js';
import { Stack, StackItem } from '@patternfly/react-core/dist/esm/layouts/Stack/index.js';

import { synchronizeConnection } from './api/connection';
import type { ConnectionSnapshot } from './api/connection';
import { runHfcacheStreaming } from './api/hfcache';
import { currentOperationHost, submissionBlocked } from './api/operations';
import { hostActionAllowed } from './api/profile';
import { DataSummary, EnvelopeAlert, QueryError, RecoveryHandles } from './components';
import { useConnection, useHostProfile, useOperationHandles, useOperations } from './hooks';
import { classifyEnvelope, Envelope } from './lib/envelope';
import { appendDisplayLine } from './lib/stream';

export const ManualFullJob = ({ mode }: { mode: 'sync' | 'verify-full' }) => {
    const connection = useConnection();
    const host = currentOperationHost();
    const profile = useHostProfile();
    const operations = useOperations();
    const [confirmation, setConfirmation] = useState<{ host: string; connection: ConnectionSnapshot } | null>(null);
    const [running, setRunning] = useState(false);
    const [detached, setDetached] = useState(false);
    const [feed, setFeed] = useState<string[]>([]);
    const [result, setResult] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const { handles, reset, onNotice } = useOperationHandles();
    const controller = useRef<AbortController | null>(null);
    const submitted = useRef(false);
    useEffect(() => () => controller.current?.abort(), []);
    const confirmationReady = confirmation?.connection === connection && confirmation.host === host;
    const verification = mode === 'verify-full';
    const action = verification ? 'full verification' : 'full sync';
    const uncertain = (result !== null && classifyEnvelope(result) === 'observation') ||
        (error !== null && (handles.idempotencyKey !== undefined || handles.operationId !== undefined));
    const disabled = running || detached || uncertain || operations.blocked ||
        !connection.administrative || !profile.permissions.archive;

    const run = () => {
        if (synchronizeConnection() !== connection || host !== currentOperationHost()) return;
        if (!confirmationReady || submitted.current || running || detached || uncertain || submissionBlocked() ||
            !connection.administrative || !hostActionAllowed('archive'))
            return;
        submitted.current = true;
        const observing = new AbortController();
        controller.current = observing;
        const { signal } = observing;
        setConfirmation(null);
        setRunning(true);
        setFeed([]);
        setResult(null);
        setError(null);
        reset();
        runHfcacheStreaming(verification ? ['verify', '--full'] : ['sync'], {
            signal,
            onNotice,
            onLine: line => setFeed(previous => appendDisplayLine(previous, line)),
        }).then(envelope => {
            if (!signal.aborted)
                setResult(envelope);
        }, failure => {
            if (!signal.aborted)
                setError(failure as Error);
        })
                .finally(() => {
                    submitted.current = false;
                    if (!signal.aborted)
                        setRunning(false);
                });
    };

    const detach = () => {
        controller.current?.abort();
        setDetached(true);
        setRunning(false);
    };

    return (
        <Card>
            <CardTitle>{verification ? 'Manual full verification' : 'Manual full synchronization'}</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>
                        {verification
                            ? 'Re-reads every unique retained object in the server’s offline private executor. Exit 40 reports possible corruption; findings are never repaired from here.'
                            : 'Submits one full synchronization to the API using the installed client. The server executes accepted work independently of this view.'}
                    </StackItem>
                    {!profile.permissions.archive && <StackItem><Alert variant="warning" isInline title="Archive jobs unavailable">{profile.reason}</Alert></StackItem>}
                    <StackItem><Button variant="primary" isDisabled={disabled} onClick={() => setConfirmation({ host, connection })}>Run {action}</Button></StackItem>
                    {running && <StackItem><Button variant="secondary" onClick={detach}>Detach manual display</Button></StackItem>}
                    {(running || detached) &&
                        <StackItem>
                            <Alert variant="info" isInline title={detached ? 'Manual display detached' : 'Observing a manual server operation'}>
                                Accepted work may continue. Detaching or closing this view never cancels execution or stops a scheduled observer. Use the original operation recovery controls to reconnect.
                            </Alert>
                        </StackItem>}
                    <StackItem><RecoveryHandles evidence={handles} /></StackItem>
                    {feed.length > 0 && <StackItem><pre className="hfcache-journal">{feed.join('\n')}</pre></StackItem>}
                    {error !== null && <StackItem><QueryError error={error} /></StackItem>}
                    {result !== null &&
                        <>
                            <StackItem><EnvelopeAlert envelope={result} /></StackItem>
                            <StackItem><DataSummary data={result.data} /></StackItem>
                        </>}
                </Stack>
                <Modal isOpen={confirmationReady} onClose={() => setConfirmation(null)} variant="small" aria-label={'Start ' + action}>
                    <ModalHeader title={'Start ' + action} />
                    <ModalBody>
                        {verification ? 'Run the estimate first and review storage maintenance windows. ' : ''}
                        Submits one keyed REST operation. Closing or detaching this display does not cancel accepted work. Scheduled service state and journals are separate host observations.
                    </ModalBody>
                    <ModalFooter>
                        <Button variant="primary" isDisabled={disabled || !confirmationReady} onClick={run}>Start {action}</Button>
                        <Button variant="link" onClick={() => setConfirmation(null)}>Cancel</Button>
                    </ModalFooter>
                </Modal>
            </CardBody>
        </Card>
    );
};
