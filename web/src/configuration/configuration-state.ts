/** ADR153/154: one RAM draft, exact original previews and read-only effect recovery. */
import type {
    SessionController,
    ConfigurationOutcomeObservation,
} from "../state/session-controller";
import type { ObservationSnapshot } from "../state/operation-observation";
import type { QueryHandle } from "../state/query-state";
import type { ReadResult } from "../api/types";
import type {
    ConfigRead,
    EmptyPayload,
    ManagedValidation,
    ManagedAssessment,
    RepositoryConfig,
} from "../wire/generated";
import {
    decodeManagedAssessment,
    decodeConfigApplicationOutcome,
} from "../wire/generated";
import { parseWireJson, WireError } from "../wire/json";
import {
    prepareDraft,
    prepareDraftJson,
    upsertRepository,
    removeRepository,
    ConfigurationDraftError,
} from "./draft";
import type { PreparedDraft } from "./draft";
import { MAX_DRAFT_BYTES } from "./draft";
import { encodedBytes } from "../state/retention-budget";

type ConfigResult = ReadResult<ConfigRead, EmptyPayload>;
type ValidationResult = ReadResult<ManagedValidation, EmptyPayload>;
export interface ConfigurationIntent {
    readonly repositoryType: "model" | "dataset";
    readonly repositoryId: string;
    readonly historical: boolean;
}
export interface ReloadReview {
    readonly generation: number;
    readonly authGeneration: number;
}
export interface ConfigurationSnapshot {
    readonly phase: "idle" | "loading" | "ready" | "unavailable";
    readonly generation: number;
    readonly authGeneration: number;
    readonly editorRevision: number;
    readonly base: ConfigRead | null;
    readonly prepared: PreparedDraft | null;
    readonly dirty: boolean;
    readonly editing: boolean;
    readonly pending:
        | "read"
        | "validation"
        | "preview"
        | "apply"
        | "outcome"
        | "compare"
        | null;
    readonly readResult: ConfigResult | null;
    readonly validation: ValidationResult | null;
    readonly previewRecordId: string | null;
    readonly previewObservation: ObservationSnapshot | null;
    readonly assessment: ManagedAssessment | null;
    readonly applicationRecordId: string | null;
    readonly applicationObservation: ObservationSnapshot | null;
    readonly outcome: ConfigurationOutcomeObservation | null;
    readonly outcomeRecordId: string | null;
    readonly comparison: ConfigRead | null;
    readonly notice: string | null;
    readonly canRead: boolean;
    readonly canEdit: boolean;
    readonly canValidate: boolean;
    readonly canPreview: boolean;
    readonly canApply: boolean;
    readonly intent: ConfigurationIntent | null;
}
export function createConfigurationStore(controller: SessionController) {
    let session = controller.snapshot();
    let authGeneration = session.generation;
    let generation = 0;
    let editorRevision = 0;
    let reloadReview: ReloadReview | null = null;
    let disposed = false;
    let base: ConfigRead | null = null;
    let prepared: PreparedDraft | null = null;
    let editing = false;
    let editBuffer: unknown = null;
    let phase: ConfigurationSnapshot["phase"] = "idle";
    let pending: ConfigurationSnapshot["pending"] = null;
    let notice: string | null = null;
    let readResult: ConfigResult | null = null;
    let validation: ValidationResult | null = null;
    let validatedGeneration = -1;
    let previewRecordId: string | null = null;
    let previewObservation: ObservationSnapshot | null = null;
    let previewGeneration = -1;
    let assessment: ManagedAssessment | null = null;
    let applicationRecordId: string | null = null;
    let applicationObservation: ObservationSnapshot | null = null;
    let applicationExpected:
        { baseRevision: string; candidateRevision: string } | undefined;
    let applicationDraftGeneration = -1;
    let outcome: ConfigurationOutcomeObservation | null = null;
    let outcomeRecordId: string | null = null;
    let comparison: ConfigRead | null = null;
    let intent: ConfigurationIntent | null = null;
    let readHandle: QueryHandle<ConfigRead, EmptyPayload> | null = null;
    let compareHandle: QueryHandle<ConfigRead, EmptyPayload> | null = null;
    let unsubscribeRead = () => {};
    let unsubscribeCompare = () => {};
    let unsubscribePreview = () => {};
    let unsubscribeApplication = () => {};
    let abort: AbortController | null = null;
    let slot = controller.createPrivateSlot();
    const listeners = new Set<() => void>();
    let snapshot: ConfigurationSnapshot;
    const permitted = (capability: "config-read" | "config-write") =>
        !disposed &&
        session.connection === "connected" &&
        session.bootstrap.user.admin_permissions.some(
            (permission) =>
                permission.capability === capability && permission.effective,
        );
    function publish(final = false) {
        if (disposed && !final) return;
        const canRead = permitted("config-read");
        const canEdit =
            canRead &&
            permitted("config-write") &&
            base !== null &&
            pending !== "read";
        const available =
            canEdit && pending === null && !editing && prepared !== null;
        snapshot = Object.freeze({
            phase,
            generation,
            authGeneration,
            editorRevision,
            base,
            prepared,
            dirty: editing || prepared?.dirty === true,
            editing,
            pending,
            readResult,
            validation,
            previewRecordId,
            previewObservation,
            assessment,
            applicationRecordId,
            applicationObservation,
            outcome,
            outcomeRecordId,
            comparison,
            notice,
            canRead,
            canEdit,
            canValidate: available,
            canPreview:
                available &&
                session.canSubmit &&
                validatedGeneration === generation &&
                validation?.kind === "success",
            canApply:
                available &&
                session.canSubmit &&
                previewGeneration === generation &&
                assessment !== null,
            intent,
        });
        for (const listener of listeners) {
            try {
                listener();
            } catch {
                /* A detached view cannot strand owned work. */
            }
        }
    }
    function retain() {
        if (
            !slot.set({
                base,
                prepared,
                editBuffer,
                readResult,
                validation,
                assessment,
                outcome,
                comparison,
            })
        ) {
            notice =
                "Browser draft capacity is unavailable. Preserve original operation handles and reload the configuration explicitly.";
            validation = null;
            assessment = null;
            validatedGeneration = previewGeneration = -1;
            return false;
        }
        return true;
    }
    function retireReadiness(preserveComparison = false) {
        generation++;
        reloadReview = null;
        abort?.abort();
        abort = null;
        validation = null;
        assessment = null;
        validatedGeneration = previewGeneration = -1;
        if (!preserveComparison) comparison = null;
        // Accepted operations are retained above the route and never cancelled.
        if (pending !== "apply" && pending !== "outcome") pending = null;
    }
    function clearPrivate() {
        retireReadiness();
        editorRevision++;
        unsubscribeRead();
        unsubscribeCompare();
        unsubscribePreview();
        unsubscribeApplication();
        readHandle?.invalidate();
        compareHandle?.invalidate();
        readHandle = compareHandle = null;
        base = null;
        prepared = null;
        readResult = null;
        previewObservation = applicationObservation = null;
        previewRecordId = applicationRecordId = null;
        applicationExpected = undefined;
        outcome = null;
        outcomeRecordId = null;
        comparison = null;
        editBuffer = null;
        editing = false;
        pending = null;
        intent = null;
        slot.clear();
    }
    function failure(error: unknown) {
        notice =
            error instanceof ConfigurationDraftError
                ? `Draft refused (${error.reason}) at ${error.field}.`
                : error instanceof WireError
                  ? "The response or draft does not match the required configuration proof. No Apply is ready."
                  : "Configuration observation is unavailable. Preserve original operation handles; no submission was retried.";
    }
    function currentAuthority(expected: number) {
        return !disposed && expected === authGeneration;
    }
    function readQuery() {
        const api = controller.apiReads;
        return controller.queries.query(
            { routeId: "config_read_default" },
            (options) => api.readConfiguration(options),
        );
    }
    async function load(replaceDraft = false): Promise<void> {
        if (
            !permitted("config-read") ||
            pending !== null ||
            (snapshot.dirty && !replaceDraft)
        ) {
            notice =
                snapshot.dirty && !replaceDraft
                    ? "Review the unsaved draft decision explicitly before reloading."
                    : "Configuration read permission or connection is unavailable.";
            publish();
            return;
        }
        retireReadiness();
        const ownGeneration = generation;
        unsubscribeRead();
        readHandle?.invalidate();
        const original = { base, prepared, editing, editBuffer };
        let detachRead = () => {};
        readResult = null;
        pending = "read";
        phase = base === null ? "loading" : "ready";
        notice = null;
        retain();
        publish();
        try {
            const handle = readQuery();
            readHandle = handle;
            detachRead = handle.subscribe(() => {
                publish();
            });
            unsubscribeRead = detachRead;
            await handle.refresh();
            if (
                disposed ||
                ownGeneration !== generation ||
                authGeneration !== controller.snapshot().generation
            )
                return;
            const result = handle.snapshot().result;
            if (result?.kind === "success") {
                if (
                    result.payload.archive_id !==
                    session.bootstrap.configured_archive_id
                )
                    throw new WireError("semantic");
                const next = prepareDraft(
                    result.payload,
                    result.payload.editable,
                );
                base = result.payload;
                prepared = next;
                editing = false;
                editBuffer = null;
                readResult = result;
                if (!retain()) {
                    ({ base, prepared, editing, editBuffer } = original);
                    readResult = null;
                    notice =
                        "Configuration reload failed because browser draft capacity is unavailable. The original draft, base and form values are preserved; return to editing.";
                } else editorRevision++;
                phase = base === null ? "unavailable" : "ready";
            } else {
                readResult = result;
                phase = base === null ? "unavailable" : "ready";
                notice =
                    "Configuration reload failed. The original draft, base and form values are preserved; return to editing or reload explicitly.";
                if (!retain()) {
                    readResult = null;
                }
            }
        } catch (error) {
            if (disposed || ownGeneration !== generation) return;
            failure(error);
            notice =
                "Configuration reload failed. " +
                (notice ?? "") +
                (base === null
                    ? ""
                    : " The original draft, base and form values are preserved; return to editing.");
            phase = base === null ? "unavailable" : "ready";
        } finally {
            detachRead();
            if (ownGeneration === generation) {
                pending = null;
                publish();
            }
        }
    }
    function replace(next: PreparedDraft) {
        const old = prepared;
        const oldEditing = editing;
        const oldBuffer = editBuffer;
        retireReadiness();
        prepared = next;
        editing = false;
        editBuffer = null;
        notice = null;
        if (!retain()) {
            prepared = old;
            editing = oldEditing;
            editBuffer = oldBuffer;
            publish();
            return false;
        }
        publish();
        return true;
    }
    function editAllowed() {
        if (
            !permitted("config-read") ||
            !permitted("config-write") ||
            base === null ||
            prepared === null
        )
            throw new Error("configuration-unavailable");
    }
    function originalPreviewChanged(recordId: string, ownGeneration: number) {
        if (
            disposed ||
            ownGeneration !== generation ||
            previewRecordId !== recordId
        )
            return;
        previewObservation = controller.observer.snapshot(recordId);
        const result = previewObservation.result;
        const receipt = previewObservation.receipt;
        if (
            result?.kind === "success" &&
            receipt?.state === "succeeded" &&
            result.response.envelope.exit_code === 0 &&
            base !== null &&
            prepared !== null &&
            validation?.kind === "success"
        ) {
            try {
                const assessed = decodeManagedAssessment(
                    parseWireJson(JSON.stringify(result.payload)),
                );
                if (
                    !assessed.complete ||
                    assessed.archive_id !== base.archive_id ||
                    assessed.base_revision !== prepared.managed.base_revision ||
                    assessed.candidate_revision !==
                        validation.payload.candidate_revision ||
                    JSON.stringify(assessed.required_selectors) !==
                        JSON.stringify(validation.payload.required_selectors)
                )
                    throw new WireError("semantic");
                assessment = assessed;
                previewGeneration = ownGeneration;
                retain();
            } catch (error) {
                assessment = null;
                previewGeneration = -1;
                failure(error);
            }
        }
        publish();
    }
    function originalApplicationChanged(recordId: string, ownAuth: number) {
        if (
            disposed ||
            ownAuth !== authGeneration ||
            applicationRecordId !== recordId
        )
            return;
        applicationObservation = controller.observer.snapshot(recordId);
        publish();
    }
    const unsubscribeSession = controller.subscribe(() => {
        const next = controller.snapshot();
        if (
            next.generation !== authGeneration ||
            next.connection !== "connected"
        ) {
            clearPrivate();
            authGeneration = next.generation;
            slot = controller.createPrivateSlot();
            phase = "unavailable";
            notice =
                "Authentication or connection changed. The private draft was cleared; original operation handles remain in Operations.";
        }
        session = next;
        publish();
    });
    publish();
    return Object.freeze({
        snapshot: () => snapshot,
        subscribe(listener: () => void) {
            listeners.add(listener);
            return () => {
                listeners.delete(listener);
            };
        },
        load: () => load(),
        reviewReload(): ReloadReview | null {
            if (!snapshot.canRead || pending !== null || !snapshot.dirty)
                return null;
            reloadReview = Object.freeze({ generation, authGeneration });
            return reloadReview;
        },
        cancelReload(review: ReloadReview) {
            if (reloadReview === review) reloadReview = null;
        },
        async reload(review?: ReloadReview) {
            if (
                review !== undefined &&
                (review !== reloadReview ||
                    review.generation !== generation ||
                    review.authGeneration !== authGeneration)
            )
                return;
            if (snapshot.dirty && review === undefined) return;
            await load(true);
        },
        async compare() {
            if (!snapshot.canRead || pending !== null) return;
            const ownGeneration = generation;
            unsubscribeCompare();
            compareHandle?.invalidate();
            pending = "compare";
            publish();
            try {
                compareHandle = readQuery();
                const handle = compareHandle;
                unsubscribeCompare = handle.subscribe(() => {
                    publish();
                });
                await handle.refresh();
                if (ownGeneration !== generation || disposed) return;
                const result = handle.snapshot().result;
                if (result?.kind === "success") {
                    if (
                        result.payload.archive_id !==
                        session.bootstrap.configured_archive_id
                    )
                        throw new WireError("semantic");
                    if (
                        base !== null &&
                        result.payload.base_revision !== base.base_revision
                    ) {
                        retireReadiness(true);
                        notice =
                            "Installed configuration changed. The original draft and base are preserved; reload and re-edit explicitly. Validation and Apply readiness were retired.";
                    }
                    const previous = comparison;
                    comparison = result.payload;
                    if (!retain()) comparison = previous;
                    publish();
                } else {
                    notice =
                        "The installed configuration could not be compared. The original draft base is preserved.";
                }
            } catch (error) {
                failure(error);
            } finally {
                unsubscribeCompare();
                if (ownGeneration === generation) {
                    pending = null;
                    publish();
                }
            }
        },
        discard() {
            if (pending === "read") {
                unsubscribeRead();
                readHandle?.invalidate();
            }
            retireReadiness();
            editing = false;
            editBuffer = null;
            notice = null;
            prepared = base === null ? null : prepareDraft(base, base.editable);
            retain();
            publish();
        },
        replaceEditable(input: unknown) {
            if (pending === "read") return false;
            try {
                editAllowed();
                if (base !== null) return replace(prepareDraft(base, input));
            } catch (error) {
                retireReadiness();
                failure(error);
                publish();
            }
            return false;
        },
        replaceJson(text: string) {
            if (pending === "read") return false;
            try {
                editAllowed();
                if (base !== null) return replace(prepareDraftJson(base, text));
            } catch (error) {
                retireReadiness();
                failure(error);
                publish();
            }
            return false;
        },
        upsert(entry: RepositoryConfig) {
            if (pending === "read") return false;
            try {
                editAllowed();
                if (base !== null && prepared !== null)
                    return replace(
                        prepareDraft(
                            base,
                            upsertRepository(prepared.editable, entry),
                        ),
                    );
            } catch (error) {
                retireReadiness();
                failure(error);
                publish();
            }
            return false;
        },
        remove(type: "model" | "dataset", id: string) {
            if (pending === "read") return false;
            try {
                editAllowed();
                if (base !== null && prepared !== null)
                    return replace(
                        prepareDraft(
                            base,
                            removeRepository(prepared.editable, type, id),
                        ),
                    );
            } catch (error) {
                retireReadiness();
                failure(error);
                publish();
            }
            return false;
        },
        setEditing(value: boolean, buffer?: unknown) {
            if (pending === "read") return false;
            const previous = editBuffer;
            retireReadiness();
            editing = value;
            try {
                const next = value ? (buffer ?? null) : null;
                if (encodedBytes(next) > MAX_DRAFT_BYTES)
                    throw new Error("draft-buffer-limit");
                editBuffer = next;
                if (!retain()) {
                    editBuffer = previous;
                    publish();
                    return false;
                }
            } catch {
                editBuffer = previous;
                notice =
                    "The editable input exceeds the finite browser draft capacity. Its last admitted value is preserved.";
                publish();
                return false;
            }
            publish();
            return true;
        },
        async validate() {
            if (!snapshot.canValidate || prepared === null || base === null)
                return;
            retireReadiness();
            const ownGeneration = generation;
            const original = prepared;
            const originalBase = base;
            const signal = new AbortController();
            abort = signal;
            pending = "validation";
            notice = null;
            publish();
            try {
                const result = await controller.validateConfiguration(
                    { managed: original.managed },
                    { signal: signal.signal },
                );
                if (disposed || ownGeneration !== generation) return;
                if (
                    result.kind === "success" &&
                    (result.payload.archive_id !== originalBase.archive_id ||
                        result.payload.base_revision !==
                            original.managed.base_revision)
                )
                    throw new WireError("semantic");
                validation = result;
                if (result.kind === "success")
                    validatedGeneration = ownGeneration;
                retain();
            } catch (error) {
                if (ownGeneration === generation) failure(error);
            } finally {
                if (ownGeneration === generation) {
                    pending = null;
                    abort = null;
                    publish();
                }
            }
        },
        async preview() {
            if (!snapshot.canPreview || prepared === null) return;
            const ownGeneration = generation;
            pending = "preview";
            notice = null;
            publish();
            try {
                const submitted = await controller.submit({
                    action: "managedPlan",
                    request: { managed: prepared.managed },
                });
                if (disposed || ownGeneration !== generation) return;
                previewRecordId = submitted.recordId;
                unsubscribePreview();
                unsubscribePreview = controller.observer.subscribe(
                    submitted.recordId,
                    () => {
                        originalPreviewChanged(
                            submitted.recordId,
                            ownGeneration,
                        );
                    },
                );
                originalPreviewChanged(submitted.recordId, ownGeneration);
                if (submitted.result.kind !== "accepted")
                    notice =
                        "Preview admission is not confirmed. Preserve its original handle and observe it in Operations; do not resubmit to discover the outcome.";
            } catch (error) {
                if (ownGeneration === generation) failure(error);
            } finally {
                if (ownGeneration === generation) {
                    pending = null;
                    publish();
                }
            }
        },
        async apply() {
            if (
                !snapshot.canApply ||
                prepared === null ||
                assessment === null ||
                previewRecordId === null
            )
                return;
            const preview = session.registry.records.find(
                (row) => row.recordId === previewRecordId,
            );
            if (
                preview?.handles.kind !== "basic-key" ||
                preview.handles.operationId === null
            )
                return;
            const managed = prepared.managed;
            const expected = {
                baseRevision: assessment.base_revision,
                candidateRevision: assessment.candidate_revision,
            };
            const ownAuth = authGeneration;
            applicationDraftGeneration = generation;
            pending = "apply";
            notice = null;
            assessment = null;
            previewGeneration = -1;
            publish();
            try {
                const submitted = await controller.submit({
                    action: "configurationApplication",
                    request: {
                        managed,
                        preview: {
                            operation_id: preview.handles.operationId,
                            key: preview.handles.key,
                        },
                    },
                });
                if (disposed || ownAuth !== authGeneration) return;
                applicationRecordId = submitted.recordId;
                applicationExpected = expected;
                outcome = null;
                unsubscribeApplication();
                unsubscribeApplication = controller.observer.subscribe(
                    submitted.recordId,
                    () => {
                        originalApplicationChanged(submitted.recordId, ownAuth);
                    },
                );
                originalApplicationChanged(submitted.recordId, ownAuth);
                notice =
                    "Application admission is not installed success. Observe the original application outcome; no replacement submission will be made.";
            } catch (error) {
                if (ownAuth === authGeneration) failure(error);
            } finally {
                if (ownAuth === authGeneration) {
                    pending = null;
                    publish();
                }
            }
        },
        async observeOutcome(recordId = applicationRecordId) {
            if (!snapshot.canRead || pending !== null || recordId === null)
                return;
            const ownAuth = authGeneration;
            pending = "outcome";
            outcomeRecordId = recordId;
            outcome = null;
            retain();
            notice = null;
            publish();
            try {
                const result = await controller.observeConfigurationOutcome(
                    recordId,
                    recordId === applicationRecordId
                        ? applicationExpected
                        : undefined,
                );
                if (disposed || ownAuth !== authGeneration) return;
                const previous = outcome;
                outcome = result;
                if (!retain()) {
                    outcome = previous;
                    return;
                }
                if (
                    result.kind === "outcome" &&
                    result.result.kind === "success"
                ) {
                    const actual = decodeConfigApplicationOutcome(
                        parseWireJson(JSON.stringify(result.result.payload)),
                    );
                    if (!actual.pending && actual.state === "confirmed") {
                        if (
                            !snapshot.dirty ||
                            (recordId === applicationRecordId &&
                                generation === applicationDraftGeneration &&
                                !editing)
                        ) {
                            pending = null;
                            await load(true);
                            if (!currentAuthority(ownAuth)) return;
                            notice =
                                "Installed configuration confirmed. Fresh editable settings were requested; the original API receipt remains independent.";
                        } else {
                            notice =
                                "Installed configuration confirmed. Your newer draft is preserved against its original base; compare and reload explicitly before re-editing.";
                        }
                    } else if (
                        !actual.pending &&
                        actual.state === "unchanged"
                    ) {
                        notice =
                            "The original application is known unchanged. This does not confirm installation of the requested edit.";
                    } else {
                        notice =
                            "The original application remains unresolved or blocked. Preserve the original handles and host evidence; do not retry Apply.";
                    }
                }
            } catch (error) {
                if (ownAuth === authGeneration) failure(error);
            } finally {
                if (ownAuth === authGeneration) {
                    pending = null;
                    publish();
                }
            }
        },
        setIntent(next: ConfigurationIntent) {
            intent = Object.freeze({ ...next });
            publish();
        },
        clearIntent() {
            intent = null;
            publish();
        },
        dispose() {
            clearPrivate();
            disposed = true;
            publish(true);
            unsubscribeSession();
            listeners.clear();
        },
    });
}
export type ConfigurationStore = ReturnType<typeof createConfigurationStore>;
