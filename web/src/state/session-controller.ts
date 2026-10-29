/** One authenticated application session, above routes; submissions are never replayed. */
import { ApiClient } from "../api/client";
import type {
    ReadApiClient,
    SubmissionOptions,
    SubmissionResult,
} from "../api/client";
import {
    bootstrapScope,
    releaseChanged,
    InterfaceUpdateRequiredError,
} from "../bootstrap";
import {
    decodeConfigApplicationOutcome,
    decodeScheduleChangeOutcome,
    decodeObserverStopOutcome,
} from "../wire/generated";
import type {
    ClientOperation,
    UiBootstrap,
    RequestManagedValidationRequest,
    RequestScheduleValidationRequest,
} from "../wire/generated";
import type { ReadOptions } from "../api/types";
import { parseWireJson, WireError } from "../wire/json";
import { createAuthSession, sameAuthSession } from "./authority";
import type { AuthorizedObservation, RecordId } from "./authority";
import {
    createOperationRegistry,
    OperationRegistryError,
} from "./operation-registry";
import type {
    Action,
    ManualImport,
    OperationStorage,
    RecoveryRecord,
    RegistrySnapshot,
    SafeTerminalSummary,
} from "./operation-registry";
import { createOperationObserver } from "./operation-observation";
import type { OriginalResultRead, PauseReason } from "./operation-observation";
import { createQueryStore } from "./query-state";
import {
    createReadCoordinator,
    createRetentionBudget,
    encodedBytes,
    READ_RESERVATION_BYTES,
    SESSION_RESPONSE_BYTES,
    StateCapacityError,
} from "./retention-budget";
import { createCrossTabAdvice } from "./cross-tab";

type SubmissionMethods = {
    [K in Action]: `submit${Capitalize<K>}`;
};
export type SubmissionIntent = {
    [K in Action]: {
        readonly action: K;
        readonly request: Parameters<ApiClient[SubmissionMethods[K]]>[0];
    };
}[Action];

function dispatch(
    client: ApiClient,
    intent: SubmissionIntent,
    options: SubmissionOptions,
): Promise<SubmissionResult> {
    switch (intent.action) {
        case "sync":
            return client.submitSync(intent.request, options);
        case "installedPlan":
            return client.submitInstalledPlan(intent.request, options);
        case "candidatePlan":
            return client.submitCandidatePlan(intent.request, options);
        case "managedPlan":
            return client.submitManagedPlan(intent.request, options);
        case "configurationApplication":
            return client.submitConfigurationApplication(
                intent.request,
                options,
            );
        case "scheduleChange":
            return client.submitScheduleChange(intent.request, options);
        case "observerStop":
            return client.submitObserverStop(intent.request, options);
        case "readOnlyDiagnostics":
            return client.submitReadOnlyDiagnostics(intent.request, options);
        case "probeDiagnostics":
            return client.submitProbeDiagnostics(intent.request, options);
        case "newVerification":
            return client.submitNewVerification(intent.request, options);
        case "fullVerification":
            return client.submitFullVerification(intent.request, options);
        case "revisionVerification":
            return client.submitRevisionVerification(intent.request, options);
        case "prunePreview":
            return client.submitPrunePreview(intent.request, options);
        case "pruneApply":
            return client.submitPruneApply(intent.request, options);
        case "purgePreview":
            return client.submitPurgePreview(intent.request, options);
        case "purgeApply":
            return client.submitPurgeApply(intent.request, options);
        case "recoveryPreview":
            return client.submitRecoveryPreview(intent.request, options);
        case "recoveryApply":
            return client.submitRecoveryApply(intent.request, options);
        case "quarantinePreview":
            return client.submitQuarantinePreview(intent.request, options);
        case "quarantineApply":
            return client.submitQuarantineApply(intent.request, options);
        case "repair":
            return client.submitRepair(intent.request, options);
        case "catalogRefresh":
            return client.submitCatalogRefresh(intent.request, options);
    }
}

