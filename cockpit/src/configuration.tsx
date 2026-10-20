/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The configuration editor (docs/cockpit.md §6, CP-11): two modes, one
 * pipeline. Form mode renders the schema and serializes canonically
 * (comments lost, and it says so); text mode edits the document verbatim.
 * Both go candidate → validate → preview → install → confirm.
 */

import React, { useEffect, useSyncExternalStore } from 'react';

import { Alert } from "@patternfly/react-core/dist/esm/components/Alert/index.js";
import { Button } from "@patternfly/react-core/dist/esm/components/Button/index.js";
import { Card, CardBody, CardTitle } from "@patternfly/react-core/dist/esm/components/Card/index.js";
import { Checkbox } from "@patternfly/react-core/dist/esm/components/Checkbox/index.js";
import {
    FormSelect, FormSelectOption,
} from "@patternfly/react-core/dist/esm/components/FormSelect/index.js";
import { TextArea } from "@patternfly/react-core/dist/esm/components/TextArea/index.js";
import { TextInput } from "@patternfly/react-core/dist/esm/components/TextInput/index.js";
import {
    ToggleGroup, ToggleGroupItem,
} from "@patternfly/react-core/dist/esm/components/ToggleGroup/index.js";
import { Flex, FlexItem } from "@patternfly/react-core/dist/esm/layouts/Flex/index.js";
import { Stack, StackItem } from "@patternfly/react-core/dist/esm/layouts/Stack/index.js";
import { ListingTable } from 'cockpit-components-table';

import {
    confirmInstalledCandidate, inspectCandidate, installCandidate, planCandidate, readInstalledConfig, removeCandidate,
    validateCandidate, writeCandidate,
} from './api/config';
import { EnvelopeAlert, Loading, QueryError, RecoveryHandles, Sha } from './components';
import {
    ConfigDocument, extractFieldPath, FieldSpec, getField, GLOBAL_FIELDS, parseConfig,
    RepositoryEntry, serializeConfig, setField, validateRevisionReference,
    configuredTagSuggestions, normalizeTags, tagInput,
} from './lib/config';
import { validateCandidateText } from './lib/candidate-guard';
import { connectionSnapshot } from './api/connection';
import { readClientAuthority } from './api/hfcache';
import { currentOperationHost, operationRegistry, operationViews, submissionBlocked } from './api/operations';
import { OperationAuthorityError } from './lib/operation-authority';
import { sameOperationScope } from './lib/operation-registry';
import type { OperationScope } from './lib/operation-registry';
import { ConfigurationSession, configurationSession, ConfigurationState } from './lib/configuration-session';
import {
    ConfigurationEvidence, ConfigurationPipelineError, ConfigurationPorts, confirmConfiguration,
    installConfiguration, MANUAL_AUTHORITY_GUIDANCE, PreparationSuperseded,
    prepareConfiguration, UNCONFIRMED_INSTALLATION,
} from './lib/config-pipeline';
import { classifyEnvelope, Envelope } from './lib/envelope';
import { useConnection, useOperations } from './hooks';
import { formatBytes, shortSha } from './lib/format';

type FieldErrors = Record<string, string>;

const FieldRow = ({ spec, value, error, onChange }: {
    spec: FieldSpec;
    value: unknown;
    error?: string;
    onChange: (value: unknown) => void;
}) => {
    const path = `${spec.table}.${spec.key}`;
    let control: React.ReactNode;
    if (spec.kind === 'bool') {
        control = (
            <Checkbox
                id={path}
                isChecked={value === true}
                label={path}
                onChange={(_event, checked) => onChange(checked)}
            />
        );
    } else if (spec.kind === 'enum' || spec.options !== undefined) {
        control = (
            <FormSelect
                id={path}
                aria-label={path}
                value={String(value ?? '')}
                onChange={(_event, selected) => onChange(spec.kind === 'int' ? Number(selected) : selected)}
            >
                {(spec.options ?? []).map(option => (
                    <FormSelectOption key={option} value={option} label={String(option)} />
                ))}
            </FormSelect>
        );
    } else {
        control = (
            <TextInput
                id={path}
                aria-label={path}
                value={String(value ?? '')}
                validated={error === undefined ? 'default' : 'error'}
                onChange={(_event, text) => {
                    if (spec.kind === 'int')
                        onChange(/^\d+$/.test(text) ? Number(text) : text);
                    else
                        onChange(text);
                }}
            />
        );
    }
    return (
        <div className="hfcache-field">
            {spec.kind !== 'bool' && <label htmlFor={path}><code>{path}</code></label>}
            {control}
            <div className="hfcache-issue-guidance">{spec.hint}</div>
            {error !== undefined && <div className="hfcache-field-error">{error}</div>}
        </div>
    );
};

