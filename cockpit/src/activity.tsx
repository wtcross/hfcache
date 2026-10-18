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
import { RecoveryHandles } from './components';
import { useOperationHandles } from './hooks';
import { interpretEvent, interpretOperationLine, JournalEvent } from './lib/events';
import { appendDisplayLine } from './lib/stream';

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
    const { handles, reset: resetHandles, onNotice } = useOperationHandles();

    useEffect(() => {
        setLines([]);
        resetHandles();
        const stop = followUnitJournal(unit, line => {
            setLines(previous => appendDisplayLine(previous, line));
        }, onNotice);
        return stop;
    }, [unit, onNotice, resetHandles]);

    const events = lines.map(interpretEvent).filter(event => event !== null);
    const perRepository = latestPerRepository(events);
    const notices = lines.map(interpretOperationLine).filter(notice => notice !== null);
    const progress = [...notices].reverse().find(notice => notice.kind === 'progress');
    const gap = [...notices].reverse().find(notice => notice.kind === 'gap');

    return (
        <Card>
            <CardTitle>Live activity — {unit}</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem><RecoveryHandles evidence={handles} /></StackItem>
                    {progress?.kind === 'progress' &&
                        <StackItem>
                            <Label isCompact>{progress.phase}</Label>{' '}
                            [{progress.sequence}] {progress.message}
                        </StackItem>}
                    {gap?.kind === 'gap' &&
                        <StackItem>Earlier operation events are no longer retained; history starts
                            at sequence {gap.oldestSequence}.
                        </StackItem>}
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
