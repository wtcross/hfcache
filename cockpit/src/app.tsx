/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Derived from cockpit-project/starter-kit src/app.tsx @ a099cb10.
 * CPT-002 scaffold: proves the bridge (cockpit.file) and the PatternFly
 * toolchain end-to-end; the real surfaces land with CPT-004 onward.
 */

import React, { useEffect, useState } from 'react';

import { Alert } from "@patternfly/react-core/dist/esm/components/Alert/index.js";
import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import { Page } from "@patternfly/react-core/dist/esm/components/Page/index.js";

import cockpit from 'cockpit';

export const Application = () => {
    const [hostname, setHostname] = useState('');

    useEffect(() => {
        const file = cockpit.file('/etc/hostname');
        file.watch(content => setHostname(content?.trim() ?? ''));
        return file.close;
    }, []);

    return (
        <Page className="pf-m-no-sidebar">
            <Card>
                <CardTitle>hfcache</CardTitle>
                <CardBody>
                    <Alert
                        variant="info"
                        title={cockpit.format("hfcache administration scaffold (CPT-002), running on $0", hostname)}
                    />
                </CardBody>
            </Card>
        </Page>
    );
};
