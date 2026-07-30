/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The run report browser (docs/cockpit.md §3): the durable record under
 * `runs/` is the authority for what a run did; the journal says what
 * happened, and run_id joins them (docs/operations.md §4).
 */

import React, { useCallback, useEffect, useState } from 'react';

import { Button } from "@patternfly/react-core/dist/esm/components/Button/index.js";
import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import {
    DescriptionList, DescriptionListDescription, DescriptionListGroup, DescriptionListTerm,
} from "@patternfly/react-core/dist/esm/components/DescriptionList/index.js";
import {
    ExpandableSection,
} from "@patternfly/react-core/dist/esm/components/ExpandableSection/index.js";
import { Stack, StackItem } from "@patternfly/react-core/dist/esm/layouts/Stack/index.js";
import { ListingTable } from 'cockpit-components-table';

import { journalForRun, listRunReports, readRunReport } from './api/archive';
import { Loading, QueryError } from './components';
import { formatBytes, formatTimestamp } from './lib/format';
import { parseReportName } from './lib/reports';

const REPORT_LIMIT = 50;

interface ReportRepository {
    repository_id?: string;
    repository_type?: string;
    status?: string;
    resolved_commit_sha?: string;
    downloaded_bytes?: number;
    reused_bytes?: number;
    hashed_bytes?: number;
    publication_generation?: number;
}

interface RunReport {
    command?: string;
    outcome?: string;
    exit_code?: number;
    invocation_mode?: string;
    run_id?: string;
    repositories?: ReportRepository[];
    totals?: Record<string, number>;
    findings?: unknown[];
}

const Item = ({ term, children }: { term: string; children: React.ReactNode }) => (
    <DescriptionListGroup>
        <DescriptionListTerm>{term}</DescriptionListTerm>
        <DescriptionListDescription>{children}</DescriptionListDescription>
    </DescriptionListGroup>
);

const JournalTrail = ({ runId }: { runId: string }) => {
    const [lines, setLines] = useState<string[] | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const [loading, setLoading] = useState(false);

    const load = () => {
        setLoading(true);
        journalForRun(runId)
                .then(result => setLines(result), failure => setError(failure as Error))
                .finally(() => setLoading(false));
    };

    return (
        <Stack hasGutter>
            <StackItem>
                <Button variant="secondary" onClick={load} isDisabled={loading} isInline>
                    Show journal trail for this run
                </Button>
            </StackItem>
            {loading && <StackItem><Loading /></StackItem>}
            {error !== null && <StackItem><QueryError error={error} /></StackItem>}
            {lines !== null && !loading &&
                <StackItem>
                    <pre className="hfcache-journal">
                        {lines.length === 0 ? 'No journal lines for this run id.' : lines.join('\n')}
                    </pre>
                </StackItem>}
        </Stack>
    );
};

const ReportView = ({ file, report }: { file: string; report: RunReport }) => {
    const repositories = report.repositories ?? [];
    const totals = report.totals ?? {};
    return (
        <Card>
            <CardTitle>{file}</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>
                        <DescriptionList isHorizontal isCompact>
                            <Item term="Command">{report.command ?? '—'}</Item>
                            <Item term="Outcome">{report.outcome ?? '—'}</Item>
                            <Item term="Exit code">{report.exit_code ?? '—'}</Item>
                            <Item term="Invocation">{report.invocation_mode ?? '—'}</Item>
                            <Item term="Run id"><code>{report.run_id ?? '—'}</code></Item>
                        </DescriptionList>
                    </StackItem>
                    {repositories.length > 0 &&
                        <StackItem>
                            <ListingTable
                                aria-label="Per-repository outcomes"
                                variant="compact"
                                columns={['Repository', 'Status', 'Downloaded', 'Reused', 'Hashed', 'Generation']}
                                emptyCaption="No repositories in this run"
                                rows={repositories.map((repository, index) => ({
                                    props: { key: repository.repository_id ?? String(index) },
                                    columns: [
                                        repository.repository_id ?? '—',
                                        repository.status ?? '—',
                                        formatBytes(repository.downloaded_bytes),
                                        formatBytes(repository.reused_bytes),
                                        formatBytes(repository.hashed_bytes),
                                        repository.publication_generation ?? '—',
                                    ],
                                }))}
                            />
                        </StackItem>}
                    {Object.keys(totals).length > 0 &&
                        <StackItem>
                            <DescriptionList isHorizontal isCompact>
                                {Object.entries(totals).map(([key, value]) => (
                                    <Item term={key} key={key}>
                                        {key.endsWith('_bytes') ? formatBytes(value) : String(value)}
                                    </Item>
                                ))}
                            </DescriptionList>
                        </StackItem>}
                    <StackItem>
                        <ExpandableSection toggleText="Raw report JSON">
                            <pre className="hfcache-journal">{JSON.stringify(report, null, 2)}</pre>
                        </ExpandableSection>
                    </StackItem>
                    {report.run_id !== undefined &&
                        <StackItem><JournalTrail runId={report.run_id} /></StackItem>}
                </Stack>
            </CardBody>
        </Card>
    );
};

export const RunReports = () => {
    const [names, setNames] = useState<string[] | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const [selected, setSelected] = useState<string | null>(null);
    const [report, setReport] = useState<RunReport | null>(null);
    const [reportError, setReportError] = useState<Error | null>(null);

    const load = useCallback(() => {
        setError(null);
        listRunReports()
                .then(result => setNames(result), failure => setError(failure as Error));
    }, []);

    useEffect(load, [load]);

    const open = (file: string) => {
        setSelected(file);
        setReport(null);
        setReportError(null);
        readRunReport(file)
                .then(result => setReport(result as RunReport),
                      failure => setReportError(failure as Error));
    };

    return (
        <Stack hasGutter>
            {error !== null && <StackItem><QueryError error={error} /></StackItem>}
            {names === null && error === null && <StackItem><Loading /></StackItem>}
            {names !== null &&
                <StackItem>
                    <Card>
                        <CardTitle>
                            Run reports ({Math.min(names.length, REPORT_LIMIT)} of {names.length})
                        </CardTitle>
                        <CardBody>
                            <ListingTable
                                aria-label="Durable run reports"
                                variant="compact"
                                columns={['Started', 'Run id', 'Report']}
                                emptyCaption="No run reports. A run that died in preflight leaves only the journal."
                                onRowClick={(_event, row) => open(String(row.props?.key ?? ''))}
                                rows={names.slice(0, REPORT_LIMIT).map(file => {
                                    const parsed = parseReportName(file);
                                    return {
                                        props: { key: file },
                                        columns: [
                                            formatTimestamp(parsed.startedAt?.toISOString()),
                                            { title: <code>{parsed.runId ?? '—'}</code> },
                                            file,
                                        ],
                                    };
                                })}
                            />
                        </CardBody>
                    </Card>
                </StackItem>}
            {selected !== null && reportError !== null &&
                <StackItem><QueryError error={reportError} /></StackItem>}
            {selected !== null && report !== null &&
                <StackItem><ReportView file={selected} report={report} /></StackItem>}
        </Stack>
    );
};
