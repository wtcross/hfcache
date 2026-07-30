/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Maintenance (docs/cockpit.md §3): prune and recover as dry-run-first
 * flows — one describes, the other performs, and neither is a default —
 * and repair as the one explicit republish (decision 89).
 */

import React, { useState } from 'react';

import { Button } from "@patternfly/react-core/dist/esm/components/Button/index.js";
import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import {
    ExpandableSection,
} from "@patternfly/react-core/dist/esm/components/ExpandableSection/index.js";
import {
    Modal, ModalBody, ModalFooter, ModalHeader,
} from "@patternfly/react-core/dist/esm/components/Modal/index.js";
import { TextInput } from "@patternfly/react-core/dist/esm/components/TextInput/index.js";
import { Flex, FlexItem } from "@patternfly/react-core/dist/esm/layouts/Flex/index.js";
import { Stack, StackItem } from "@patternfly/react-core/dist/esm/layouts/Stack/index.js";

import { runHfcache, runHfcacheStreaming } from './api/hfcache';
import { DataSummary, EnvelopeAlert, Loading, QueryError } from './components';
import { parseSelector, SelectorError } from './lib/command';
import { classifyEnvelope, Envelope } from './lib/envelope';

const DryRunApplyCard = ({ title, command, intro, applyWarning }: {
    title: string;
    command: 'prune' | 'recover';
    intro: string;
    applyWarning: string;
}) => {
    const [busy, setBusy] = useState(false);
    const [dryRun, setDryRun] = useState<Envelope | null>(null);
    const [applied, setApplied] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const [confirming, setConfirming] = useState(false);

    const run = (apply: boolean) => {
        setConfirming(false);
        setBusy(true);
        setError(null);
        if (apply)
            setApplied(null);
        else
            setDryRun(null);
        runHfcache([command, apply ? '--apply' : '--dry-run'])
                .then(envelope => {
                    if (apply) {
                        setApplied(envelope);
                    } else {
                        setDryRun(envelope);
                        setApplied(null);
                    }
                }, failure => setError(failure as Error))
                .finally(() => setBusy(false));
    };

    const canApply = dryRun !== null && classifyEnvelope(dryRun) === 'success';

    return (
        <Card>
            <CardTitle>{title}</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>{intro}</StackItem>
                    <StackItem>
                        <Flex>
                            <FlexItem>
                                <Button variant="secondary" isDisabled={busy} onClick={() => run(false)}>
                                    Dry run
                                </Button>
                            </FlexItem>
                            <FlexItem>
                                <Button
                                    variant="danger"
                                    isDisabled={busy || !canApply}
                                    onClick={() => setConfirming(true)}
                                >
                                    Apply
                                </Button>
                            </FlexItem>
                            {busy && <FlexItem><Loading /></FlexItem>}
                        </Flex>
                    </StackItem>
                    {error !== null && <StackItem><QueryError error={error} /></StackItem>}
                    {dryRun !== null &&
                        <>
                            <StackItem><EnvelopeAlert envelope={dryRun} /></StackItem>
                            <StackItem><DataSummary data={dryRun.data} /></StackItem>
                            <StackItem>
                                <ExpandableSection toggleText="Dry-run detail">
                                    <pre className="hfcache-journal">
                                        {JSON.stringify(dryRun.data, null, 2)}
                                    </pre>
                                </ExpandableSection>
                            </StackItem>
                        </>}
                    {applied !== null &&
                        <>
                            <StackItem><EnvelopeAlert envelope={applied} /></StackItem>
                            <StackItem><DataSummary data={applied.data} /></StackItem>
                        </>}
                </Stack>

                <Modal
                    isOpen={confirming}
                    onClose={() => setConfirming(false)}
                    variant="small"
                    aria-label={`Apply ${command}`}
                >
                    <ModalHeader title={`Apply ${command}`} />
                    <ModalBody>{applyWarning}</ModalBody>
                    <ModalFooter>
                        <Button variant="danger" onClick={() => run(true)}>{`Run ${command} --apply`}</Button>
                        <Button variant="link" onClick={() => setConfirming(false)}>Cancel</Button>
                    </ModalFooter>
                </Modal>
            </CardBody>
        </Card>
    );
};

