/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The archive browser (docs/cockpit.md §3): `list --revisions --json` —
 * what is archived, which is not the same as what is configured (AD-06).
 * Works even when the catalog is missing or corrupt, because `list` reads
 * only manifests and references.
 */

import React from 'react';

import { Button } from "@patternfly/react-core/dist/esm/components/Button/index.js";
import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import { Flex, FlexItem } from "@patternfly/react-core/dist/esm/layouts/Flex/index.js";
import { Stack, StackItem } from "@patternfly/react-core/dist/esm/layouts/Stack/index.js";
import { ListingTable } from 'cockpit-components-table';

import {
    EnabledLabel, EnvelopeAlert, Loading, QueryError, Sha, UnmanagedLabel, VerificationLabel,
} from './components';
import { useHfcache } from './hooks';
import { formatBytes, formatTimestamp, shortSha } from './lib/format';

/* The list payload (docs/cli.md §4.1), fields as deployed at 0.1.3. */
export interface ListRevision {
    commit_sha: string;
    file_count: number;
    publication_generation: number;
    publication_id: string;
    published_at: string;
    total_bytes: number;
    verification_state: string;
}

export interface ListRepository {
    repository_id: string;
    repository_type: string;
    enabled: boolean;
    managed: boolean;
    current_commit_sha: string | null;
    current_publication_id?: string | null;
    retained_revisions: number;
    revisions?: ListRevision[];
}

interface ListData {
    repositories?: ListRepository[];
}

const RevisionsTable = ({ repository }: { repository: ListRepository }) => (
    <ListingTable
        aria-label={`Retained revisions of ${repository.repository_id}`}
        variant="compact"
        columns={['Generation', 'Commit', 'Files', 'Size', 'Published', 'Verification']}
        emptyCaption="No retained revisions"
        rows={(repository.revisions ?? []).map(revision => ({
            props: { key: revision.publication_id },
            columns: [
                {
                    title: (
                        <>
                            {revision.publication_generation}
                            {revision.commit_sha === repository.current_commit_sha &&
                                <>{' '}<strong>(current)</strong></>}
                        </>
                    ),
                },
                { title: <Sha sha={revision.commit_sha} short={shortSha(revision.commit_sha)} /> },
                revision.file_count,
                formatBytes(revision.total_bytes),
                formatTimestamp(revision.published_at),
                { title: <VerificationLabel state={revision.verification_state} /> },
            ],
        }))}
    />
);

function currentSize(repository: ListRepository): number | null {
    const current = (repository.revisions ?? [])
            .find(revision => revision.commit_sha === repository.current_commit_sha);
    return current === undefined ? null : current.total_bytes;
}

export const ArchiveBrowser = () => {
    const list = useHfcache(['list', '--revisions']);
    const data = (list.envelope?.data ?? {}) as ListData;
    const repositories = data.repositories ?? [];

    return (
        <Stack hasGutter>
            <StackItem>
                <Flex>
                    <FlexItem align={{ default: 'alignRight' }}>
                        <Button variant="secondary" onClick={() => list.refresh()} isDisabled={list.loading}>
                            Refresh
                        </Button>
                    </FlexItem>
                </Flex>
            </StackItem>
            {list.loading && <StackItem><Loading /></StackItem>}
            {list.error !== null && <StackItem><QueryError error={list.error} /></StackItem>}
            {list.envelope !== null && !list.loading &&
                <>
                    <StackItem><EnvelopeAlert envelope={list.envelope} /></StackItem>
                    <StackItem>
                        <Card>
                            <CardTitle>Archived repositories</CardTitle>
                            <CardBody>
                                <ListingTable
                                    aria-label="Archived repositories and revisions"
                                    columns={['Repository', 'Type', 'State', 'Current', 'Retained', 'Current size']}
                                    emptyCaption="Nothing archived yet"
                                    rows={repositories.map(repository => ({
                                        props: { key: `${repository.repository_type}:${repository.repository_id}` },
                                        expandedContent: <RevisionsTable repository={repository} />,
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
                                            formatBytes(currentSize(repository)),
                                        ],
                                    }))}
                                />
                            </CardBody>
                        </Card>
                    </StackItem>
                </>}
        </Stack>
    );
};
