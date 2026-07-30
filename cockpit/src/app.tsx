/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The application shell: one tab per contract surface (docs/cockpit.md §3),
 * added as its work package lands.
 */

import React, { useState } from 'react';

import { Page, PageSection } from "@patternfly/react-core/dist/esm/components/Page/index.js";
import { Tab, Tabs, TabTitleText } from "@patternfly/react-core/dist/esm/components/Tabs/index.js";

import { ArchiveBrowser } from './archive';
import { Configuration } from './configuration';
import { Dashboard } from './dashboard';
import { Maintenance } from './maintenance';
import { RunReports } from './reports';
import { SyncOperations } from './sync';
import { Verification } from './verify';

export const Application = () => {
    const [activeTab, setActiveTab] = useState<string | number>('overview');

    return (
        <Page className="pf-m-no-sidebar">
            <PageSection>
                <Tabs
                    activeKey={activeTab}
                    onSelect={(_event, eventKey) => setActiveTab(eventKey)}
                    mountOnEnter
                    unmountOnExit
                >
                    <Tab eventKey="overview" title={<TabTitleText>Overview</TabTitleText>}>
                        <Dashboard />
                    </Tab>
                    <Tab eventKey="sync" title={<TabTitleText>Sync</TabTitleText>}>
                        <SyncOperations />
                    </Tab>
                    <Tab eventKey="archive" title={<TabTitleText>Repositories</TabTitleText>}>
                        <ArchiveBrowser />
                    </Tab>
                    <Tab eventKey="configuration" title={<TabTitleText>Configuration</TabTitleText>}>
                        <Configuration />
                    </Tab>
                    <Tab eventKey="verify" title={<TabTitleText>Verification</TabTitleText>}>
                        <Verification />
                    </Tab>
                    <Tab eventKey="runs" title={<TabTitleText>Runs</TabTitleText>}>
                        <RunReports />
                    </Tab>
                    <Tab eventKey="maintenance" title={<TabTitleText>Maintenance</TabTitleText>}>
                        <Maintenance />
                    </Tab>
                </Tabs>
            </PageSection>
        </Page>
    );
};