const RepairCard = () => {
    const [selectorText, setSelectorText] = useState('');
    const [reason, setReason] = useState('');
    const [confirming, setConfirming] = useState(false);
    const [running, setRunning] = useState(false);
    const [feed, setFeed] = useState<string[]>([]);
    const [result, setResult] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);

    let validationError: string | null = null;
    if (selectorText !== '') {
        try {
            const selector = parseSelector(selectorText);
            if (selector.sha === undefined)
                validationError = 'repair takes TYPE:ID@SHA with the full 40-character commit SHA';
        } catch (failure) {
            validationError = failure instanceof SelectorError ? failure.message : String(failure);
        }
    }

    const run = () => {
        setConfirming(false);
        setRunning(true);
        setFeed([]);
        setResult(null);
        setError(null);
        const command = reason === ''
            ? ['repair', selectorText]
            : ['repair', selectorText, '--reason', reason];
        runHfcacheStreaming(command, {
            onLine: line => setFeed(previous => [...previous, line].slice(-100)),
        })
                .then(envelope => setResult(envelope), failure => setError(failure as Error))
                .finally(() => setRunning(false));
    };

    return (
        <Card>
            <CardTitle>Repair a damaged revision</CardTitle>
            <CardBody>
                <Stack hasGutter>
                    <StackItem>
                        The explicit republish for a revision a verification found damaged: the
                        exact SHA is re-downloaded in isolation, verified against the
                        <strong> original</strong> manifest, and only then switched in. If any
                        expected digest differs, repair stops without changing the published
                        revision (AD-13). Copy the SHA from the verification finding.
                    </StackItem>
                    <StackItem>
                        <TextInput
                            id="repair-selector"
                            aria-label="Revision selector"
                            placeholder="model:organization/name@0123456789abcdef0123456789abcdef01234567"
                            value={selectorText}
                            validated={validationError === null ? 'default' : 'error'}
                            onChange={(_event, value) => setSelectorText(value)}
                        />
                        {validationError !== null &&
                            <div className="hfcache-field-error">{validationError}</div>}
                    </StackItem>
                    <StackItem>
                        <TextInput
                            id="repair-reason"
                            aria-label="Reason"
                            placeholder="--reason (recorded in the audit trail; optional)"
                            value={reason}
                            onChange={(_event, value) => setReason(value)}
                        />
                    </StackItem>
                    <StackItem>
                        <Button
                            variant="danger"
                            isDisabled={running || selectorText === '' || validationError !== null}
                            onClick={() => setConfirming(true)}
                        >
                            Repair…
                        </Button>
                    </StackItem>
                    {running && <StackItem><Loading /></StackItem>}
                    {feed.length > 0 &&
                        <StackItem>
                            <ExpandableSection toggleText="Command log">
                                <pre className="hfcache-journal">{feed.join('\n')}</pre>
                            </ExpandableSection>
                        </StackItem>}
                    {error !== null && <StackItem><QueryError error={error} /></StackItem>}
                    {result !== null &&
                        <>
                            <StackItem><EnvelopeAlert envelope={result} /></StackItem>
                            <StackItem><DataSummary data={result.data} /></StackItem>
                        </>}
                </Stack>

                <Modal
                    isOpen={confirming}
                    onClose={() => setConfirming(false)}
                    variant="small"
                    aria-label="Start repair"
                >
                    <ModalHeader title={`Repair ${selectorText}`} />
                    <ModalBody>
                        Downloads that revision again and publishes a replacement instance; the
                        superseded instance stays readable for the configured grace period (at
                        least seven days). This runs as a transient unit — closing the tab
                        detaches this view while the repair continues, and its transaction is
                        reconciled like any other (recover describes it afterwards). It shares
                        the single archive lock.
                    </ModalBody>
                    <ModalFooter>
                        <Button variant="danger" onClick={run}>Start repair</Button>
                        <Button variant="link" onClick={() => setConfirming(false)}>Cancel</Button>
                    </ModalFooter>
                </Modal>
            </CardBody>
        </Card>
    );
};

export const Maintenance = () => (
    <Stack hasGutter>
        <StackItem>
            <DryRunApplyCard
                title="Retention (prune)"
                command="prune"
                intro={'Retention normally runs inside sync: a sixth published revision rotates the ' +
                    'oldest non-current one out (AD-04). This exists to inspect the plan and to ' +
                    'finish a rotation an earlier failure deferred.'}
                applyWarning={'Executes exactly the plan the dry run described. Where a prune can ' +
                    'fail leaving more or less data, it leaves more (TX-06).'}
            />
        </StackItem>
        <StackItem>
            <DryRunApplyCard
                title="Recovery (recover)"
                command="recover"
                intro={'Reconciles unfinished transaction journals. The dry run is always safe, ' +
                    'including on an archive that has stopped accepting writes; blocked states ' +
                    'carry their HFTXN codes and stop every mutating command until resolved.'}
                applyWarning={'Executes only a fully validated plan and is idempotent — running it ' +
                    'twice is harmless. Recovery never replaces an expected digest, never picks a ' +
                    'revision by modification time, and never deletes unknown data (AD-16).'}
            />
        </StackItem>
        <StackItem><RepairCard /></StackItem>
    </Stack>
);
