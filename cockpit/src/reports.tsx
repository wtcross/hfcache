/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Authenticated historical run reports; host journals are optional diagnostics.
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';

import { Alert } from '@patternfly/react-core/dist/esm/components/Alert/index.js';
import { Button } from '@patternfly/react-core/dist/esm/components/Button/index.js';
import { Card, CardBody, CardTitle } from '@patternfly/react-core/dist/esm/components/Card/index.js';
import { DescriptionList, DescriptionListDescription, DescriptionListGroup, DescriptionListTerm } from '@patternfly/react-core/dist/esm/components/DescriptionList/index.js';
import { ExpandableSection } from '@patternfly/react-core/dist/esm/components/ExpandableSection/index.js';
import { Stack, StackItem } from '@patternfly/react-core/dist/esm/layouts/Stack/index.js';
import { ListingTable } from 'cockpit-components-table';

import { journalForRun } from './api/archive';
import { JournalReadError } from './lib/run-journal';
import type { RunJournal } from './api/archive';
import { listRunReports, readRunReport } from './api/reports';
import type { RunDetailResult, RunPageResult } from './api/reports';
import { connectionSnapshot, synchronizeConnection } from './api/connection';
import { currentOperationHost } from './api/operations';
import { EnvelopeAlert, Loading, QueryError } from './components';
import { useConnection } from './hooks';
import { formatBytes, formatTimestamp } from './lib/format';
import type { RunReadMetadata } from './lib/read-metadata';
import { REPORT_PAGE_LIMIT } from './lib/reports';
import type { RunReport } from './lib/reports';

const Item = ({ term, children }: { term: string; children: React.ReactNode }) => (
    <DescriptionListGroup><DescriptionListTerm>{term}</DescriptionListTerm><DescriptionListDescription>{children}</DescriptionListDescription></DescriptionListGroup>
);

const JournalTrail = ({ runId }: { runId: string }) => {
    const connection = useConnection();
    const host = currentOperationHost();
    const origin = JSON.stringify([runId, host, connection]);
    const [observedOrigin, setObservedOrigin] = useState('');
    const [result, setResult] = useState<RunJournal | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const [loading, setLoading] = useState(false);
    const [readyOrigin, setReadyOrigin] = useState('');
    const revision = useRef(0);
    useEffect(() => {
        revision.current += 1;
        setResult(null);
        setError(null);
        setLoading(false);
        setReadyOrigin(origin);
        return () => { revision.current += 1 };
    }, [origin]);
    const load = () => {
        if (synchronizeConnection() !== connection || host !== currentOperationHost()) return;
        const request = ++revision.current;
        const active = connectionSnapshot();
        const current = () => request === revision.current && active === connectionSnapshot() && host === currentOperationHost();
        setLoading(true);
        setResult(null);
        setError(null);
        journalForRun(runId).then(value => {
            if (current()) { setObservedOrigin(origin); setResult(value) }
        }, failure => {
            if (current()) {
                setObservedOrigin(origin);
                setError(failure as Error);
                if (failure instanceof JournalReadError) setResult(failure.partial);
            }
        })
                .finally(() => { if (current()) setLoading(false); });
    };
    const fresh = observedOrigin === origin;
    return (
        <Stack hasGutter>
            <StackItem>Optional host-local event trail: the latest seven days, newest first. It does not establish the recorded run outcome.</StackItem>
            <StackItem><Button variant="secondary" onClick={load} isDisabled={readyOrigin !== origin || loading || !connection.administrative}>Show host journal trail for this run</Button></StackItem>
            {loading && <StackItem><Loading /></StackItem>}
            {fresh && error !== null && <StackItem><QueryError error={error} /></StackItem>}
            {fresh && result?.truncated && <StackItem><Alert variant="warning" isInline title="Host journal diagnostic is incomplete">{result.truncationReasons.join(', ')}. The REST report remains independent.</Alert></StackItem>}
            {fresh && result !== null && !loading && <StackItem><pre className="hfcache-journal">{result.lines.length === 0 ? 'No matching projected host events in the bounded window.' : result.lines.join('\n')}</pre></StackItem>}
        </Stack>
    );
};

