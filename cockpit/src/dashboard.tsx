/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The Overview surface (docs/cockpit.md §3): archive health from
 * `status --json` (the six ops §1 fields plus capacity), findings, the
 * per-repository state table, doctor on demand, and version.
 */

import React, { useEffect, useRef, useState } from 'react';

import { Button } from "@patternfly/react-core/dist/esm/components/Button/index.js";
import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import {
    DescriptionList, DescriptionListDescription, DescriptionListGroup, DescriptionListTerm,
} from "@patternfly/react-core/dist/esm/components/DescriptionList/index.js";
import { Label } from "@patternfly/react-core/dist/esm/components/Label/index.js";
import { Flex, FlexItem } from "@patternfly/react-core/dist/esm/layouts/Flex/index.js";
import { Stack, StackItem } from "@patternfly/react-core/dist/esm/layouts/Stack/index.js";
import { ListingTable } from 'cockpit-components-table';

import { runHfcache } from './api/hfcache';
import { connectionSnapshot, synchronizeConnection } from './api/connection';
import { currentOperationHost, submissionBlocked } from './api/operations';
import {
    EnabledLabel, EnvelopeAlert, IssueRows, Loading, QueryError, Sha, UnmanagedLabel, VerificationLabel,
} from './components';
import { useHfcache, useConnection, useOperations, useHostProfile } from './hooks';
import { hostActionAllowed } from './api/profile';
import { Envelope } from './lib/envelope';
import { formatBytes, formatHours, formatTimestamp, shortSha } from './lib/format';
import { parseDoctor, parseStatus, parseVersion } from './lib/read-results';
import type { StatusArchive, StatusFinding, StatusRepository } from './lib/read-results';

const Item = ({ term, children }: { term: string; children: React.ReactNode }) => (
    <DescriptionListGroup>
        <DescriptionListTerm>{term}</DescriptionListTerm>
        <DescriptionListDescription>{children}</DescriptionListDescription>
    </DescriptionListGroup>
);

const OkLabel = ({ ok, children }: { ok: boolean; children: React.ReactNode }) => (
    <Label isCompact color={ok ? 'green' : 'orange'}>{children}</Label>
);

const ArchiveHealthCard = ({ archive }: { archive: StatusArchive }) => {
    const verification = archive.verification;
    const last = verification.last_full_verification;
    const health = archive.reachable ? archive : null;
    const spaceOk = health !== null && health.available_bytes > health.reserve_bytes;
    return (
        <Card>
            <CardTitle>Archive health</CardTitle>
            <CardBody>
                <DescriptionList isHorizontal isCompact>
                    <Item term="Reachable">
                        <OkLabel ok={archive.reachable}>{archive.reachable ? 'yes' : 'unavailable'}</OkLabel>
                    </Item>
                    {health === null && <Item term="Health measurements">Unavailable; capacity and cleanup counters were not returned.</Item>}
                    {health !== null &&
                    <>
                        <Item term="Free space">
                            <OkLabel ok={spaceOk}>{formatBytes(health.available_bytes)} available</OkLabel>
                            {' '}reserve {formatBytes(health.reserve_bytes)}, headroom {formatBytes(health.headroom_bytes)}
                        </Item>
                        <Item term="Unfinished transactions">
                            <OkLabel ok={health.unfinished_transactions === 0}>
                                {health.unfinished_transactions}
                            </OkLabel>
                            {health.unfinished_transactions > 0 &&
                            <> — recover --dry-run describes them (Maintenance)</>}
                        </Item>
                    </>}
                    <Item term="Verification">
                        <OkLabel ok={!verification.degraded && last !== null}>
                            {verification.degraded
                                ? `degraded — ${verification.outstanding_failures} outstanding`
                                : (last === null ? 'not yet fully verified' : 'not degraded')}
                        </OkLabel>
                    </Item>
                    <Item term="Last full verification">
                        {last === null
                            ? 'never'
                            : `${last.outcome ?? '?'} · ${formatTimestamp(last.completed_at)}`}
                    </Item>
                    {health !== null &&
                    <>
                        <Item term="Deferred cleanup">
                            <OkLabel ok={health.deferred_cleanup === 0}>{health.deferred_cleanup}</OkLabel>
                        </Item>
                        <Item term="Unknown entries">
                            <OkLabel ok={health.unknown_entries.length === 0}>
                                {health.unknown_entries.length}
                            </OkLabel>
                            {health.unknown_entries.length > 0 && <> — preserved, never deleted (FS-19)</>}
                        </Item>
                    </>}
                    <Item term="Identity">
                        <code>{archive.archive_id}</code> at <code>{archive.root}</code>
                    </Item>
                </DescriptionList>
            </CardBody>
        </Card>
    );
};