export interface SessionSnapshot {
    readonly bootstrap: UiBootstrap;
    readonly generation: number;
    readonly connection:
        "connected" | "disconnected" | "reconnecting" | "update_required";
    readonly registry: RegistrySnapshot;
    readonly pendingSubmission: boolean;
    readonly canSubmit: boolean;
    readonly notice: string | null;
}
export interface SessionControllerOptions {
    readonly bootstrap: UiBootstrap;
    readonly fetcher?: typeof fetch;
    readonly storage: OperationStorage | null;
    /** Production supplies the same bounded, build-verified bootstrap loader used at mount. */
    readonly reconnect: () => Promise<UiBootstrap>;
}
export type ConfigurationOutcomeObservation =
    | {
          readonly kind: "outcome";
          readonly receipt: ClientOperation;
          readonly result: Awaited<
              ReturnType<ApiClient["readConfigurationOutcome"]>
          >;
      }
    | {
          readonly kind: "lookup";
          readonly result: Awaited<ReturnType<ApiClient["lookupOperation"]>>;
      };
export type HostActionOutcomeObservation =
    | {
          readonly kind: "outcome";
          readonly receipt: ClientOperation;
          readonly result:
              | Awaited<ReturnType<ApiClient["readScheduleOutcome"]>>
              | Awaited<ReturnType<ApiClient["readObserverStopOutcome"]>>;
      }
    | {
          readonly kind: "lookup";
          readonly result: Awaited<ReturnType<ApiClient["lookupOperation"]>>;
      };

export function resultCertainty(
    receipt: ClientOperation,
    result: OriginalResultRead,
): "known" | "unknown-effects" {
    if (result.kind !== "success" && result.kind !== "domain_failure")
        return "unknown-effects";
    const decode =
        receipt.route === "/api/v1/config/applications"
            ? decodeConfigApplicationOutcome
            : receipt.route === "/api/v1/host/sync-schedule/changes"
              ? decodeScheduleChangeOutcome
              : receipt.route === "/api/v1/host/sync-observer/stops"
                ? decodeObserverStopOutcome
                : null;
    if (decode === null) return "known";
    let outcome;
    try {
        outcome = decode(parseWireJson(JSON.stringify(result.payload)));
    } catch {
        return "unknown-effects";
    }
    return !outcome.pending &&
        (outcome.state === "confirmed" || outcome.state === "unchanged")
        ? "known"
        : "unknown-effects";
}

