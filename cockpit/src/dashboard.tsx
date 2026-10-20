/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The Overview surface (docs/cockpit.md §3): archive health from
 * `status --json` (the six ops §1 fields plus capacity), findings, the
 * per-repository state table, doctor on demand, and version.
 */

import React, { useRef, useState } from 'react';

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
import { connectionSnapshot } from './api/connection';
import { submissionBlocked } from './api/operations';
import {
    EnabledLabel, EnvelopeAlert, IssueRows, Loading, QueryError, Sha, UnmanagedLabel, VerificationLabel,
} from './components';
import { useHfcache, useConnection, useOperations } from './hooks';
import { Envelope } from './lib/envelope';
import { formatBytes, formatHours, formatTimestamp, shortSha } from './lib/format';

/* The status payload (docs/cli.md §4.1), fields as deployed at 0.1.3. */
interface StatusVerification {
    degraded: boolean;
    outstanding_failures: number;
    last_full_verification: {
        completed_at?: string;
        outcome?: string;
        unique_objects?: number;
        unique_bytes?: number;
    } | null;
}

interface StatusFinding {
    area: string;
    path: string;
    age_hours: number;
    stale: boolean;
    transaction_id: string;
}

interface StatusArchive {
    archive_id: string;
    root?: string;
    reachable: boolean;
    available_bytes: number;
    reserve_bytes: number;
    headroom_bytes?: number;
    total_bytes?: number;
    unfinished_transactions: number;
    deferred_cleanup: number;
    findings: StatusFinding[];
    unknown_entries: string[];
    verification: StatusVerification;
}

interface StatusRepository {
    repository_id: string;
    repository_type: string;
    enabled: boolean;
    managed: boolean;
    requested_revision?: string;
    current_commit_sha: string | null;
    retained_revisions: number;
    last_run_status: string | null;
    verification_state: string;
}

interface StatusData {
    archive?: StatusArchive;
    repositories?: StatusRepository[];
}

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
    const spaceOk = archive.available_bytes > archive.reserve_bytes;
    return (
        <Card>
            <CardTitle>Archive health</CardTitle>
            <CardBody>
                <DescriptionList isHorizontal isCompact>
                    <Item term="Reachable">
                        <OkLabel ok={archive.reachable}>{archive.reachable ? 'yes' : 'no — mount gone'}</OkLabel>
                    </Item>
                    <Item term="Free space">
                        <OkLabel ok={spaceOk}>{formatBytes(archive.available_bytes)} available</OkLabel>
                        {' '}reserve {formatBytes(archive.reserve_bytes)}, headroom {formatBytes(archive.headroom_bytes)}
                    </Item>
                    <Item term="Unfinished transactions">
                        <OkLabel ok={archive.unfinished_transactions === 0}>
                            {archive.unfinished_transactions}
                        </OkLabel>
                        {archive.unfinished_transactions > 0 &&
                            <> — recover --dry-run describes them (Maintenance)</>}
                    </Item>
                    <Item term="Verification">
                        <OkLabel ok={!verification.degraded}>
                            {verification.degraded
                                ? `degraded — ${verification.outstanding_failures} outstanding`
                                : 'not degraded'}
                        </OkLabel>
                    </Item>
                    <Item term="Last full verification">
                        {last === null
                            ? 'never'
                            : `${last.outcome ?? '?'} · ${formatTimestamp(last.completed_at)}`}
                    </Item>
                    <Item term="Deferred cleanup">
                        <OkLabel ok={archive.deferred_cleanup === 0}>{archive.deferred_cleanup}</OkLabel>
                    </Item>
                    <Item term="Unknown entries">
                        <OkLabel ok={archive.unknown_entries.length === 0}>
                            {archive.unknown_entries.length}
                        </OkLabel>
                        {archive.unknown_entries.length > 0 && <> — preserved, never deleted (FS-19)</>}
                    </Item>
                    <Item term="Identity">
                        <code>{archive.archive_id}</code> at <code>{archive.root ?? '/srv/hfcache'}</code>
                    </Item>
                </DescriptionList>
            </CardBody>
        </Card>
    );
};