const FindingsCard = ({ findings }: { findings: readonly StatusFinding[] }) => (
    <Card>
        <CardTitle>Findings</CardTitle>
        <CardBody>
            <ListingTable
                aria-label="Archive findings"
                variant="compact"
                columns={['Area', 'Path', 'Age', 'State']}
                emptyCaption="No findings"
                rows={findings.map(finding => ({
                    props: { key: finding.path },
                    columns: [
                        finding.area,
                        { title: <code>{finding.path}</code> },
                        formatHours(finding.age_hours),
                        {
                            title: finding.stale
                                ? <Label isCompact color="orange">stale</Label>
                                : <Label isCompact color="grey">recent</Label>,
                        },
                    ],
                }))}
            />
        </CardBody>
    </Card>
);

const RepositoriesCard = ({ repositories }: { repositories: readonly StatusRepository[] }) => (
    <Card>
        <CardTitle>Repositories</CardTitle>
        <CardBody>
            <ListingTable
                aria-label="Configured and archived repositories"
                variant="compact"
                columns={['Repository', 'Type', 'State', 'Current', 'Retained', 'Last run', 'Verification']}
                emptyCaption="Nothing configured and nothing archived"
                rows={repositories.map(repository => ({
                    props: { key: `${repository.repository_type}:${repository.repository_id}` },
                    columns: [
                        repository.repository_id,
                        repository.repository_type,
                        {
                            title: (
                                repository.managed && repository.enabled !== null
                                    ? <EnabledLabel enabled={repository.enabled} />
                                    : <UnmanagedLabel />
                            ),
                        },
                        { title: <Sha sha={repository.current_commit_sha} short={shortSha(repository.current_commit_sha)} /> },
                        repository.retained_revisions,
                        repository.last_run_status ?? '—',
                        { title: <VerificationLabel state={repository.verification_state} /> },
                    ],
                }))}
            />
        </CardBody>
    </Card>
);

const DOCTOR_COLORS: Record<string, 'green' | 'red' | 'grey'> = {
    pass: 'green',
    fail: 'red',
    skipped: 'grey',
};

const DoctorCard = () => {
    const connection = useConnection();
    const operations = useOperations();
    const profile = useHostProfile();
    const [running, setRunning] = useState(false);
    const [result, setResult] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const [observedOrigin, setObservedOrigin] = useState('');
    const submitted = useRef(false);
    const mounted = useRef(true);
    const host = currentOperationHost();
    const origin = JSON.stringify([connection.generation, connection.administrative, host]);
    const latestOrigin = useRef(origin);
    latestOrigin.current = origin;
    useEffect(() => {
        mounted.current = true;
        return () => { mounted.current = false };
    }, []);
    useEffect(() => { setResult(null); setError(null) }, [origin]);

    const run = (readOnly: boolean) => {
        if (synchronizeConnection() !== connection || host !== currentOperationHost()) return;
        if (submitted.current || running || submissionBlocked() || !connectionSnapshot().administrative ||
            !hostActionAllowed('hub') || (!readOnly && !hostActionAllowed('archive')))
            return;
        submitted.current = true;
        setRunning(true);
        setResult(null);
        setError(null);
        const observedOrigin = origin;
        const current = () => mounted.current && latestOrigin.current === observedOrigin &&
            connectionSnapshot().generation === connection.generation && connectionSnapshot().administrative && currentOperationHost() === host;
        const command = readOnly ? ['doctor', '--read-only'] : ['doctor'];
        runHfcache(command)
                .then(envelope => { if (current()) { setObservedOrigin(observedOrigin); setResult(envelope) } },
                      failure => { if (current()) { setObservedOrigin(observedOrigin); setError(failure as Error) } })
                .finally(() => { submitted.current = false; if (mounted.current) setRunning(false); });
    };

    const fresh = observedOrigin === origin;
    const parsed = result === null || !fresh ? null : parseDoctor(result);
    const checks = parsed?.payload?.checks;

    return (
        <Card>
            <CardTitle>Doctor</CardTitle>
            <CardBody>
                <Flex>
                    <FlexItem>
                        <Button variant="secondary" isDisabled={running || operations.blocked || !connection.administrative || !profile.permissions.hub} onClick={() => run(true)}>
                            Run checks (read-only)
                        </Button>
                    </FlexItem>
                    <FlexItem>
                        <Button variant="secondary" isDisabled={running || operations.blocked || !connection.administrative || !profile.permissions.hub || !profile.permissions.archive} onClick={() => run(false)}>
                            Run full checks (write probes)
                        </Button>
                    </FlexItem>
                    {running && <FlexItem><Loading /></FlexItem>}
                </Flex>
                {(!profile.permissions.hub || !profile.permissions.archive) && <p>{profile.reason}</p>}
                <p>Both checks contact the Hub and write a control receipt. Full checks also perform archive write probes.</p>
                {error !== null && fresh && <QueryError error={error} />}
                {result !== null && fresh && !running &&
                    <Stack hasGutter>
                        <StackItem><EnvelopeAlert envelope={result} /></StackItem>
                        {parsed?.error && <StackItem><QueryError error={parsed.error} /></StackItem>}
                        {parsed?.partial && checks && <StackItem>Partial diagnostics; the command failed. These checks are informational.</StackItem>}
                        {checks &&
                        <StackItem>
                            <ListingTable
                                aria-label="Doctor checks"
                                variant="compact"
                                columns={['Check', 'Outcome', 'Detail']}
                                emptyCaption="No checks ran"
                                rows={checks.map(check => ({
                                    props: { key: check.name },
                                    columns: [
                                        <code key="name">{check.name}</code>,
                                        {
                                            title: (
                                                <Label isCompact color={DOCTOR_COLORS[check.outcome] ?? 'orange'}>
                                                    {check.outcome}
                                                </Label>
                                            ),
                                        },
                                        check.detail,
                                    ],
                                }))}
                            />
                        </StackItem>}
                    </Stack>}
            </CardBody>
        </Card>
    );
};