export function createSessionController(options: SessionControllerOptions) {
    let bootstrap = options.bootstrap;
    let session = createAuthSession({
        scope: bootstrapScope(bootstrap),
        authGeneration: 1,
    });
    let client = new ApiClient({
        scope: session.scope,
        ...(options.fetcher === undefined ? {} : { fetcher: options.fetcher }),
    });
    let connection: SessionSnapshot["connection"] = "connected";
    let pendingSubmission = false;
    let notice: string | null = null;
    let disposed = false;
    let batching = false;
    let otherTabChanged = false;
    let pageHidden = false;
    let visibilityEpoch = 0;
    const listeners = new Set<() => void>();
    const registry = createOperationRegistry({ storage: options.storage });
    const retention = createRetentionBudget();
    const reads = createReadCoordinator();
    let privateSerial = 0;
    const privateOwners = new Set<string>();
    const controlledReads = new Set<AbortController>();
    const observationReads = new Set<AbortController>();
    let snapshot: SessionSnapshot;
    function publish() {
        if (batching || disposed) return;
        snapshot = Object.freeze({
            bootstrap,
            generation: session.authGeneration,
            connection,
            registry: registry.snapshot(),
            pendingSubmission,
            canSubmit:
                !otherTabChanged &&
                connection === "connected" &&
                !pendingSubmission &&
                registry.canSubmit(session),
            notice,
        });
        for (const listener of listeners) {
            try {
                listener();
            } catch {
                /* A detached view cannot interrupt recovery persistence. */
            }
        }
    }
    const queries = createQueryStore({
        session,
        retention,
        reads,
        onUnauthorized: unauthorized,
    });
    const newHostStatus = () =>
        queries.query({ routeId: "host_status_default" }, (readOptions) =>
            client.hostStatus(readOptions),
        );
    let hostStatus = newHostStatus();
    const observer = createOperationObserver({
        retention,
        reads,
        onUnauthorized: unauthorized,
        onReceipt: (auth, receipt) => {
            if (!current(auth)) return null;
            registry.observed(auth, receipt);
            return registry.authorizeObservation(auth.recordId, session);
        },
        onResult: (auth, receipt, result) => {
            if (!current(auth)) return "unknown-effects";
            const certainty = resultCertainty(receipt, result);
            if (result.kind === "success" || result.kind === "domain_failure") {
                const envelope = result.response.envelope;
                const exitCode = envelope.exit_code;
                if (
                    exitCode !== 0 &&
                    exitCode !== 10 &&
                    exitCode !== 20 &&
                    exitCode !== 30 &&
                    exitCode !== 40 &&
                    exitCode !== 50
                )
                    throw new WireError("semantic");
                const summary: SafeTerminalSummary = {
                    command: envelope.command,
                    exitCode,
                    outcome: envelope.outcome,
                    runId: envelope.run_id,
                    code:
                        envelope.errors[0]?.code ??
                        envelope.warnings[0]?.code ??
                        null,
                };
                registry.resolved(auth, summary, certainty);
                // Tags can change without changing the configuration fingerprint.
                if (
                    certainty === "known" &&
                    receipt.route === "/api/v1/config/applications"
                )
                    queries.invalidate(() => true);
            }
            return certainty;
        },
    });
    function current(auth: AuthorizedObservation) {
        return (
            !disposed &&
            connection === "connected" &&
            sameAuthSession(
                session,
                createAuthSession({
                    scope: auth.target,
                    authGeneration: auth.authGeneration,
                }),
            )
        );
    }
    function currentObservation(
        auth: AuthorizedObservation,
        epoch: number,
        signal: AbortSignal,
    ) {
        return (
            current(auth) &&
            !pageHidden &&
            epoch === visibilityEpoch &&
            !signal.aborted
        );
    }
    function stillReconnecting(generation: number) {
        return (
            !disposed &&
            session.authGeneration === generation &&
            connection === "reconnecting"
        );
    }
    function startObservation(auth: AuthorizedObservation) {
        void observer.observe(auth, client).catch(() => {
            if (current(auth)) registry.unknown(auth.recordId, "unavailable");
        });
    }
    function clearPrivate() {
        batching = true;
        session = createAuthSession({
            scope: session.scope,
            authGeneration: session.authGeneration + 1,
        });
        observer.clearPrivate();
        queries.clearPrivate("authentication");
        for (const controller of controlledReads) controller.abort();
        for (const owner of privateOwners) retention.release(owner);
        privateOwners.clear();
        registry.invalidateObservations();
        batching = false;
    }
    function unauthorized() {
        if (disposed) return;
        connection = "disconnected";
        notice =
            "Authentication or connection changed. Private observations were cleared; original handles are preserved.";
        clearPrivate();
        publish();
    }
    let advice = createCrossTabAdvice({ scope: session.scope });
    function receiveAdvice() {
        otherTabChanged = true;
        notice =
            "Another tab changed recovery history. Copy any memory-only handles, then reload to read the saved history before submitting.";
        publish();
    }
    let unsubscribeAdvice = advice.subscribe(receiveAdvice);
    let previousRecords = registry.snapshot().records;
    const unsubscribeRegistry = registry.subscribe(() => {
        const records = registry.snapshot().records;
        for (const record of records)
            if (
                previousRecords.find(
                    (previous) => previous.recordId === record.recordId,
                ) !== record
            )
                advice.publish(record.recordId);
        for (const record of previousRecords)
            if (!records.some((next) => next.recordId === record.recordId))
                advice.publish(record.recordId);
        previousRecords = records;
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
        queries,
        get apiReads(): ReadApiClient {
            return client;
        },
        get hostStatus() {
            return hostStatus;
        },
        /** RAM-only draft copies share the query/observer encoded retention budget. */
        createPrivateSlot() {
            const owner = "private-state:" + String(++privateSerial);
            const generation = session.authGeneration;
            return Object.freeze({
                set(value: unknown): boolean {
                    if (
                        disposed ||
                        connection !== "connected" ||
                        generation !== session.authGeneration
                    )
                        return false;
                    const bytes = encodedBytes(value);
                    if (
                        bytes > SESSION_RESPONSE_BYTES ||
                        !retention.claim(owner, bytes)
                    )
                        return false;
                    privateOwners.add(owner);
                    return true;
                },
                clear() {
                    retention.release(owner);
                    privateOwners.delete(owner);
                },
            });
        },
        async validateConfiguration(
            request: RequestManagedValidationRequest,
            options: ReadOptions = {},
        ) {
            if (
                disposed ||
                connection !== "connected" ||
                !bootstrap.user.admin_permissions.some(
                    (permission) =>
                        permission.capability === "config-write" &&
                        permission.effective,
                )
            )
                throw new OperationRegistryError("scope");
            const generation = session.authGeneration;
            const originalClient = client;
            const controller = new AbortController();
            const abort = () => {
                controller.abort();
            };
            options.signal?.addEventListener("abort", abort, { once: true });
            if (options.signal?.aborted === true) controller.abort();
            controlledReads.add(controller);
            const owner = "managed-validation";
            try {
                return await reads.run(owner, controller.signal, async () => {
                    if (!retention.claim(owner, READ_RESERVATION_BYTES))
                        throw new StateCapacityError();
                    try {
                        const result =
                            await originalClient.validateManagedConfiguration(
                                request,
                                {
                                    signal: controller.signal,
                                    responseByteLimit: SESSION_RESPONSE_BYTES,
                                },
                            );
                        if (
                            generation !== session.authGeneration ||
                            connection !== "connected"
                        )
                            return { kind: "aborted" } as const;
                        if (
                            result.kind === "api_problem" &&
                            result.status === 401
                        )
                            unauthorized();
                        return result;
                    } finally {
                        retention.release(owner);
                    }
                });
            } finally {
                options.signal?.removeEventListener("abort", abort);
                controlledReads.delete(controller);
            }
        },
        async validateSchedule(
            request: RequestScheduleValidationRequest,
            options: ReadOptions = {},
        ) {
            if (
                disposed ||
                connection !== "connected" ||
                !bootstrap.user.admin_permissions.some(
                    (permission) =>
                        permission.capability === "schedule-write" &&
                        permission.effective,
                )
            )
                throw new OperationRegistryError("scope");
            const generation = session.authGeneration;
            const originalClient = client;
            const controller = new AbortController();
            const abort = () => {
                controller.abort();
            };
            options.signal?.addEventListener("abort", abort, { once: true });
            if (options.signal?.aborted === true) controller.abort();
            controlledReads.add(controller);
            const owner = "schedule-validation";
            try {
                return await reads.run(owner, controller.signal, async () => {
                    if (!retention.claim(owner, READ_RESERVATION_BYTES))
                        throw new StateCapacityError();
                    try {
                        const result = await originalClient.validateSchedule(
                            request,
                            {
                                signal: controller.signal,
                                responseByteLimit: SESSION_RESPONSE_BYTES,
                            },
                        );
                        if (
                            disposed ||
                            controller.signal.aborted ||
                            generation !== session.authGeneration ||
                            connection !== "connected"
                        )
                            return { kind: "aborted" } as const;
                        if (
                            result.kind === "api_problem" &&
                            result.status === 401
                        )
                            unauthorized();
                        return result;
                    } finally {
                        retention.release(owner);
                    }
                });
            } finally {
                options.signal?.removeEventListener("abort", abort);
                controlledReads.delete(controller);
            }
        },
        async observeConfigurationOutcome(
            id: RecordId,
            expected?: {
                readonly baseRevision: string;
                readonly candidateRevision: string;
            },
        ): Promise<ConfigurationOutcomeObservation> {
            if (
                disposed ||
                pageHidden ||
                connection !== "connected" ||
                !bootstrap.user.admin_permissions.some(
                    (permission) =>
                        permission.capability === "config-read" &&
                        permission.effective,
                )
            )
                throw new OperationRegistryError("scope");
            const record = registry
                .snapshot()
                .records.find((row) => row.recordId === id);
            if (record?.handles.kind !== "basic-key")
                throw new OperationRegistryError("namespace");
            const originalKey = record.handles.key;
            const originalClient = client;
            const auth = registry.authorizeObservation(id, session, {
                reconnect: true,
            });
            const controller = new AbortController();
            controlledReads.add(controller);
            observationReads.add(controller);
            const observationEpoch = visibilityEpoch;
            const owner = "configuration-outcome:" + id;
            try {
                return await reads.run(owner, controller.signal, async () => {
                    if (!retention.claim(owner, READ_RESERVATION_BYTES))
                        throw new StateCapacityError();
                    try {
                        // Always prove the original subject/key association, also after restore.
                        const lookup = await originalClient.lookupOperation(
                            originalKey,
                            {
                                signal: controller.signal,
                                responseByteLimit: SESSION_RESPONSE_BYTES,
                            },
                        );
                        if (
                            !currentObservation(
                                auth,
                                observationEpoch,
                                controller.signal,
                            )
                        )
                            throw new OperationRegistryError("scope");
                        if (lookup.kind !== "success") {
                            if (
                                lookup.kind === "api_problem" &&
                                lookup.status === 401
                            )
                                unauthorized();
                            return { kind: "lookup", result: lookup };
                        }
                        const receipt = lookup.payload.operation;
                        if (receipt.route !== "/api/v1/config/applications")
                            throw new WireError("semantic");
                        registry.observed(auth, receipt);
                        const proven = registry.authorizeObservation(
                            id,
                            session,
                        );
                        if (
                            !currentObservation(
                                proven,
                                observationEpoch,
                                controller.signal,
                            )
                        )
                            throw new OperationRegistryError("scope");
                        const result =
                            await originalClient.readConfigurationOutcome(
                                receipt.operation_id,
                                originalKey,
                                {
                                    signal: controller.signal,
                                    responseByteLimit: SESSION_RESPONSE_BYTES,
                                },
                            );
                        if (
                            !currentObservation(
                                proven,
                                observationEpoch,
                                controller.signal,
                            )
                        )
                            throw new OperationRegistryError("scope");
                        if (
                            result.kind === "api_problem" &&
                            result.status === 401
                        )
                            unauthorized();
                        if (result.kind === "success") {
                            if (
                                expected !== undefined &&
                                (result.payload.base_revision !==
                                    expected.baseRevision ||
                                    result.payload.candidate_revision !==
                                        expected.candidateRevision)
                            )
                                throw new WireError("semantic");
                            registry.configurationOutcome(
                                proven,
                                result.payload,
                            );
                            if (
                                !result.payload.pending &&
                                (result.payload.state === "confirmed" ||
                                    result.payload.state === "unchanged")
                            )
                                queries.invalidate(() => true);
                        }
                        return { kind: "outcome", receipt, result };
                    } finally {
                        retention.release(owner);
                    }
                });
            } finally {
                controlledReads.delete(controller);
                observationReads.delete(controller);
            }
        },
        async observeHostActionOutcome(
            id: RecordId,
        ): Promise<HostActionOutcomeObservation> {
            if (
                disposed ||
                pageHidden ||
                connection !== "connected" ||
                !bootstrap.user.admin_permissions.some(
                    (permission) =>
                        permission.capability === "host-read" &&
                        permission.effective,
                )
            )
                throw new OperationRegistryError("scope");
            const record = registry
                .snapshot()
                .records.find((row) => row.recordId === id);
            if (record?.handles.kind !== "basic-key")
                throw new OperationRegistryError("namespace");
            const originalKey = record.handles.key;
            const originalClient = client;
            const auth = registry.authorizeObservation(id, session, {
                reconnect: true,
            });
            const controller = new AbortController();
            controlledReads.add(controller);
            observationReads.add(controller);
            const observationEpoch = visibilityEpoch;
            const owner = "host-action-outcome:" + id;
            try {
                return await reads.run(owner, controller.signal, async () => {
                    if (!retention.claim(owner, READ_RESERVATION_BYTES))
                        throw new StateCapacityError();
                    try {
                        // Always prove the original subject/key association, also after restore.
                        const lookup = await originalClient.lookupOperation(
                            originalKey,
                            {
                                signal: controller.signal,
                                responseByteLimit: SESSION_RESPONSE_BYTES,
                            },
                        );
                        if (
                            !currentObservation(
                                auth,
                                observationEpoch,
                                controller.signal,
                            )
                        )
                            throw new OperationRegistryError("scope");
                        if (lookup.kind !== "success") {
                            if (
                                lookup.kind === "api_problem" &&
                                lookup.status === 401
                            )
                                unauthorized();
                            return { kind: "lookup", result: lookup };
                        }
                        const receipt = lookup.payload.operation;
                        if (
                            receipt.route !==
                                "/api/v1/host/sync-schedule/changes" &&
                            receipt.route !== "/api/v1/host/sync-observer/stops"
                        )
                            throw new WireError("semantic");
                        registry.observed(auth, receipt);
                        const proven = registry.authorizeObservation(
                            id,
                            session,
                        );
                        if (
                            !currentObservation(
                                proven,
                                observationEpoch,
                                controller.signal,
                            )
                        )
                            throw new OperationRegistryError("scope");
                        const result = await (
                            receipt.route ===
                                "/api/v1/host/sync-schedule/changes"
                                ? originalClient.readScheduleOutcome.bind(
                                      originalClient,
                                  )
                                : originalClient.readObserverStopOutcome.bind(
                                      originalClient,
                                  )
                        )(receipt.operation_id, originalKey, {
                            signal: controller.signal,
                            responseByteLimit: SESSION_RESPONSE_BYTES,
                        });
                        if (
                            !currentObservation(
                                proven,
                                observationEpoch,
                                controller.signal,
                            )
                        )
                            throw new OperationRegistryError("scope");
                        if (
                            result.kind === "api_problem" &&
                            result.status === 401
                        )
                            unauthorized();
                        if (result.kind === "success") {
                            registry.hostActionOutcome(proven, result.payload);
                            if (
                                !result.payload.pending &&
                                (result.payload.state === "confirmed" ||
                                    result.payload.state === "unchanged")
                            )
                                queries.invalidate((identity) =>
                                    [
                                        "host_status_default",
                                        "host_observer_default",
                                        "host_journal_default",
                                    ].includes(identity.routeId),
                                );
                        }
                        return { kind: "outcome", receipt, result };
                    } finally {
                        retention.release(owner);
                    }
                });
            } finally {
                controlledReads.delete(controller);
                observationReads.delete(controller);
            }
        },
        observer,
        importHandle(input: ManualImport): RecoveryRecord {
            if (disposed || connection !== "connected")
                throw new OperationRegistryError("scope");
            return registry.importHandle(input, session);
        },
        originalScope: () => session.scope,
        setPageHidden(value: boolean) {
            if (disposed || pageHidden === value) return;
            pageHidden = value;
            if (value) visibilityEpoch++;
            observer.setHidden(value);
            if (value)
                for (const controller of observationReads) controller.abort();
        },
        observe(id: RecordId) {
            if (disposed || connection !== "connected")
                throw new OperationRegistryError("scope");
            const auth = registry.authorizeObservation(id, session, {
                reconnect: true,
            });
            startObservation(auth);
        },
        stopObserving(id: RecordId, reason: PauseReason = "user") {
            observer.pause(id, reason);
        },
        async submit(intent: SubmissionIntent): Promise<{
            readonly recordId: RecordId;
            readonly result: SubmissionResult;
        }> {
            if (
                disposed ||
                connection !== "connected" ||
                pendingSubmission ||
                otherTabChanged
            )
                throw new OperationRegistryError("blocked");
            const hostCapability =
                intent.action === "scheduleChange"
                    ? "schedule-write"
                    : intent.action === "observerStop"
                      ? "observer-stop"
                      : null;
            if (
                hostCapability !== null &&
                !bootstrap.user.admin_permissions.some(
                    (permission) =>
                        permission.capability === hostCapability &&
                        permission.effective,
                )
            )
                throw new OperationRegistryError("scope");
            const originalSession = session;
            const originalClient = client;
            const observationEpoch = visibilityEpoch;
            const observationWasAllowed = !pageHidden;
            const record = registry.prepare(intent.action, originalSession);
            if (record.handles.kind !== "basic-key")
                throw new OperationRegistryError("invalid");
            pendingSubmission = true;
            notice = null;
            publish();
            try {
                const result = await dispatch(originalClient, intent, {
                    idempotencyKey: record.handles.key,
                });
                const saved = registry.submitted(
                    record.recordId,
                    result,
                    originalSession,
                );
                if (saved === null)
                    notice =
                        "Not submitted. Validation refused the request before transmission.";
                if (result.kind === "api_problem" && result.status === 401)
                    unauthorized();
                if (
                    result.kind === "accepted" &&
                    current({
                        recordId: record.recordId,
                        target: originalSession.scope,
                        authGeneration: originalSession.authGeneration,
                        locator: {
                            kind: "id",
                            operationId:
                                result.acceptance.operation.operation_id,
                        },
                        expectedSafeReceiptIdentity: null,
                    })
                ) {
                    if (
                        !observationWasAllowed ||
                        observationEpoch !== visibilityEpoch
                    ) {
                        // A deliberate Observe after return owns its own lifecycle.
                        if (observer.snapshot(record.recordId).phase === "idle")
                            observer.pause(record.recordId, "hidden");
                    } else
                        startObservation(
                            registry.authorizeObservation(
                                record.recordId,
                                session,
                            ),
                        );
                }
                return { recordId: record.recordId, result };
            } finally {
                pendingSubmission = false;
                publish();
            }
        },
        disconnect: unauthorized,
        async reconnect(): Promise<void> {
            if (disposed || connection === "reconnecting") return;
            clearPrivate();
            const reconnectGeneration = session.authGeneration;
            connection = "reconnecting";
            notice = null;
            publish();
            try {
                const next = await options.reconnect();
                if (!stillReconnecting(reconnectGeneration)) return;
                if (releaseChanged(bootstrap, next)) {
                    connection = "update_required";
                    notice =
                        "Interface update required. Copy original recovery handles before reloading.";
                } else {
                    bootstrap = next;
                    session = createAuthSession({
                        scope: bootstrapScope(next),
                        authGeneration: session.authGeneration,
                    });
                    client = new ApiClient({
                        scope: session.scope,
                        ...(options.fetcher === undefined
                            ? {}
                            : { fetcher: options.fetcher }),
                    });
                    queries.setSession(session);
                    hostStatus = newHostStatus();
                    unsubscribeAdvice();
                    advice.dispose();
                    advice = createCrossTabAdvice({ scope: session.scope });
                    unsubscribeAdvice = advice.subscribe(receiveAdvice);
                    connection = "connected";
                    notice =
                        "Reconnected. Observe original operations explicitly; no submission was replayed.";
                }
            } catch (error) {
                if (!stillReconnecting(reconnectGeneration)) return;
                connection =
                    error instanceof InterfaceUpdateRequiredError
                        ? "update_required"
                        : "disconnected";
                notice =
                    error instanceof InterfaceUpdateRequiredError
                        ? "Interface update required. Copy original recovery handles before reloading."
                        : "Reconnect is unavailable. Preserve original handles; no submission was replayed.";
            }
            publish();
        },
        dispose() {
            disposed = true;
            observer.dispose();
            queries.dispose();
            for (const controller of controlledReads) controller.abort();
            for (const owner of privateOwners) retention.release(owner);
            privateOwners.clear();
            unsubscribeRegistry();
            unsubscribeAdvice();
            advice.dispose();
            listeners.clear();
        },
    });
}

export type SessionController = ReturnType<typeof createSessionController>;
