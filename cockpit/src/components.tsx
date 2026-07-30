/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Shared presentational pieces: envelopes render the same way on every
 * surface (docs/cockpit.md §4).
 */

import React from 'react';

import { Alert } from "@patternfly/react-core/dist/esm/components/Alert/index.js";
import { Label } from "@patternfly/react-core/dist/esm/components/Label/index.js";
import { Spinner } from "@patternfly/react-core/dist/esm/components/Spinner/index.js";

import { classifyEnvelope, Envelope, EnvelopeIssue, EXIT_CODE_GUIDANCE, ResultKind } from './lib/envelope';
import { WARNING_GUIDANCE } from './lib/warnings';

type AlertVariant = 'success' | 'info' | 'warning' | 'danger';

export const ALERT_VARIANT: Record<ResultKind, AlertVariant> = {
    success: 'success',
    warnings: 'warning',
    invalid: 'warning',
    busy: 'info',
    refused: 'danger',
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
    const title = busy
        ? 'Another mutating command holds the archive lock (AD-17) — normal; exactly one runs at a time'
        : `${envelope.command}: ${guidance?.title ?? `exit ${envelope.exit_code}`}`;
    return (
        <Alert variant={ALERT_VARIANT[kind]} isInline title={title}>
            {!busy && guidance !== undefined && <p>{guidance.guidance}</p>}
            <IssueRows issues={[...envelope.errors, ...envelope.warnings]} />
        </Alert>
    );
};

/* A spawn- or envelope-level failure: hfcache itself never got to answer. */
export const QueryError = ({ error }: { error: Error }) => (
    <Alert variant="danger" isInline title="hfcache could not be invoked">
        {error.message}
    </Alert>
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
