/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The archive browser (docs/cockpit.md §3): `list --revisions --json` —
 * what is archived, which is not the same as what is configured (AD-06).
 * Works even when the catalog is missing or corrupt, because `list` reads
 * only manifests and references.
 */

import React from 'react';

import { Alert } from "@patternfly/react-core/dist/esm/components/Alert/index.js";
import { Button } from "@patternfly/react-core/dist/esm/components/Button/index.js";
import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import { Flex, FlexItem } from "@patternfly/react-core/dist/esm/layouts/Flex/index.js";
import { Stack, StackItem } from "@patternfly/react-core/dist/esm/layouts/Stack/index.js";
import { ListingTable } from 'cockpit-components-table';

import {
    EnabledLabel, EnvelopeAlert, Loading, QueryError, Sha, UnmanagedLabel, VerificationLabel,
} from './components';
import { useConnection, useHfcache } from './hooks';
import { formatBytes, formatTimestamp, shortSha } from './lib/format';
import { parseInventory } from './lib/inventory-read';
import type { InventoryRepository } from './lib/inventory-read';
import { huggingFaceRepositoryUrl } from './lib/repository';

export type { InventoryRepository as ListRepository, InventoryRevision as ListRevision } from './lib/inventory-read';

const RevisionsTable = ({ repository }: { repository: InventoryRepository }) => (
    <ListingTable
        aria-label={`Retained revisions of ${repository.repository_id}`}
        variant="compact"
        columns={['Generation', 'Commit', 'Files', 'Size', 'Published', 'Verification']}
        emptyCaption="No retained revisions"
        rows={repository.revisions.map(revision => ({
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
                { title: <code>{revision.commit_sha}</code> },
                revision.file_count,
                formatBytes(revision.total_bytes),
                formatTimestamp(revision.published_at),
                { title: <VerificationLabel state={revision.verification_state} /> },
            ],
        }))}
    />
);

function currentSize(repository: InventoryRepository): number | null {
    const current = repository.revisions
            .find(revision => revision.commit_sha === repository.current_commit_sha);
    return current === undefined ? null : current.total_bytes;
}

export const ArchiveBrowser = () => {
    const list = useHfcache(['list', '--revisions']);
    const connection = useConnection();
    const parsed = list.envelope === null ? null : parseInventory(list.envelope);
    const repositories = parsed?.payload?.repositories;

    return (
        <Stack hasGutter>
            <StackItem>
                <Flex>
                    <FlexItem align={{ default: 'alignRight' }}>
                        <Button variant="secondary" onClick={() => list.refresh()} isDisabled={list.loading || !connection.administrative}>
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
                    {parsed?.error && <StackItem><QueryError error={parsed.error} /></StackItem>}
                    {parsed?.partial && <StackItem><Alert variant="warning" isInline title="Partial archive inventory">Validated rows from a failed read are informational. They do not establish complete inventory or authorize an operation.</Alert></StackItem>}
                    {repositories === undefined && parsed?.error === null && <StackItem><Alert variant="warning" isInline title="Archive inventory unavailable">The response did not provide a validated repository inventory.</Alert></StackItem>}
                    {repositories !== undefined &&
                    <StackItem>
                        <Card>
                            <CardTitle>{parsed?.partial ? 'Archived repositories (partial)' : 'Archived repositories'}</CardTitle>
                            <CardBody>
                                <ListingTable
                                    aria-label="Archived repositories and revisions"
                                    columns={['Repository', 'Type', 'State', 'Current', 'Retained', 'Current size']}
                                    emptyCaption={parsed?.partial ? 'No repository rows in this partial response' : 'Nothing archived yet'}
                                    rows={repositories.map(repository => ({
                                        props: { key: `${repository.repository_type}:${repository.repository_id}` },
                                        expandedContent: <RevisionsTable repository={repository} />,
                                        columns: [
                                            {
                                                title: (
                                                    <a
                                                        href={huggingFaceRepositoryUrl(
                                                            repository.repository_type,
                                                            repository.repository_id,
                                                        )}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        aria-label={`Open ${repository.repository_id} on Hugging Face in a new tab`}
                                                    >
                                                        {repository.repository_id}
                                                    </a>
                                                ),
                                            },
                                            repository.repository_type,
                                            {
                                                title: (
                                                    repository.managed
                                                        ? <EnabledLabel enabled={repository.enabled === true} />
                                                        : <UnmanagedLabel />
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
                    </StackItem>}
                </>}
        </Stack>
    );
};