const VersionCard = () => {
    const version = useHfcache(['version', '--server']);
    const parsed = version.envelope === null ? null : parseVersion(version.envelope);
    const data = parsed?.payload;
    return (
        <Card>
            <CardTitle>Version</CardTitle>
            <CardBody>
                {version.loading && <Loading />}
                {version.error !== null && <QueryError error={version.error} />}
                {version.envelope !== null && <EnvelopeAlert envelope={version.envelope} />}
                {parsed?.error && <QueryError error={parsed.error} />}
                {parsed?.partial && data && <p>Partial server version information; the command failed.</p>}
                {data &&
                <DescriptionList isHorizontal isCompact>
                    {data.application !== undefined && <Item term="hfcache">{data.application}</Item>}
                    {data.python !== undefined && <Item term="Python">{data.python}</Item>}
                    {data.huggingface_hub !== undefined && <Item term="huggingface_hub">{data.huggingface_hub}</Item>}
                    {data.transfer_backend !== undefined && <Item term="Transfer backend">{data.transfer_backend}</Item>}
                </DescriptionList>}
            </CardBody>
        </Card>
    );
};

export const Dashboard = () => {
    const status = useHfcache(['status']);
    const parsed = status.envelope === null ? null : parseStatus(status.envelope);
    const data = parsed?.payload;

    return (
        <Stack hasGutter>
            <StackItem>
                <Flex>
                    <FlexItem align={{ default: 'alignRight' }}>
                        <Button variant="secondary" onClick={() => status.refresh()} isDisabled={status.loading}>
                            Refresh
                        </Button>
                    </FlexItem>
                </Flex>
            </StackItem>
            {status.loading && <StackItem><Loading /></StackItem>}
            {status.error !== null && <StackItem><QueryError error={status.error} /></StackItem>}
            {status.envelope !== null && !status.loading &&
                <>
                    <StackItem><EnvelopeAlert envelope={status.envelope} /></StackItem>
                    {status.envelope.warnings.length > 0 &&
                        <StackItem>
                            <Card>
                                <CardTitle>Warnings</CardTitle>
                                <CardBody><IssueRows issues={status.envelope.warnings} /></CardBody>
                            </Card>
                        </StackItem>}
                    {parsed?.error && <StackItem><QueryError error={parsed.error} /></StackItem>}
                    {parsed?.partial && data && <StackItem>Partial archive status; the command failed. These observations are informational.</StackItem>}
                    {data?.archive !== undefined &&
                        <StackItem><ArchiveHealthCard archive={data.archive} /></StackItem>}
                    {data?.archive?.reachable === true && data.archive.findings.length > 0 &&
                        <StackItem><FindingsCard findings={data.archive.findings} /></StackItem>}
                    {data?.repositories !== undefined &&
                        <StackItem><RepositoriesCard repositories={data.repositories} /></StackItem>}
                </>}
            <StackItem><DoctorCard /></StackItem>
            <StackItem><VersionCard /></StackItem>
        </Stack>
    );
};