const ReportView = ({ report }: { report: Readonly<RunReport> }) => (
    <Card>
        <CardTitle>Recorded run {report.run_id}</CardTitle>
        <CardBody>
            <Stack hasGutter>
                {report.exit_code !== 0 && <StackItem><Alert variant="danger" isInline title={`Recorded run failed (exit ${report.exit_code})`}>{report.errors.join(', ')}</Alert></StackItem>}
                {report.warnings.length > 0 && <StackItem><Alert variant="warning" isInline title="Recorded run warnings">{report.warnings.join(', ')}</Alert></StackItem>}
                <StackItem>
                    <DescriptionList isHorizontal isCompact>
                        <Item term="Command">{report.command}</Item><Item term="Recorded outcome">{report.outcome}</Item>
                        <Item term="Recorded exit code">{report.exit_code}</Item><Item term="Invocation">{report.invocation_mode}</Item>
                        <Item term="Run id"><code>{report.run_id}</code></Item>
                        <Item term="Started">{formatTimestamp(report.started_at)}</Item><Item term="Completed">{formatTimestamp(report.completed_at)}</Item>
                        <Item term="Archive identity"><code>{report.archive_id}</code></Item>
                        <Item term="Historical policy fingerprint"><code>{report.config_fingerprint}</code></Item>
                    </DescriptionList>
                </StackItem>
                {report.repositories !== undefined && report.repositories.length > 0 &&
                <StackItem>
                    <ListingTable
                        aria-label="Per-repository outcomes" variant="compact"
                    columns={['Repository', 'Status', 'Downloaded', 'Reused', 'Hashed', 'Generation']} emptyCaption="No repositories in this run"
                    rows={report.repositories.map(repository => ({
                        props: { key: repository.repository_type + ':' + repository.repository_id },
                        columns: [repository.repository_id, repository.status, formatBytes(repository.downloaded_bytes),
                            formatBytes(repository.reused_bytes), formatBytes(repository.hashed_bytes), repository.publication_generation ?? '—'],
                    }))}
                    />
                </StackItem>}
                {report.totals !== undefined &&
                <StackItem>
                    <DescriptionList isHorizontal isCompact>
                        {Object.entries(report.totals).map(([key, value]) => <Item term={key} key={key}>{formatBytes(value)}</Item>)}
                    </DescriptionList>
                </StackItem>}
                <StackItem><ExpandableSection toggleText="Raw report JSON"><pre className="hfcache-journal">{JSON.stringify(report, null, 2)}</pre></ExpandableSection></StackItem>
                <StackItem><JournalTrail key={report.run_id} runId={report.run_id} /></StackItem>
            </Stack>
        </CardBody>
    </Card>
);

