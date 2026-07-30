/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Live unit activity (docs/cockpit.md §5): a journal follower rendering the
 * closed §24 event vocabulary — latest event per repository plus the raw
 * tail. Checkpoint-grained by design; no invented percentages.
 */

import React, { useEffect, useState } from 'react';

import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import {
    DescriptionList, DescriptionListDescription, DescriptionListGroup, DescriptionListTerm,
} from "@patternfly/react-core/dist/esm/components/DescriptionList/index.js";
import { Label } from "@patternfly/react-core/dist/esm/components/Label/index.js";
import { Stack, StackItem } from "@patternfly/react-core/dist/esm/layouts/Stack/index.js";

import { followUnitJournal } from './api/journal';
import { interpretEvent, JournalEvent } from './lib/events';

function latestPerRepository(events: JournalEvent[]): Array<[string, JournalEvent]> {
    const latest = new Map<string, JournalEvent>();
    for (const event of events) {
        if (event.repository !== undefined)
            latest.set(event.repository, event);
    }
    return [...latest.entries()];
}

export const UnitActivity = ({ unit }: { unit: string }) => {
    const [lines, setLines] = useState<string[]>([]);

    useEffect(() => {
        const stop = followUnitJournal(unit, line => {
            setLines(previous => [...previous, line].slice(-200));
        });
        return stop;
    }, [unit]);

    const events = lines.map(interpretEvent).filter(event => event !== null);
    const perRepository = latestPerRepository(events);

    return (
        <Card>
            <CardTitle>Live activity — {unit}</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    {perRepository.length > 0 &&
                        <StackItem>
                            <DescriptionList isHorizontal isCompact>
                                {perRepository.map(([repository, event]) => (
                                    <DescriptionListGroup key={repository}>
                                        <DescriptionListTerm>{repository}</DescriptionListTerm>
                                        <DescriptionListDescription>
                                            <Label isCompact>{event.event}</Label>
                                        </DescriptionListDescription>
                                    </DescriptionListGroup>
                                ))}
                            </DescriptionList>
                        </StackItem>}
                    <StackItem>
                        <pre className="hfcache-journal">
                            {lines.length === 0 ? 'Waiting for journal lines…' : lines.join('\n')}
                        </pre>
                    </StackItem>
                </Stack>
            </CardBody>
        </Card>
    );
};
