/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The application shell: one tab per contract surface (docs/cockpit.md §3),
 * added as its work package lands.
 */

import React, { useState } from 'react';

import { Page, PageSection } from "@patternfly/react-core/dist/esm/components/Page/index.js";
import { Tab, Tabs, TabTitleText } from "@patternfly/react-core/dist/esm/components/Tabs/index.js";

import { Dashboard } from './dashboard';

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
                </Tabs>
            </PageSection>
        </Page>
    );
};