export const RunReports = () => {
    const connection = useConnection();
    const host = currentOperationHost();
    const origin = JSON.stringify([host, connection]);
    const [listOrigin, setListOrigin] = useState('');
    const [listing, setListing] = useState<RunPageResult | null>(null);
    const [listError, setListError] = useState<Error | null>(null);
    const [listLoading, setListLoading] = useState(false);
    const [cursor, setCursor] = useState<string | null>(null);
    const [selected, setSelected] = useState<string | null>(null);
    const [detailOrigin, setDetailOrigin] = useState('');
    const [detail, setDetail] = useState<RunDetailResult | null>(null);
    const [detailError, setDetailError] = useState<Error | null>(null);
    const [detailLoading, setDetailLoading] = useState(false);
    const listRevision = useRef(0);
    const detailRevision = useRef(0);
    const detailPending = useRef(false);
    const mountedView = useRef(true);
    useEffect(() => {
        mountedView.current = true;
        return () => { mountedView.current = false };
    }, []);
    const load = useCallback((next: string | null, expected?: Readonly<RunReadMetadata>) => {
        if (synchronizeConnection() !== connection || host !== currentOperationHost()) return;
        const request = ++listRevision.current;
        detailRevision.current += 1;
        const active = connectionSnapshot();
        const current = () => request === listRevision.current && active === connectionSnapshot() && host === currentOperationHost();
        setListing(null); setListError(null); setSelected(null); setDetail(null); setDetailError(null);
        setListLoading(true); setCursor(next);
        listRunReports(next, expected).then(value => {
            if (current()) { setListOrigin(origin); setListing(value) }
        }, failure => {
            if (current()) { setListOrigin(origin); setListError(failure as Error) }
        })
                .finally(() => { if (current()) setListLoading(false); });
    }, [origin, host, connection]);
    useEffect(() => {
        load(null);
        return () => { listRevision.current += 1; detailRevision.current += 1 };
    }, [load]);
    const fresh = listOrigin === origin;
    const page = fresh ? listing?.page ?? null : null;
    const open = (runId: string) => {
        if (synchronizeConnection() !== connection || host !== currentOperationHost()) return;
        if (detailPending.current || page === null || !page.runs.includes(runId) || listing?.metadata === null || !connection.administrative) return;
        detailPending.current = true;
        const request = ++detailRevision.current;
        const active = connectionSnapshot();
        const current = () => request === detailRevision.current && active === connectionSnapshot() && host === currentOperationHost();
        setSelected(runId); setDetail(null); setDetailError(null); setDetailLoading(true);
        readRunReport(runId, listing?.metadata?.archive_id).then(value => {
            if (current()) { setDetailOrigin(origin); setDetail(value) }
        }, failure => {
            if (current()) { setDetailOrigin(origin); setDetailError(failure as Error) }
        })
                .finally(() => {
                    detailPending.current = false;
                    if (mountedView.current) setDetailLoading(false);
                });
    };
    const shownDetail = detailOrigin === origin ? detail : null;
    return (
        <Stack hasGutter>
            <StackItem><Button variant="secondary" isDisabled={listLoading || !connection.administrative} onClick={() => load(null)}>Refresh run reports</Button></StackItem>
            {listLoading && <StackItem><Loading /></StackItem>}
            {fresh && listError !== null && <StackItem><QueryError error={listError} /></StackItem>}
            {fresh && listing !== null && (listing.envelope.exit_code !== 0 || listing.envelope.warnings.length > 0) && <StackItem><EnvelopeAlert envelope={listing.envelope} /></StackItem>}
            {page !== null &&
                <StackItem>
                    <Card>
                        <CardTitle>Run reports ({page.runs.length} on this page)</CardTitle>
                        <CardBody>
                            <Stack hasGutter>
                                <StackItem>One page contains at most {REPORT_PAGE_LIMIT} run IDs in server order. Select an ID to read its historical report.</StackItem>
                                <StackItem>
                                    <ListingTable
                            aria-label="Durable run reports" variant="compact" columns={['Run id']}
                        emptyCaption="No run reports on this page. A run that died in preflight may leave only host diagnostics."
                        rows={page.runs.map(runId => ({
                            props: { key: runId },
                            columns: [
                                { title: <Button variant="link" isInline isDisabled={detailLoading || !connection.administrative} onClick={() => open(runId)}>Open report {runId}</Button> },
                            ]
                        }))}
                                    />
                                </StackItem>
                                <StackItem>
                                    <Button
                            variant="secondary" isDisabled={page.nextCursor === null || listLoading || !connection.administrative}
                        onClick={() => { if (page.nextCursor !== null && listing?.metadata) load(page.nextCursor, listing.metadata); }}
                                    >Next report page
                                    </Button>{' '}
                                    <Button variant="link" isDisabled={cursor === null || listLoading || !connection.administrative} onClick={() => load(null)}>Return to first report page</Button>
                                </StackItem>
                            </Stack>
                        </CardBody>
                    </Card>
                </StackItem>}
            {detailLoading && <StackItem><Loading /><p>A report read is finishing. You can select another report when it completes.</p></StackItem>}
            {selected !== null && detailOrigin === origin && detailError !== null && <StackItem><QueryError error={detailError} /></StackItem>}
            {selected !== null && shownDetail !== null && (shownDetail.envelope.exit_code !== 0 || shownDetail.envelope.warnings.length > 0) && <StackItem><EnvelopeAlert envelope={shownDetail.envelope} /></StackItem>}
            {selected !== null && shownDetail?.report && <StackItem><ReportView key={selected} report={shownDetail.report} /></StackItem>}
        </Stack>
    );
};
