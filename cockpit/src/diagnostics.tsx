/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Advisory source/selected-release/client evidence, never effect permission.
 */
import React from 'react';

import { Alert } from '@patternfly/react-core/dist/esm/components/Alert/index.js';
import { Button } from '@patternfly/react-core/dist/esm/components/Button/index.js';
import { Card, CardBody, CardTitle } from '@patternfly/react-core/dist/esm/components/Card/index.js';
import { DescriptionList, DescriptionListDescription, DescriptionListGroup, DescriptionListTerm } from '@patternfly/react-core/dist/esm/components/DescriptionList/index.js';
import { ExpandableSection } from '@patternfly/react-core/dist/esm/components/ExpandableSection/index.js';
import { Stack, StackItem } from '@patternfly/react-core/dist/esm/layouts/Stack/index.js';

import { readClientAuthority } from './api/hfcache';
import { currentOperationHost } from './api/operations';
import { Loading, QueryError } from './components';
import { useConnection, useHostProfile, useOperations } from './hooks';
import { BuildInfoError, compareBuildSource, embeddedBuildInfo, parseBuildInfo } from './lib/build-info';
import type { BuildInfo } from './lib/build-info';

const Item = ({ term, children }: { term: string; children: React.ReactNode }) => (
    <DescriptionListGroup><DescriptionListTerm>{term}</DescriptionListTerm><DescriptionListDescription>{children}</DescriptionListDescription></DescriptionListGroup>
);

export const DeploymentDiagnostics = ({ buildInfo = embeddedBuildInfo }: { buildInfo?: unknown }) => {
    const connection = useConnection();
    const host = currentOperationHost();
    const profile = useHostProfile();
    const { views } = useOperations();
    const authority = views.authority;
    const client = connection.administrative && !authority.loading && authority.error === null &&
        authority.generation === connection.generation && authority.scope?.host === host
        ? authority.scope
        : null;
    const selected = connection.administrative && !profile.loading && profile.error === null &&
        profile.generation === connection.generation && profile.host === host && profile.profile?.state !== 'unknown'
        ? profile.profile
        : null;
    let browser: Readonly<BuildInfo> | null = null;
    let browserError: BuildInfoError | null = null;
    try { browser = parseBuildInfo(buildInfo) } catch { browserError = new BuildInfoError() }
    const comparison = browser ? compareBuildSource(browser, selected?.source_commit ?? null) : 'unavailable';
    const mismatch = browser?.source_commit !== null && browser?.source_commit !== undefined && selected !== null &&
        browser.source_commit !== selected.source_commit;

    return (
        <Card aria-label="Source and connection diagnostics">
            <CardTitle>Source and connection diagnostics</CardTitle>
            <CardBody>
                <ExpandableSection toggleText="Inspect browser, selected release and API identities">
                    <Stack hasGutter>
                        <StackItem>These read identities grant no workload permission. Selected physical bindings do not identify the running API payload; package versions and health readiness do not establish archive writability.</StackItem>
                        {browserError && <StackItem><Alert variant="warning" isInline title="Browser build provenance is unavailable">{browserError.message}</Alert></StackItem>}
                        {comparison === 'unavailable' && !browserError && <StackItem><Alert variant="warning" isInline title="Browser source comparison is unavailable">A production build with known provenance and fresh selected-release evidence is required for comparison.</Alert></StackItem>}
                        {browser?.source_dirty === true && <StackItem><Alert variant="warning" isInline title="Browser build contains uncommitted changes">Its commit alone cannot identify the loaded browser inputs.</Alert></StackItem>}
                        {mismatch && <StackItem><Alert variant="warning" isInline title="Browser and selected-release source commits differ">Preserve both identities and verify the intended deployment. This comparison does not identify the running payload.</Alert></StackItem>}
                        {comparison === 'same-source' && <StackItem>Browser and selected-release source commits agree. This agreement does not prove bundle equality or the running payload.</StackItem>}
                        <StackItem>
                            <DescriptionList isHorizontal isCompact>
                                <Item term="Browser source commit"><code>{browser?.source_commit ?? 'unknown'}</code></Item>
                                <Item term="Browser working-copy state">{browser?.source_dirty === true ? 'dirty' : browser?.source_dirty === false ? 'clean at build time' : 'unknown'}</Item>
                                <Item term="Browser build-input SHA-256"><code>{browser?.inputs_sha256 ?? 'unknown'}</code></Item>
                            </DescriptionList>
                            <p>The input digest covers declared public browser build inputs. It is separate from the output bundle checksum and installed dependency bytes. Development/watch builds report unknown provenance.</p>
                        </StackItem>
                        {profile.loading && <StackItem><Loading /></StackItem>}
                        {profile.error && <StackItem><QueryError error={profile.error} /></StackItem>}
                        {selected === null && <StackItem>Selected protected release identities are unavailable or stale.</StackItem>}
                        {selected !== null &&
                            <StackItem>
                                <DescriptionList isHorizontal isCompact>
                                    <Item term="Selected release source commit"><code>{selected.source_commit}</code></Item>
                                    <Item term="Selected protected index SHA-256"><code>{selected.index_sha256}</code></Item>
                                    <Item term="Selected immutable image identity"><code>{selected.image}</code></Item>
                                </DescriptionList>
                            </StackItem>}
                        {authority.loading && <StackItem><Loading /></StackItem>}
                        {authority.error && <StackItem><QueryError error={authority.error} /></StackItem>}
                        {client === null && <StackItem>Authenticated client/API identity is unavailable or stale.</StackItem>}
                        {client !== null &&
                            <StackItem>
                                <DescriptionList isHorizontal isCompact>
                                    <Item term="Client host">{client.host}</Item><Item term="Fixed client endpoint"><code>{client.endpoint}</code></Item>
                                    <Item term="Public client profile fingerprint"><code>{client.profile}</code></Item>
                                    <Item term="Credential class">{client.credentialClass}</Item><Item term="Archive UUID"><code>{client.archiveId ?? 'unconfirmed'}</code></Item>
                                    <Item term="Authenticated API instance"><code>{client.instanceId}</code></Item>
                                </DescriptionList>
                            </StackItem>}
                        <StackItem>
                            <Button
variant="secondary" isDisabled={!connection.administrative || authority.loading}
                    onClick={() => { readClientAuthority().catch(() => { /* Original classified result remains in the authority view. */ }) }}
                            >Refresh diagnostic client identity
                            </Button>
                        </StackItem>
                    </Stack>
                </ExpandableSection>
            </CardBody>
        </Card>
    );
};
