/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The configuration editor (docs/cockpit.md §6, CP-11): two modes, one
 * pipeline. Form mode renders the schema and serializes canonically
 * (comments lost, and it says so); text mode edits the document verbatim.
 * Both go candidate → validate → preview → install → confirm.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';

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
    confirmInstalledCandidate, installCandidate, planCandidate, readInstalledConfig, removeCandidate,
    validateCandidate, writeCandidate,
} from './api/config';
import { EnvelopeAlert, Loading, QueryError, Sha } from './components';
import {
    ConfigDocument, extractFieldPath, FieldSpec, getField, GLOBAL_FIELDS, parseConfig,
    RepositoryEntry, serializeConfig, setField, validateRevisionReference,
    configuredTagSuggestions, normalizeTags, tagInput,
} from './lib/config';
import { CandidateGuard } from './lib/candidate-guard';
import {
    CandidatePreparation, ConfigurationPorts, installConfiguration, MANUAL_AUTHORITY_GUIDANCE,
    prepareConfiguration, UNCONFIRMED_INSTALLATION,
} from './lib/config-pipeline';
import { Envelope } from './lib/envelope';
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
    const revisionError = validateRevisionReference(entry.revision);
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
                            value={entry.revision}
                            validated={revisionError === null ? 'default' : 'error'}
                            onChange={(_event, revision) => onChange({ ...entry, revision })}
                        />
                    </FlexItem>
                    <FlexItem>
                        <Checkbox
                            id={`repo-enabled-${index}`}
                            label="enabled"
                            isChecked={entry.enabled}
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
                    value={entry.declared_dependencies.join(', ')}
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

type Phase = 'idle' | 'checking' | 'ready' | 'installing' | 'done';