const GlobalFields = ({ document, errors, onChange }: {
    document: ConfigDocument;
    errors: FieldErrors;
    onChange: (next: ConfigDocument) => void;
}) => (
    <div className="hfcache-field-grid">
        {GLOBAL_FIELDS.map(spec => (
            <FieldRow
                key={`${spec.table}.${spec.key}`}
                spec={spec}
                value={getField(document, spec)}
                error={errors[`${spec.table}.${spec.key}`]}
                onChange={value => onChange(setField(document, spec, value))}
            />
        ))}
    </div>
);

const RepositoryRow = ({ entry, index, suggestions, onChange, onRemove }: {
    entry: RepositoryEntry;
    index: number;
    suggestions: string[];
    onChange: (entry: RepositoryEntry) => void;
    onRemove: () => void;
}) => {
    const revisionError = validateRevisionReference(entry.revision ?? 'main');
    let tagError: string | null = null;
    try { normalizeTags(entry.tags ?? []) } catch (failure) { tagError = (failure as Error).message }

    return (
        <Card isCompact className="hfcache-repository">
            <CardBody>
                <Flex>
                    <FlexItem grow={{ default: 'grow' }}>
                        <TextInput
                            id={`repo-id-${index}`}
                            aria-label="Repository id"
                            placeholder="organization/name"
                            value={entry.id}
                            onChange={(_event, id) => onChange({ ...entry, id })}
                        />
                    </FlexItem>
                    <FlexItem>
                        <FormSelect
                            id={`repo-type-${index}`}
                            aria-label="Repository type"
                            value={entry.type}
                            onChange={(_event, type) =>
                                onChange({ ...entry, type: type as RepositoryEntry['type'] })}
                        >
                            <FormSelectOption value="model" label="model" />
                            <FormSelectOption value="dataset" label="dataset" />
                        </FormSelect>
                    </FlexItem>
                    <FlexItem>
                        <TextInput
                            id={`repo-revision-${index}`}
                            aria-label="Revision"
                            placeholder="main"
                            value={entry.revision ?? 'main'}
                            validated={revisionError === null ? 'default' : 'error'}
                            onChange={(_event, revision) => onChange({ ...entry, revision })}
                        />
                    </FlexItem>
                    <FlexItem>
                        <Checkbox
                            id={`repo-enabled-${index}`}
                            label="enabled"
                            isChecked={entry.enabled ?? true}
                            onChange={(_event, enabled) => onChange({ ...entry, enabled })}
                        />
                    </FlexItem>
                    <FlexItem>
                        <Button variant="link" isDanger onClick={onRemove}>Remove</Button>
                    </FlexItem>
                </Flex>
                <TextInput
                    id={`repo-deps-${index}`}
                    aria-label="Declared dependencies"
                    placeholder="declared_dependencies, comma-separated org/name entries"
                    value={(entry.declared_dependencies ?? []).join(', ')}
                    onChange={(_event, text) => onChange({
                        ...entry,
                        declared_dependencies: text.split(',')
                                .map(part => part.trim())
                                .filter(part => part !== ''),
                    })}
                />
                <label htmlFor={`repo-tags-${index}`}>Tags</label>
                <TextInput
                    id={`repo-tags-${index}`}
                    aria-label="Tags"
                    value={(entry.tags ?? []).join(',')}
                    validated={tagError === null ? 'default' : 'error'}
                    onChange={(_event, text) => onChange({ ...entry, tags: tagInput(text) })}
                />
                <div className="hfcache-issue-guidance">
                    Comma-separated flat labels. Outer spaces are trimmed and ASCII letters lowercased
                    when serialized; duplicates are removed. Tags do not change downloads or retention.
                    The backend validates the final candidate.
                </div>
                {tagError !== null && <div className="hfcache-field-error">{tagError}</div>}
                {suggestions.length > 0 &&
                    <FormSelect
                        aria-label="Add an existing configured tag"
                        value=""
                        onChange={(_event, tag) => {
                            if (tag !== '')
                                onChange({ ...entry, tags: [...(entry.tags ?? []), tag] });
                        }}
                    >
                        <FormSelectOption value="" label="Add an existing configured tag…" />
                        {suggestions.map(tag => <FormSelectOption key={tag} value={tag} label={tag} />)}
                    </FormSelect>}
                {revisionError !== null &&
                    <div className="hfcache-field-error">{revisionError}</div>}
            </CardBody>
        </Card>
    );
};

