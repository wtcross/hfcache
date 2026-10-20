/* SPDX-License-Identifier: LGPL-2.1-or-later */
import React, { useEffect } from 'react';
import { Alert } from '@patternfly/react-core/dist/esm/components/Alert/index.js';
import { Button } from '@patternfly/react-core/dist/esm/components/Button/index.js';
import { Card, CardBody, CardTitle } from '@patternfly/react-core/dist/esm/components/Card/index.js';
import { Stack, StackItem } from '@patternfly/react-core/dist/esm/layouts/Stack/index.js';

import { lookupOriginalOperation, readClientAuthority, waitOriginalOperation } from './api/hfcache';
import { synchronizeConnection } from './api/connection';
import { currentOperationHost, operationRegistry } from './api/operations';
import { DataSummary, EnvelopeAlert, Loading, QueryError } from './components';
import { useConnection, useOperations } from './hooks';
import { operationCommands } from './lib/envelope';

/* This root lives above Tabs. Restored metadata never restores Apply readiness
 * or a candidate proposal; every recovery uses authenticated lookup/observation. */
export const OriginalOperations = () => {
    const { registry, views } = useOperations();
    const connection = useConnection();
    const host = currentOperationHost();
    useEffect(() => {
        if (synchronizeConnection() !== connection || host !== currentOperationHost()) return;
        if (connection.administrative)
            readClientAuthority().catch(() => undefined);
    }, [connection, host]);
    const fresh = views.authority.generation === connection.generation && connection.administrative && views.authority.scope?.host === host;
    const scope = fresh ? views.authority.scope : null;
    return (
        <Card aria-label="Original operation recovery">
            <CardTitle>Original operations</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>
                        Keys are recorded before submission. Switching tabs or ending observation does not cancel server work.
                        Session storage supports reloads in this browser tab; closing the session or clearing storage can lose handles.
                        Stored summaries are recovery metadata. Obtain the original authenticated result before relying on it.
                        Restored summaries remain unverified and block a new submission until original observation confirms them.
                    </StackItem>
                    {registry.error &&
                        <StackItem><Alert variant="warning" isInline title={registry.error} /></StackItem>}
                    {views.authority.error && <StackItem><QueryError error={views.authority.error} /></StackItem>}
                    <StackItem>
                        {scope &&
                            <p>
                                Client target: {scope.host}. Endpoint: <code>{scope.endpoint}</code>. Credential class: {scope.credentialClass}.
                                Archive UUID: {scope.archiveId ?? 'unconfirmed'}. Profile: <code>{scope.profile}</code>.
                            </p>}
                        {!scope && <p>Client authority is unavailable or stale; saved handles cannot be followed.</p>}
                        <Button
variant="link" isDisabled={!connection.administrative || views.authority.loading}
                            onClick={() => { readClientAuthority().catch(() => undefined) }}
                        >Refresh client authority
                        </Button>
                        {views.authority.loading && <Loading />}
                    </StackItem>
                    {registry.records.map(record => {
                        const current = views.records.get(record.key);
                        const allowed = scope !== null && operationRegistry.canRecover(record, scope);
                        const commands = operationCommands({
                            idempotencyKey: record.key,
                            ...(record.operationId ? { operationId: record.operationId } : {}),
                            workMayContinue: record.state !== 'terminal'
                        },
                                                           record.scope.authorityFingerprint);
                        return (
                            <StackItem key={record.key}>
                                <section aria-label={`Original ${record.action}`}>
                                    <p>{record.action}: {record.state}. Original key: <code>{record.key}</code></p>
                                    {record.operationId && <p>Original operation: <code>{record.operationId}</code></p>}
                                    <p>Original host: {record.scope.host}; archive: {record.scope.archiveId ?? 'unconfirmed'}.</p>
                                    {!allowed && <p>Original authority is changed, unconfirmed or conflicted. Preserve these handles for operator review.</p>}
                                    {record.state === 'missing' && <p>Missing or expired history does not prove nonexecution. No replacement was submitted.</p>}
                                    <Button
isDisabled={!allowed || current?.busy === true}
                                        onClick={() => { lookupOriginalOperation(record.key).catch(() => undefined) }}
                                    >Look up original key
                                    </Button>
                                    {' '}
                                    <Button
isDisabled={!allowed || current?.busy === true || record.operationId === null}
                                        onClick={() => { waitOriginalOperation(record.key).catch(() => undefined) }}
                                    >Observe original operation
                                    </Button>
                                    {current?.busy && <Loading />}
                                    <p><code>{commands.lookup}</code></p>
                                    {commands.wait && <p><code>{commands.wait}</code></p>}
                                    {current?.error && <QueryError error={current.error} />}
                                    {current?.envelope &&
                                        <>
                                            <EnvelopeAlert envelope={current.envelope} />
                                            {(record.state === 'terminal' || current.envelope.exit_code !== 0) &&
                                                <DataSummary data={current.envelope.data} />}
                                        </>}
                                    {record.terminal &&
                                        <p>Recorded summary: {record.terminal.command}, exit {record.terminal.exitCode},
                                            run <code>{record.terminal.runId}</code>.
                                        </p>}
                                </section>
                            </StackItem>
                        );
                    })}
                </Stack>
            </CardBody>
        </Card>
    );
};
