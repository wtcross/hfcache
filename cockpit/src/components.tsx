/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Shared presentational pieces: envelopes render the same way on every
 * surface (docs/cockpit.md §4).
 */

import React from 'react';

import { Alert } from "@patternfly/react-core/dist/esm/components/Alert/index.js";
import {
    DescriptionList, DescriptionListDescription, DescriptionListGroup, DescriptionListTerm,
} from "@patternfly/react-core/dist/esm/components/DescriptionList/index.js";
import { Label } from "@patternfly/react-core/dist/esm/components/Label/index.js";
import { Spinner } from "@patternfly/react-core/dist/esm/components/Spinner/index.js";

import {
    classifyEnvelope, Envelope, EnvelopeIssue, EXIT_CODE_GUIDANCE, OperationEvidence,
    operationCommands, operationEvidence, readOperationEvidence, ResultKind,
} from './lib/envelope';
import { WARNING_GUIDANCE } from './lib/warnings';
import { normalizeFailure } from './lib/failure';
import { OperationRegistryError } from './lib/operation-registry';
import { OperationAuthorityError } from './lib/operation-authority';
import { HfcacheSpawnError } from './lib/runner';

type AlertVariant = 'success' | 'info' | 'warning' | 'danger';

export const ALERT_VARIANT: Record<ResultKind, AlertVariant> = {
    success: 'success',
    warnings: 'warning',
    invalid: 'warning',
    busy: 'info',
    refused: 'danger',
    observation: 'warning',
    sync_failures: 'warning',
    integrity: 'danger',
    maintenance: 'warning',
    unknown: 'danger',
};

/* Issues render with their stable code, and warnings carry the ops §8
 * response inline — the UI teaches the runbook (docs/cockpit.md §3). */
export const IssueRows = ({ issues }: { issues: EnvelopeIssue[] }) => (
    <>
        {issues.map((issue, index) => {
            const guidance = WARNING_GUIDANCE[issue.code];
            return (
                <div key={`${issue.code}-${index}`} className="hfcache-issue">
                    <Label isCompact>{issue.code}</Label>
                    {' '}
                    {issue.repository !== null && <strong>{issue.repository}:&nbsp;</strong>}
                    {issue.message}
                    {guidance !== undefined &&
                        <div className="hfcache-issue-guidance">{guidance.response}</div>}
                </div>
            );
        })}
    </>
);

/* One envelope, one alert. Success renders nothing; the busy state names
 * the single-writer lock as normal operation (CP-10). */
export const EnvelopeAlert = ({ envelope }: { envelope: Envelope }) => {
    const kind = classifyEnvelope(envelope);
    if (kind === 'success')
        return null;
    const guidance = EXIT_CODE_GUIDANCE[envelope.exit_code];
    const busy = kind === 'busy';
    const observation = kind === 'observation';
    const title = busy
        ? 'Another mutating command holds the archive lock (AD-17) — normal; exactly one runs at a time'
        : observation
            ? `${envelope.command}: execution outcome is not confirmed`
            : `${envelope.command}: ${guidance?.title ?? `exit ${envelope.exit_code}`}`;
    return (
        <Alert variant={ALERT_VARIANT[kind]} isInline title={title}>
            {observation &&
                <p>Accepted server work may continue. Preserve the original handles and observe
                    that operation before considering another submission.
                </p>}
            {!busy && !observation && guidance !== undefined && <p>{guidance.guidance}</p>}
            <IssueRows issues={[...envelope.errors, ...envelope.warnings]} />
            <RecoveryHandles evidence={operationEvidence(envelope)} />
        </Alert>
    );
};

