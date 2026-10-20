/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The application shell: one tab per contract surface (docs/cockpit.md §3),
 * added as its work package lands.
 */

import React, { useState } from 'react';

import { Alert } from "@patternfly/react-core/dist/esm/components/Alert/index.js";
import { Page, PageSection } from "@patternfly/react-core/dist/esm/components/Page/index.js";
import { Tab, Tabs, TabTitleText } from "@patternfly/react-core/dist/esm/components/Tabs/index.js";

import { ArchiveBrowser } from './archive';
import { Configuration } from './configuration';
import { Dashboard } from './dashboard';
import { useConnection } from './hooks';
import { Maintenance } from './maintenance';
import { RunReports } from './reports';
import { SyncOperations } from './sync';
import { Verification } from './verify';

const AdministrativeControls = ({ children }: { children: React.ReactNode }) => {
    const connection = useConnection();
    return (
        <fieldset className="hfcache-administrative-controls" disabled={!connection.administrative}>
            {children}
        </fieldset>
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