const Repositories = ({ document, onChange }: {
    document: ConfigDocument;
    onChange: (next: ConfigDocument) => void;
}) => {
    const entries = document.repositories ?? [];
    const suggestions = configuredTagSuggestions(document);
    const replace = (repositories: RepositoryEntry[]) => onChange({ ...document, repositories });
    return (
        <Stack hasGutter>
            <StackItem>
                Removing a repository never deletes its archive (AD-06): its revisions remain
                and report as unmanaged (HFWRN007). Declaring a dependency does not archive it.
            </StackItem>
            {entries.map((entry, index) => (
                <StackItem key={index}>
                    <RepositoryRow
                        entry={entry}
                        index={index}
                        suggestions={suggestions}
                        onChange={changed => replace(entries.map((e, i) => i === index ? changed : e))}
                        onRemove={() => replace(entries.filter((_e, i) => i !== index))}
                    />
                </StackItem>
            ))}
            <StackItem>
                <Button
                    variant="secondary"
                    onClick={() => replace([...entries, {
                        id: '',
                        type: 'model',
                        revision: 'main',
                        enabled: true,
                        tags: [],
                        declared_dependencies: [],
                    }])}
                >
                    Add repository
                </Button>
            </StackItem>
        </Stack>
    );
};

interface PlanRepository {
    repository_id?: string;
    repository_type?: string;
    requested_revision?: string;
    resolved_commit_sha?: string | null;
    upstream_state?: string;
    file_count?: number | null;
    logical_bytes?: number | null;
    estimated_new_bytes?: number | null;
    projected_publication_bytes?: number | null;
    publication_mode?: string;
}

const PlanPreview = ({ envelope }: { envelope: Envelope }) => {
    const repositories = ((envelope.data ?? {}) as { repositories?: PlanRepository[] })
            .repositories ?? [];
    return (
        <Stack hasGutter>
            <StackItem>
                The sizing preview the runbook requires before enabling a repository
                (docs/operations.md §3): the dataset quota is sized from these numbers.
            </StackItem>
            <StackItem>
                <ListingTable
                    aria-label="Plan preview"
                    variant="compact"
                    columns={['Repository', 'Revision', 'Resolved', 'Files', 'Logical', 'New bytes', 'Publication']}
                    emptyCaption="Nothing to preview"
                    rows={repositories.map((repository, index) => ({
                        props: { key: repository.repository_id ?? String(index) },
                        columns: [
                            repository.repository_id ?? '—',
                            repository.requested_revision ?? '—',
                            { title: <Sha sha={repository.resolved_commit_sha ?? null} short={shortSha(repository.resolved_commit_sha)} /> },
                            repository.file_count ?? '—',
                            formatBytes(repository.logical_bytes),
                            formatBytes(repository.estimated_new_bytes),
                            `${formatBytes(repository.projected_publication_bytes)} (${repository.publication_mode ?? '?'})`,
                        ],
                    }))}
                />
            </StackItem>
        </Stack>
    );
};

const ports = (scope: Readonly<OperationScope>): ConfigurationPorts => ({
    write: writeCandidate,
    validate: guard => validateCandidate(guard, scope.archiveId === null ? undefined : scope.authorityFingerprint),
    preview: (selectors, guard, notice) => planCandidate(selectors, guard, notice, scope),
    install: installCandidate,
    confirm: expected => confirmInstalledCandidate(expected, scope.authorityFingerprint),
});

function sessionBusy(state: ConfigurationState): boolean {
    return state.loading || ['checking', 'installing', 'confirming', 'inspecting', 'discarding'].includes(state.phase);
}

function loadInstalled(session: ConfigurationSession): void {
    const current = session.snapshot();
    if (sessionBusy(current) || current.diskGuard || current.uncertainty !== null)
        return;
    session.patch({
        initialized: true,
        loading: true,
        loadError: null,
        preparation: null,
        proposal: null,
        phase: 'idle',
        generation: connectionSnapshot().generation
    });
    readInstalledConfig().then(content => {
        validateCandidateText(content, true);
        let parsed: ConfigDocument | null = null;
        try { parsed = parseConfig(content) } catch { /* Text editing remains available. */ }
        session.patch({
            installedText: content,
            loading: false,
            text: content,
            document: parsed,
            mode: parsed === null ? 'text' : 'form',
            loadError: null,
            preparation: null,
            proposal: null,
            phase: 'idle',
            draftRevision: session.snapshot().draftRevision + 1,
        });
    })
            .catch(failure => session.patch({ loadError: failure as Error, loading: false }));
}

