/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The application shell: one tab per contract surface (docs/cockpit.md §3),
 * added as its work package lands.
 */

import React, { useState } from 'react';

import { Alert } from "@patternfly/react-core/dist/esm/components/Alert/index.js";
import { Button } from "@patternfly/react-core/dist/esm/components/Button/index.js";
import { Page, PageSection } from "@patternfly/react-core/dist/esm/components/Page/index.js";
import { Tab, Tabs, TabTitleText } from "@patternfly/react-core/dist/esm/components/Tabs/index.js";

import { ArchiveBrowser } from './archive';
import { Configuration } from './configuration';
import { Dashboard } from './dashboard';
import { DeploymentDiagnostics } from './diagnostics';
import { useConnection, useHostProfile } from './hooks';
import { readHostProfile } from './api/profile';
import { QueryError } from './components';
import { Maintenance } from './maintenance';
import { RunReports } from './reports';
import { SyncOperations } from './sync';
import { Verification } from './verify';
import { OriginalOperations } from './operations';

const AdministrativeControls = ({ children }: { children: React.ReactNode }) => {
    const connection = useConnection();
    return (
        <fieldset className="hfcache-administrative-controls" disabled={!connection.administrative}>
            {children}
        </fieldset>
    );
};

const HostRestrictions = () => {
    const profile = useHostProfile();
    const connection = useConnection();
    return (
        <>
            <Alert variant={profile.permissions.archive ? 'info' : 'warning'} isInline title="Host restrictions">
                <p>{profile.reason}</p>
                <Button
variant="link" isDisabled={profile.loading || !connection.administrative}
                    onClick={() => { readHostProfile().catch(() => { /* Error remains visible below. */ }) }}
                >
                    Refresh host restrictions
                </Button>
            </Alert>
            {profile.error && <QueryError error={profile.error} />}
        </>
    );
};

export const Application = () => {
    const [activeTab, setActiveTab] = useState<string | number>('overview');
    const connection = useConnection();

    return (
        <Page className="pf-m-no-sidebar">
            <PageSection>
                {!connection.administrative &&
                    <Alert variant="warning" isInline title="Administrative access is required for client and host actions">
                        Enable administrative access in Cockpit. Existing operation observation
                        and host changes remain uncertain until reconciled; no action is repeated.
                    </Alert>}
                <OriginalOperations />
                <HostRestrictions />
                <DeploymentDiagnostics />
                <Tabs
                    activeKey={activeTab}
                    onSelect={(_event, eventKey) => setActiveTab(eventKey)}
                    mountOnEnter
                    unmountOnExit
                >
                    <Tab eventKey="overview" title={<TabTitleText>Overview</TabTitleText>}>
                        <AdministrativeControls><Dashboard /></AdministrativeControls>
                    </Tab>
                    <Tab eventKey="sync" title={<TabTitleText>Sync</TabTitleText>}>
                        <AdministrativeControls><SyncOperations /></AdministrativeControls>
                    </Tab>
                    <Tab eventKey="archive" title={<TabTitleText>Repositories</TabTitleText>}>
                        <AdministrativeControls><ArchiveBrowser /></AdministrativeControls>
                    </Tab>
                    <Tab eventKey="configuration" title={<TabTitleText>Configuration</TabTitleText>}>
                        <AdministrativeControls><Configuration /></AdministrativeControls>
                    </Tab>
                    <Tab eventKey="verify" title={<TabTitleText>Verification</TabTitleText>}>
                        <AdministrativeControls><Verification /></AdministrativeControls>
                    </Tab>
                    <Tab eventKey="runs" title={<TabTitleText>Runs</TabTitleText>}>
                        <AdministrativeControls><RunReports /></AdministrativeControls>
                    </Tab>
                    <Tab eventKey="maintenance" title={<TabTitleText>Maintenance</TabTitleText>}>
                        <AdministrativeControls><Maintenance /></AdministrativeControls>
                    </Tab>
                </Tabs>
            </PageSection>
        </Page>
    );
};