const FindingsCard = ({ findings }: { findings: StatusFinding[] }) => (
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

const RepositoriesCard = ({ repositories }: { repositories: StatusRepository[] }) => (
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
                                <>
                                    <EnabledLabel enabled={repository.enabled} />
                                    {!repository.managed && <>{' '}<UnmanagedLabel /></>}
                                </>
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

interface DoctorCheck {
    name: string;
    outcome: string;
    detail?: unknown;
}

const DOCTOR_COLORS: Record<string, 'green' | 'red' | 'grey'> = {
    pass: 'green',
    fail: 'red',
    skipped: 'grey',
};

const DoctorCard = () => {
    const connection = useConnection();
    const operations = useOperations();
    const [running, setRunning] = useState(false);
    const [result, setResult] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const submitted = useRef(false);

    const run = (readOnly: boolean) => {
        if (submitted.current || running || submissionBlocked() || !connectionSnapshot().administrative)
            return;
        submitted.current = true;
        setRunning(true);
        setError(null);
        const command = readOnly ? ['doctor', '--read-only'] : ['doctor'];
        runHfcache(command)
                .then(envelope => setResult(envelope), failure => setError(failure as Error))
                .finally(() => { submitted.current = false; setRunning(false) });
    };

    const checks = ((result?.data as { checks?: DoctorCheck[] } | undefined)?.checks) ?? [];

    return (
        <Card>
            <CardTitle>Doctor</CardTitle>
            <CardBody>
                <Flex>
                    <FlexItem>
                        <Button variant="secondary" isDisabled={running || operations.blocked || !connection.administrative} onClick={() => run(true)}>
                            Run checks (read-only)
                        </Button>
                    </FlexItem>
                    <FlexItem>
                        <Button variant="secondary" isDisabled={running || operations.blocked || !connection.administrative} onClick={() => run(false)}>
                            Run full checks (write probes)
                        </Button>
                    </FlexItem>
                    {running && <FlexItem><Loading /></FlexItem>}
                </Flex>
                {error !== null && <QueryError error={error} />}
                {result !== null && !running &&
                    <Stack hasGutter>
                        <StackItem><EnvelopeAlert envelope={result} /></StackItem>
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
                                        typeof check.detail === 'string'
                                            ? check.detail
                                            : JSON.stringify(check.detail ?? ''),
                                    ],
                                }))}
                            />
                        </StackItem>
                    </Stack>}
            </CardBody>
        </Card>
    );
};

interface VersionData {
    application?: string;
    python?: string;
    huggingface_hub?: string;
    transfer_backend?: string;
}

const VersionCard = () => {
    const version = useHfcache(['version', '--server']);
    const data = (version.envelope?.data ?? {}) as VersionData;
    return (
        <Card>
            <CardTitle>Version</CardTitle>
            <CardBody>
                {version.loading && <Loading />}
                {version.error !== null && <QueryError error={version.error} />}
                {version.envelope !== null &&
                    <DescriptionList isHorizontal isCompact>
                        <Item term="hfcache">{data.application ?? '—'}</Item>
                        <Item term="Python">{data.python ?? '—'}</Item>
                        <Item term="huggingface_hub">{data.huggingface_hub ?? '—'}</Item>
                        <Item term="Transfer backend">{data.transfer_backend ?? '—'}</Item>
                    </DescriptionList>}
            </CardBody>
        </Card>
    );
};

export const Dashboard = () => {
    const status = useHfcache(['status']);
    const data = (status.envelope?.data ?? {}) as StatusData;

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
                    {status.envelope.warnings.length > 0 &&
                        <StackItem>
                            <Card>
                                <CardTitle>Warnings</CardTitle>
                                <CardBody><IssueRows issues={status.envelope.warnings} /></CardBody>
                            </Card>
                        </StackItem>}
                    <StackItem><EnvelopeAlert envelope={status.envelope} /></StackItem>
                    {data.archive !== undefined &&
                        <StackItem><ArchiveHealthCard archive={data.archive} /></StackItem>}
                    {data.archive !== undefined && data.archive.findings.length > 0 &&
                        <StackItem><FindingsCard findings={data.archive.findings} /></StackItem>}
                    {data.repositories !== undefined &&
                        <StackItem><RepositoriesCard repositories={data.repositories} /></StackItem>}
                </>}
            <StackItem><DoctorCard /></StackItem>
            <StackItem><VersionCard /></StackItem>
        </Stack>
    );
};