export const Configuration = ({ session = configurationSession }: { session?: ConfigurationSession }) => {
    const state = useSyncExternalStore(session.subscribe, session.snapshot);
    const {
        installedText, loadError, mode, document, text, fieldErrors, phase, validation, plan,
        fingerprint, pipelineError, preparation, diskGuard, connectionChanged,
    } = state;
    const connection = useConnection();
    const operations = useOperations();
    const unconfirmed = state.uncertainty === 'install';
    const busy = sessionBusy(state);
    const currentAuthority = operations.views.authority.scope;
    const authorityFresh = operations.views.authority.generation === connection.generation && currentAuthority !== null &&
        state.authority !== null && sameOperationScope(state.authority, currentAuthority);
    const fresh = connection.administrative && state.generation === connection.generation && authorityFresh;
    const inspectionFresh = connection.administrative && state.inspectedGeneration === connection.generation;
    const stagedMatches = inspectionFresh && state.inspection?.candidate === 'matching' &&
        state.inspection.installedBase === 'matching';
    const installedMatches = inspectionFresh && state.inspection?.installedCandidate === 'matching' &&
        state.inspection.backupBase === 'matching';
    const authorityIsCurrent = (scope: Readonly<OperationScope> | null): boolean => {
        const latest = operationViews().authority;
        const active = connectionSnapshot();
        return scope !== null && active.administrative && latest.generation === active.generation &&
            !latest.loading && latest.error === null && latest.scope !== null &&
            scope.host === currentOperationHost() && sameOperationScope(scope, latest.scope);
    };
    const setMode = (value: 'form' | 'text') => session.patch({ mode: value });
    const setDocument = (value: ConfigDocument) => session.patch({ document: value });
    const setPipelineError = () => session.patch({ localError: 'Fix the document before changing editing mode.' });
    const setText = (value: string) => {
        try {
            validateCandidateText(value, true);
            session.patch({ text: value, localError: null });
        } catch {
            session.patch({ localError: 'Configuration text must be complete UTF-8 without NUL and at most 1 MiB.' });
        }
    };

    useEffect(() => {
        const previous = session.snapshot();
        if (previous.generation !== null && previous.generation !== connection.generation) {
            session.patch({
                connectionChanged: true,
                inspection: null,
                inspectedGeneration: null,
                confirmed: false,
                ...(previous.phase === 'ready' ? { phase: 'idle' } : {}),
                ...(previous.diskGuard && previous.uncertainty === null ? { uncertainty: 'candidate' } : {})
            });
        }
    }, [connection.generation, session]);

    useEffect(() => {
        const current = session.snapshot();
        const recovered = operations.registry.records.find(record => record.key === current.previewKey);
        if (current.previewUncertain && recovered?.state === 'terminal')
            session.patch({ previewUncertain: false });
        const authority = operations.views.authority;
        const matches = connection.administrative && authority.generation === connection.generation &&
            !authority.loading && authority.error === null && authority.scope !== null && current.authority !== null &&
            current.authority.host === currentOperationHost() && sameOperationScope(current.authority, authority.scope);
        if (!matches && (current.phase === 'ready' || current.confirmed))
            session.patch({
                ...(current.phase === 'ready' ? { phase: 'idle', preparation: null } : {}),
                confirmed: false,
                connectionChanged: true,
            });
    }, [operations.registry.records, operations.views.authority, connection.administrative, connection.generation, session]);

    useEffect(() => {
        if (session.snapshot().initialized)
            return;
        loadInstalled(session);
    }, [session]);

    const candidateContent = (): string => mode === 'text' ? text : serializeConfig(document ?? {}, new Date());
    const invalidate = () => {
        const current = session.snapshot();
        session.patch({
            draftRevision: current.draftRevision + 1,
            phase: 'idle',
            preparation: null,
            fieldErrors: {},
            localError: null
        });
    };
    const editDocument = (value: ConfigDocument) => {
        if (!busy && state.uncertainty === null) {
            try { validateCandidateText(serializeConfig(value, new Date())) } catch {
                session.patch({ localError: 'The configuration must be valid bounded text before it can be retained.' });
                return;
            }
            invalidate();
            setDocument(value);
        }
    };
    const onEvidence = (event: ConfigurationEvidence) => {
        const current = session.snapshot();
        const update: Partial<typeof current> = { evidence: [...current.evidence, event].slice(-32) };
        if (event.status === 'notice' && event.notice.kind === 'key')
            update.previewKey = event.notice.key;
        if (event.status === 'result') {
            if (event.stage === 'candidate-validate') {
                update.validation = event.envelope;
                const errors: FieldErrors = {};
                for (const issue of event.envelope.errors) {
                    const path = extractFieldPath(issue);
                    if (path !== null)
                        errors[path] = issue.message;
                }
                update.fieldErrors = errors;
            } else if (event.stage === 'candidate-preview') {
                update.plan = event.envelope;
                update.previewUncertain = classifyEnvelope(event.envelope) === 'observation';
            } else {
                update.confirmation = event.envelope;
            }
        }
        session.patch(update);
    };
    const failed = (failure: unknown, installing = false) => {
        const current = session.snapshot();
        const pipeline = failure instanceof ConfigurationPipelineError ? failure : null;
        const writeUncertain = pipeline?.stage === 'candidate-write';
        session.patch({
            pipelineError: failure as Error,
            phase: 'idle',
            preparation: null,
            uncertainty: installing
                ? 'install'
                : writeUncertain || failure instanceof PreparationSuperseded
                    ? 'candidate'
                    : current.uncertainty,
            previewUncertain: current.previewUncertain || (pipeline?.stage === 'candidate-preview' && current.previewKey !== null),
            inspection: null,
            inspectedGeneration: null,
            confirmed: false
        });
    };
    const check = (reuse = false) => {
        const current = session.snapshot();
        if (sessionBusy(current) || !connectionSnapshot().administrative || current.installedText === null ||
            current.uncertainty === 'install' || current.previewUncertain || (!reuse && submissionBlocked()))
            return;
        if (reuse
            ? !stagedMatches || current.inspectedGeneration !== connectionSnapshot().generation ||
                current.inspection?.candidate !== 'matching' || current.inspection.installedBase !== 'matching' ||
                current.guardRevision !== current.draftRevision
            : current.diskGuard !== null)
            return;
        let guard;
        try {
            guard = reuse && current.diskGuard
                ? current.diskGuard
                : Object.freeze({
                    candidateContent: candidateContent(), installedContent: current.installedText,
                });
            validateCandidateText(guard.candidateContent);
            validateCandidateText(guard.installedContent, true);
        } catch {
            session.patch({ localError: 'Configuration text must be complete UTF-8 without NUL and at most 1 MiB.' });
            return;
        }
        const capturedRevision = current.draftRevision;
        const capturedGeneration = connectionSnapshot().generation;
        const isCurrent = () => session.snapshot().draftRevision === capturedRevision &&
            connectionSnapshot().generation === capturedGeneration && connectionSnapshot().administrative;
        // Retain exact bytes BEFORE transmission; a lost write acknowledgement does not lose ownership evidence.
        const recovered = reuse && current.previewKey
            ? operations.views.records.get(current.previewKey)?.envelope
            : null;
        const originalPreview = reuse && current.previewKey
            ? operationRegistry.snapshot().records.find(record => record.key === current.previewKey)
            : null;
        session.patch({
            diskGuard: guard,
            guardRevision: capturedRevision,
            generation: capturedGeneration,
            phase: 'checking',
            preparation: null,
            proposal: null,
            validation: null,
            plan: null,
            confirmation: null,
            fingerprint: null,
            pipelineError: reuse ? current.pipelineError : null,
            reconciliationError: null,
            fieldErrors: {},
            evidence: reuse ? current.evidence : [],
            inspection: null,
            inspectedGeneration: null,
            uncertainty: null,
            connectionChanged: false,
            confirmed: false
        });
        let confirmedScope: Readonly<OperationScope> | null = null;
        const flow = async () => {
            const scope = await readClientAuthority();
            confirmedScope = scope;
            if (reuse && current.previewKey && (!originalPreview || originalPreview.state !== 'terminal' || !recovered || !current.authority ||
                !sameOperationScope(originalPreview.scope, scope) || !sameOperationScope(current.authority, scope)))
                throw new OperationAuthorityError('changed');
            session.patch({ authority: scope, previewKey: originalPreview?.key ?? null });
            const scopedPorts = ports(scope);
            return prepareConfiguration(guard, recovered
                ? { ...scopedPorts, preview: async () => recovered }
                : scopedPorts, isCurrent, { skipWrite: reuse, onEvidence });
        };
        flow().then(prepared => {
            if (!isCurrent()) {
                failed(new PreparationSuperseded());
                return;
            }
            session.patch({
                preparation: confirmedScope?.archiveId === null && prepared.proposal !== null
                    ? { ...prepared, proposal: null, blocked: 'authority' }
                    : prepared,
                proposal: confirmedScope?.archiveId === null ? null : prepared.proposal,
                phase: confirmedScope?.archiveId === null || prepared.proposal === null ? 'idle' : 'ready'
            });
        })
                .catch(failure => {
                    if (!reuse && !session.snapshot().evidence.some(event => event.stage === 'candidate-write' && event.status === 'started'))
                        session.patch({ phase: 'idle', diskGuard: null, pipelineError: failure as Error });
                    else {
                        failed(failure);
                        if (reuse)
                            session.patch({
                                pipelineError: current.pipelineError ?? failure as Error,
                                reconciliationError: failure as Error,
                                uncertainty: current.uncertainty ?? 'candidate'
                            });
                    }
                });
    };
    const install = () => {
        const current = session.snapshot();
        const proposal = current.proposal;
        if (!proposal || current.phase !== 'ready' || !connectionSnapshot().administrative ||
            current.generation !== connectionSnapshot().generation || current.uncertainty !== null || submissionBlocked())
            return;
        const generation = connectionSnapshot().generation;
        if (!current.authority || current.authority.archiveId === null)
            return;
        session.patch({
            phase: 'installing',
            pipelineError: null,
            inspection: null,
            inspectedGeneration: null,
            confirmed: false
        });
        let transmitted = false;
        const flow = async () => {
            const scope = await readClientAuthority();
            if (!current.authority || !sameOperationScope(current.authority, scope))
                throw new OperationAuthorityError('changed');
            transmitted = true;
            return installConfiguration(proposal, ports(scope), {
                onEvidence,
                isCurrent: () =>
                    connectionSnapshot().administrative && connectionSnapshot().generation === generation
            });
        };
        flow().then(confirmed => {
            session.patch({
                fingerprint: confirmed.fingerprint,
                confirmation: confirmed.envelope,
                diskGuard: null,
                proposal: null,
                preparation: null,
                phase: 'done',
                uncertainty: null,
                installedText: proposal.guard.candidateContent
            });
        })
                .catch(failure => {
                    if (transmitted) failed(failure, true);
                    else session.patch({
                        phase: 'idle',
                        preparation: null,
                        pipelineError: failure as Error,
                        uncertainty: 'candidate',
                        inspection: null,
                        inspectedGeneration: null
                    });
                });
    };
    const inspect = () => {
        const current = session.snapshot();
        if (!current.diskGuard || sessionBusy(current) || !connectionSnapshot().administrative)
            return;
        const generation = connectionSnapshot().generation;
        session.patch({
            phase: 'inspecting',
            confirmed: false,
            reconciliationError: null,
            inspection: null,
            inspectedGeneration: null
        });
        inspectCandidate(current.diskGuard).then(inspection => {
            if (connectionSnapshot().generation !== generation || !connectionSnapshot().administrative) {
                session.patch({ phase: 'idle' });
                return;
            }
            session.patch({ phase: 'idle', inspection, inspectedGeneration: generation });
        })
                .catch(failure => session.patch({ phase: 'idle', reconciliationError: failure as Error }));
    };
    const confirm = () => {
        const current = session.snapshot();
        if (!installedMatches || current.inspection?.installedCandidate !== 'matching' ||
            current.inspection.backupBase !== 'matching' || sessionBusy(current) ||
            current.inspectedGeneration !== connectionSnapshot().generation ||
            !connectionSnapshot().administrative || !current.proposal || current.uncertainty !== 'install')
            return;
        const generation = connectionSnapshot().generation;
        if (!current.authority)
            return;
        session.patch({ phase: 'confirming', reconciliationError: null });
        const originalAuthority = current.authority;
        const proposal = current.proposal;
        const confirmation = async () => {
            const scope = await readClientAuthority();
            if (!sameOperationScope(originalAuthority, scope) || !authorityIsCurrent(originalAuthority) ||
                connectionSnapshot().generation !== generation)
                throw new OperationAuthorityError('changed');
            return confirmConfiguration(proposal, ports(originalAuthority), {
                onEvidence,
                isCurrent: () => authorityIsCurrent(originalAuthority) && connectionSnapshot().generation === generation
            });
        };
        confirmation().then(result => {
            session.patch({
                phase: 'idle',
                confirmed: true,
                fingerprint: result.fingerprint,
                confirmation: result.envelope
            });
        })
                .catch(failure => session.patch({ phase: 'idle', reconciliationError: failure as Error }));
    };
    const acknowledge = () => {
        const current = session.snapshot();
        if (!current.confirmed || !current.diskGuard || !installedMatches ||
            !authorityIsCurrent(current.authority) ||
            current.inspection?.installedCandidate !== 'matching' || current.inspection.backupBase !== 'matching' || sessionBusy(current) ||
            current.inspectedGeneration !== connectionSnapshot().generation || !connectionSnapshot().administrative)
            return;
        const content = current.diskGuard.candidateContent;
        let parsed: ConfigDocument | null = null;
        try { parsed = parseConfig(content) } catch { /* Strict API confirmation already required. */ }
        session.patch({
            installedText: content,
            text: content,
            document: parsed,
            uncertainty: null,
            diskGuard: null,
            proposal: null,
            preparation: null,
            phase: 'done',
            generation: connectionSnapshot().generation,
            connectionChanged: false
        });
    };
    const cancel = () => {
        const current = session.snapshot();
        if (!current.diskGuard || sessionBusy(current) || current.uncertainty !== null || current.previewUncertain ||
            current.generation !== connectionSnapshot().generation || !connectionSnapshot().administrative)
            return;
        session.patch({ phase: 'discarding' });
        removeCandidate(current.diskGuard).then(() => {
            session.patch({
                diskGuard: null,
                preparation: null,
                proposal: null,
                phase: 'idle',
                inspection: null,
                inspectedGeneration: null
            });
        })
                .catch(failure => {
                    session.patch({
                        phase: 'idle',
                        pipelineError: failure as Error,
                        uncertainty: 'candidate',
                        inspection: null,
                        inspectedGeneration: null
                    });
                });
    };

    return (
        <Stack hasGutter>
            {connectionChanged &&
                <StackItem>
                    <Alert variant="warning" isInline title="Connection changed; installation readiness was invalidated">
                        The draft and existing failure evidence are retained. Reconcile any
                        interrupted host change before explicitly preparing another candidate.
                    </Alert>
                </StackItem>}
            {loadError !== null && <StackItem><QueryError error={loadError} /></StackItem>}
            {diskGuard === null && state.uncertainty === null && !busy &&
                <StackItem>
                    <Button
variant="link" isDisabled={!connection.administrative}
                        onClick={() => loadInstalled(session)}
                    >Reload installed configuration
                    </Button>
                </StackItem>}
            {installedText === null && loadError === null && <StackItem><Loading /></StackItem>}
            {installedText !== null &&
                <StackItem>
                    <Card>
                        <CardTitle>Configuration — /etc/hfcache/config.toml</CardTitle>
                        <CardBody>
                            <Stack hasGutter>
                                <StackItem>
                                    <ToggleGroup aria-label="Editing mode">
                                        <ToggleGroupItem
                                            text="Form (canonical; comments not preserved)"
                                            isSelected={mode === 'form'}
                                            isDisabled={busy || state.uncertainty !== null}
                                            onChange={() => {
                                                if (!busy && state.uncertainty === null && mode !== 'form') {
                                                    try {
                                                        const parsed = parseConfig(text);
                                                        invalidate();
                                                        setDocument(parsed);
                                                        setMode('form');
                                                    } catch {
                                                        setPipelineError();
                                                    }
                                                }
                                            }}
                                        />
                                        <ToggleGroupItem
                                            text="Text (verbatim)"
                                            isSelected={mode === 'text'}
                                            isDisabled={busy || state.uncertainty !== null}
                                            onChange={() => {
                                                if (mode === 'text')
                                                    return;
                                                try {
                                                    const content = serializeConfig(document ?? {}, new Date());
                                                    invalidate();
                                                    setText(content);
                                                    setMode('text');
                                                } catch {
                                                    setPipelineError();
                                                }
                                            }}
                                        />
                                    </ToggleGroup>
                                </StackItem>
                                {mode === 'form' && document !== null &&
                                    <>
                                        <StackItem>
                                            <Repositories document={document} onChange={editDocument} />
                                        </StackItem>
                                        <StackItem>
                                            <GlobalFields
                                                document={document}
                                                errors={fieldErrors}
                                                onChange={editDocument}
                                            />
                                        </StackItem>
                                    </>}
                                {mode === 'text' &&
                                    <StackItem>
                                        <TextArea
                                            id="config-text"
                                            aria-label="Configuration text"
                                            className="hfcache-config-text"
                                            value={text}
                                            rows={26}
                                            isDisabled={busy || state.uncertainty !== null}
                                            onChange={(_event, value) => {
                                                invalidate();
                                                setText(value);
                                            }}
                                        />
                                    </StackItem>}
                                <StackItem>
                                    <Flex>
                                        <FlexItem>
                                            <Button
                                                variant="primary"
                                                isDisabled={busy || operations.blocked || !connection.administrative || diskGuard !== null || state.uncertainty !== null}
                                                onClick={() => check()}
                                            >
                                                Validate candidate
                                            </Button>
                                        </FlexItem>
                                        {phase === 'ready' && preparation?.proposal != null && fresh && state.uncertainty === null &&
                                            <FlexItem>
                                                <Button variant="danger" onClick={install}>
                                                    Install validated candidate
                                                </Button>
                                            </FlexItem>}
                                        {diskGuard !== null && !busy && state.uncertainty === null && !state.previewUncertain && fresh &&
                                            <FlexItem>
                                                <Button variant="link" onClick={cancel}>Discard candidate</Button>
                                            </FlexItem>}
                                        {busy &&
                                            <FlexItem><Loading /></FlexItem>}
                                    </Flex>
                                </StackItem>
                                {pipelineError !== null &&
                                    <StackItem>
                                        {pipelineError instanceof PreparationSuperseded &&
                                            <Alert variant="warning" isInline title="Draft or administrative session changed; captured stage evidence was retained" />}
                                        {pipelineError instanceof ConfigurationPipelineError && pipelineError.envelope &&
                                            <EnvelopeAlert envelope={pipelineError.envelope} />}
                                        {!(pipelineError instanceof PreparationSuperseded) &&
                                            (!(pipelineError instanceof ConfigurationPipelineError) || pipelineError.cause) &&
                                            <QueryError error={pipelineError instanceof ConfigurationPipelineError
                                                ? pipelineError.cause!
                                                : pipelineError}
                                            />}
                                    </StackItem>}
                                {state.localError && <StackItem><Alert variant="warning" isInline title={state.localError} /></StackItem>}
                                {state.reconciliationError &&
                                    <StackItem>
                                        {state.reconciliationError instanceof ConfigurationPipelineError && state.reconciliationError.envelope &&
                                            <EnvelopeAlert envelope={state.reconciliationError.envelope} />}
                                        {(!(state.reconciliationError instanceof ConfigurationPipelineError) || state.reconciliationError.cause) &&
                                            <QueryError error={state.reconciliationError instanceof ConfigurationPipelineError
                                                ? state.reconciliationError.cause!
                                                : state.reconciliationError}
                                            />}
                                    </StackItem>}
                                {state.uncertainty === 'candidate' &&
                                    <StackItem>
                                        <Alert variant="warning" isInline title="Candidate acknowledgement is uncertain">
                                            Preserve the captured draft and base. Inspect the fixed files before any deliberate revalidation.
                                            Changed, absent or unknown files do not prove that execution did not occur.
                                        </Alert>
                                    </StackItem>}
                                {diskGuard !== null && !busy &&
                                    <StackItem>
                                        <Button isDisabled={!connection.administrative} onClick={inspect}>
                                            Inspect captured configuration
                                        </Button>
                                    </StackItem>}
                                {state.inspection && inspectionFresh &&
                                    <StackItem>
                                        <p>Captured candidate: {state.inspection.candidate}. Installed base: {state.inspection.installedBase}.
                                            Installed candidate: {state.inspection.installedCandidate}. Backup base: {state.inspection.backupBase}.
                                        </p>
                                        {stagedMatches && state.uncertainty !== 'install' &&
                                            <Button
isDisabled={busy || state.previewUncertain || state.guardRevision !== state.draftRevision}
                                                onClick={() => check(true)}
                                            >Revalidate captured candidate
                                            </Button>}
                                        {installedMatches && unconfirmed && state.proposal &&
                                            <Button isDisabled={busy} onClick={confirm}>Confirm captured installation</Button>}
                                        {state.confirmed && installedMatches && unconfirmed &&
                                            <Button isDisabled={busy || !authorityFresh} onClick={acknowledge}>Acknowledge confirmed installation</Button>}
                                    </StackItem>}
                                {state.previewUncertain &&
                                    <StackItem>
                                        <Alert variant="warning" isInline title="Sizing observation is uncertain">
                                            Preserve its original operation handles and observe that operation before another sizing submission.
                                        </Alert>
                                    </StackItem>}
                                {state.previewKey &&
                                    <StackItem>
                                        <RecoveryHandles
evidence={{ idempotencyKey: state.previewKey, workMayContinue: state.previewUncertain }}
                                            expectedClientScope={state.authority?.authorityFingerprint}
                                        />
                                    </StackItem>}
                                {state.evidence.length > 0 &&
                                    <StackItem>
                                        <p aria-label="Configuration stage evidence">
                                            {state.evidence.map(event => `${event.stage}: ${event.status}`).join('; ')}
                                        </p>
                                    </StackItem>}
                                {unconfirmed &&
                                    <StackItem>
                                        <Alert variant="warning" isInline title={UNCONFIRMED_INSTALLATION}>
                                            Retain the original cause below. Inspect, explicitly confirm the captured installation,
                                            and acknowledge its exact bytes before starting a fresh preparation.
                                        </Alert>
                                    </StackItem>}
                                {validation !== null && (validation.exit_code !== 0 || phase === 'done') &&
                                    <StackItem><EnvelopeAlert envelope={validation} /></StackItem>}
                                {preparation?.assessment?.syntaxValid &&
                                    <StackItem>
                                        <Alert variant="info" isInline title="Candidate configuration syntax is valid" />
                                    </StackItem>}
                                {preparation?.blocked === 'authority' &&
                                    <StackItem>
                                        <Alert variant="warning" isInline title="Candidate cannot be previewed or installed through this API authority">
                                            {preparation.assessment!.mismatches.length > 0 &&
                                                <p>Changed authority fields: {preparation.assessment!.mismatches.join(', ')}.</p>}
                                            {MANUAL_AUTHORITY_GUIDANCE}
                                        </Alert>
                                    </StackItem>}
                                {phase === 'ready' && validation !== null &&
                                    <StackItem>
                                        <Alert
                                            variant="info"
                                            isInline
                                            title="Candidate validated. Installing keeps one predecessor at config.toml.bak, then renames atomically (CP-11)."
                                        />
                                    </StackItem>}
                                {plan !== null &&
                                    <StackItem>
                                        {plan.exit_code !== 0 && <EnvelopeAlert envelope={plan} />}
                                        {plan.exit_code === 0 && preparation?.plan === plan && <PlanPreview envelope={plan} />}
                                    </StackItem>}
                                {phase === 'done' &&
                                    <StackItem>
                                        <Alert
                                            variant="success"
                                            isInline
                                            title={`Installed and re-validated. Configuration fingerprint: ${fingerprint}`}
                                        >
                                            Future admissions use the installed policy. Existing operations retain their admitted
                                            policy; queued mutations reject stale policy before work begins.
                                        </Alert>
                                    </StackItem>}
                            </Stack>
                        </CardBody>
                    </Card>
                </StackItem>}
        </Stack>
    );
};