/* A lost/malformed response cannot establish whether accepted work stopped. */
export const QueryError = ({ error }: { error: Error }) => {
    if (error instanceof OperationRegistryError)
        return <Alert variant="warning" isInline title="Original operation recovery requires attention">{error.message}</Alert>;
    if (error instanceof OperationAuthorityError) {
        return (
            <>
                {error.envelope && <EnvelopeAlert envelope={error.envelope} />}
                <Alert variant="warning" isInline title={error.message} />
            </>
        );
    }
    const failure = normalizeFailure(error);
    const evidence = readOperationEvidence({
        idempotency_key: failure.idempotencyKey,
        operation_id: failure.operationId,
        work_may_continue: failure.workMayContinue
    });
    const category = {
        access: 'Administrative access is required',
        bridge: 'Host connection interrupted',
        launcher: 'Client launcher could not start',
        process: 'Host process failed',
        protocol: 'Client output could not be validated',
        observation: 'Operation observation interrupted',
    }[failure.category];
    return (
        <>
            {error instanceof HfcacheSpawnError && error.envelope && <EnvelopeAlert envelope={error.envelope} />}
            <Alert variant="danger" isInline title={`${failure.stage}: ${category}`}>
                <p>{failure.message}</p>
                {failure.problem !== undefined && <p>Host problem: <code>{failure.problem}</code></p>}
                {failure.exitStatus !== undefined && <p>Process exit status: {failure.exitStatus}</p>}
                {failure.exitSignal !== undefined && <p>Process exit signal: {failure.exitSignal}</p>}
                {failure.hostMutationUncertain &&
                <p>The host change may have completed. Preserve its evidence and reconcile the
                    fixed configuration or unit state before another deliberate change.
                </p>}
                {failure.workMayContinue &&
                <p>Server execution is uncertain. Preserve the original handles and use authenticated
                    lookup and observation before submitting again.
                </p>}
                <RecoveryHandles evidence={evidence} />
            </Alert>
        </>
    );
};

export const RecoveryHandles = ({ evidence, expectedClientScope }: { evidence: OperationEvidence; expectedClientScope?: string | undefined }) => (
    <>
        {evidence.idempotencyKey !== undefined &&
            <p>Original key: <code>{evidence.idempotencyKey}</code><br />
                <code>{operationCommands(evidence, expectedClientScope).lookup}</code>
            </p>}
        {evidence.operationId !== undefined &&
            <p>Operation: <code>{evidence.operationId}</code><br />
                <code>{operationCommands(evidence, expectedClientScope).wait}</code>
            </p>}
    </>
);

export const Loading = () => <Spinner size="lg" aria-label="Loading" />;

const VERIFICATION_COLORS: Record<string, 'green' | 'grey' | 'red'> = {
    verified: 'green',
    unverified: 'grey',
};

export const VerificationLabel = ({ state }: { state: string }) => (
    <Label isCompact color={VERIFICATION_COLORS[state] ?? 'red'}>{state}</Label>
);

export const EnabledLabel = ({ enabled }: { enabled: boolean }) => (
    <Label isCompact color={enabled ? 'green' : 'grey'}>{enabled ? 'enabled' : 'disabled'}</Label>
);

export const UnmanagedLabel = () => (
    <Label isCompact color="yellow">unmanaged</Label>
);

/* Display truncation beside the full value (docs/cockpit.md: anything that
 * goes back into a command uses the full SHA). */
export const Sha = ({ sha, short }: { sha: string | null; short: string }) => (
    <code title={sha ?? undefined}>{short}</code>
);

/* A command payload's scalar fields, for envelopes whose data the UI has no
 * richer rendering for; arrays summarize to their length. */
export const DataSummary = ({ data }: { data: unknown }) => {
    if (typeof data !== 'object' || data === null)
        return null;
    const entries = Object.entries(data as Record<string, unknown>);
    if (entries.length === 0)
        return null;
    return (
        <DescriptionList isHorizontal isCompact>
            {entries.map(([key, value]) => {
                let shown: string;
                if (value === null)
                    shown = 'null';
                else if (Array.isArray(value))
                    shown = `${value.length} entries`;
                else if (typeof value === 'object')
                    shown = '…';
                else
                    shown = String(value);
                return (
                    <DescriptionListGroup key={key}>
                        <DescriptionListTerm>{key}</DescriptionListTerm>
                        <DescriptionListDescription>{shown}</DescriptionListDescription>
                    </DescriptionListGroup>
                );
            })}
        </DescriptionList>
    );
};