export const Configuration = () => {
    const [installedText, setInstalledText] = useState<string | null>(null);
    const [loadError, setLoadError] = useState<Error | null>(null);
    const [mode, setMode] = useState<'form' | 'text'>('form');
    const [document, setDocument] = useState<ConfigDocument | null>(null);
    const [text, setText] = useState('');
    const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
    const [phase, setPhase] = useState<Phase>('idle');
    const [validation, setValidation] = useState<Envelope | null>(null);
    const [plan, setPlan] = useState<Envelope | null>(null);
    const [fingerprint, setFingerprint] = useState<string | null>(null);
    const [pipelineError, setPipelineError] = useState<Error | null>(null);
    const [preparation, setPreparation] = useState<CandidatePreparation | null>(null);
    const [diskGuard, setDiskGuard] = useState<CandidateGuard | null>(null);
    const [unconfirmed, setUnconfirmed] = useState(false);
    const revision = useRef(0);

    const load = useCallback(() => {
        setLoadError(null);
        readInstalledConfig()
                .then(content => {
                    setUnconfirmed(false);
                    setInstalledText(content);
                    setText(content);
                    try {
                        const parsed = parseConfig(content);
                        setDocument(parsed);
                    } catch (failure) {
                        setDocument(null);
                        setMode('text');
                        setLoadError(new Error(`installed configuration does not parse: ${String(failure)}`));
                    }
                }, failure => setLoadError(failure as Error));
    }, []);

    useEffect(load, [load]);

    const candidateContent = (): string => {
        if (mode === 'text')
            return text;
        return serializeConfig(document ?? {}, new Date());
    };

    const invalidate = () => {
        revision.current += 1;
        setPhase('idle');
        setPreparation(null);
        setValidation(null);
        setPlan(null);
        setFingerprint(null);
        setFieldErrors({});
        setPipelineError(null);
    };

    const editDocument = (value: ConfigDocument) => {
        if (phase !== 'installing') {
            invalidate();
            setDocument(value);
        }
    };

    const ports: ConfigurationPorts = {
        write: writeCandidate,
        validate: validateCandidate,
        preview: planCandidate,
        install: installCandidate,
        confirm: confirmInstalledCandidate,
    };

    const check = () => {
        if (installedText === null || unconfirmed)
            return;
        revision.current += 1;
        const capturedRevision = revision.current;
        setPhase('checking');
        setPreparation(null);
        setValidation(null);
        setPlan(null);
        setFingerprint(null);
        setPipelineError(null);
        setFieldErrors({});
        const flow = async () => {
            const guard = { candidateContent: candidateContent(), installedContent: installedText };
            const prepared = await prepareConfiguration(guard, {
                ...ports,
                write: async expected => {
                    await writeCandidate(expected);
                    if (revision.current === capturedRevision)
                        setDiskGuard(expected);
                },
            }, () => revision.current === capturedRevision);
            if (revision.current !== capturedRevision)
                return;
            setPreparation(prepared);
            setValidation(prepared.validation);
            setPlan(prepared.plan);
            const errors: FieldErrors = {};
            for (const issue of prepared.validation.errors) {
                const path = extractFieldPath(issue);
                if (path !== null)
                    errors[path] = issue.message;
            }
            setFieldErrors(errors);
            setPhase(prepared.proposal === null ? 'idle' : 'ready');
        };
        flow().catch(failure => {
            if (revision.current === capturedRevision) {
                setPipelineError(failure as Error);
                setPhase('idle');
            }
        });
    };

    const install = () => {
        const proposal = preparation?.proposal;
        if (proposal === undefined || proposal === null || phase !== 'ready')
            return;
        setPhase('installing');
        setPipelineError(null);
        const flow = async () => {
            const confirmed = await installConfiguration(proposal, ports);
            setFingerprint(confirmed.fingerprint);
            setValidation(confirmed.envelope);
            setDiskGuard(null);
            setPreparation(null);
            setPhase('done');
            load();
        };
        flow().catch(failure => {
            setPreparation(null);
            setValidation(null);
            setPlan(null);
            setDiskGuard(null);
            setUnconfirmed(true);
            setPipelineError(failure as Error);
            setPhase('idle');
        });
    };

    const cancel = () => {
        if (diskGuard === null || phase === 'installing')
            return;
        revision.current += 1;
        removeCandidate(diskGuard).then(() => {
            setDiskGuard(null);
            invalidate();
        }, failure => {
            invalidate();
            setPipelineError(failure as Error);
        });
    };

    return (
        <Stack hasGutter>
            {loadError !== null && <StackItem><QueryError error={loadError} /></StackItem>}
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
                                            isDisabled={phase === 'installing'}
                                            onChange={() => {
                                                if (phase !== 'installing' && mode !== 'form') {
                                                    try {
                                                        const parsed = parseConfig(text);
                                                        invalidate();
                                                        setDocument(parsed);
                                                        setMode('form');
                                                    } catch {
                                                        setPipelineError(new Error('Fix the text document before switching to form mode'));
                                                    }
                                                }
                                            }}
                                        />
                                        <ToggleGroupItem
                                            text="Text (verbatim)"
                                            isSelected={mode === 'text'}
                                            isDisabled={phase === 'installing'}
                                            onChange={() => {
                                                if (mode === 'text')
                                                    return;
                                                try {
                                                    const content = serializeConfig(document ?? {}, new Date());
                                                    invalidate();
                                                    setText(content);
                                                    setMode('text');
                                                } catch {
                                                    setPipelineError(new Error('Fix invalid tags before switching to text mode'));
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
                                            isDisabled={phase === 'installing'}
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
                                                isDisabled={phase === 'checking' || phase === 'installing' || unconfirmed}
                                                onClick={check}
                                            >
                                                Validate candidate
                                            </Button>
                                        </FlexItem>
                                        {phase === 'ready' && preparation?.proposal != null &&
                                            <FlexItem>
                                                <Button variant="danger" onClick={install}>
                                                    Install validated candidate
                                                </Button>
                                            </FlexItem>}
                                        {diskGuard !== null && phase !== 'installing' && phase !== 'checking' &&
                                            <FlexItem>
                                                <Button variant="link" onClick={cancel}>Discard candidate</Button>
                                            </FlexItem>}
                                        {(phase === 'checking' || phase === 'installing') &&
                                            <FlexItem><Loading /></FlexItem>}
                                    </Flex>
                                </StackItem>
                                {pipelineError !== null &&
                                    <StackItem><QueryError error={pipelineError} /></StackItem>}
                                {unconfirmed &&
                                    <StackItem>
                                        <Alert variant="warning" isInline title={UNCONFIRMED_INSTALLATION}>
                                            <Button variant="link" onClick={() => { invalidate(); load() }}>
                                                Reload installed configuration
                                            </Button>
                                        </Alert>
                                    </StackItem>}
                                {validation !== null && (validation.exit_code !== 0 || phase === 'done') &&
                                    <StackItem><EnvelopeAlert envelope={validation} /></StackItem>}
                                {preparation?.assessment.syntaxValid &&
                                    <StackItem>
                                        <Alert variant="info" isInline title="Candidate configuration syntax is valid" />
                                    </StackItem>}
                                {preparation?.blocked === 'authority' &&
                                    <StackItem>
                                        <Alert variant="warning" isInline title="Candidate cannot be previewed or installed through this API authority">
                                            {preparation.assessment.mismatches.length > 0 &&
                                                <p>Changed authority fields: {preparation.assessment.mismatches.join(', ')}.</p>}
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
                                        {plan.exit_code === 0 && <PlanPreview envelope={plan} />}
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
