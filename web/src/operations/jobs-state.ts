/** Bounded RAM job intent; the session controller alone owns POST and original handles. */
import { refusalExplanation } from "../state/operation-registry";
import type { RecoveryState } from "../state/operation-registry";
import type { SubmissionResult } from "../api/client";
import type {
    SessionController,
    SubmissionIntent,
} from "../state/session-controller";
import type { ObservationSnapshot } from "../state/operation-observation";
import type { QueryHandle, QuerySnapshot } from "../state/query-state";
import { encodedBytes } from "../state/retention-budget";
import {
    decodeRequestCatalogRefreshSubmission,
    decodeRequestFullVerification,
    decodeRequestInstalledPlan,
    decodeRequestLiteralCandidatePlan,
    decodeRequestNewVerification,
    decodeRequestProbeDiagnostics,
    decodeRequestReadOnlyDiagnostics,
    decodeRequestRevisionVerification,
    decodeRequestSyncSubmission,
} from "../wire/generated";
import type {
    JobReadiness,
    EmptyPayload,
    EstimatePayload,
} from "../wire/generated";
import { parseWireJson } from "../wire/json";

export const MAX_JOB_INPUT_BYTES = 2 * 1024 * 1024;
export const MAX_CANDIDATE_FILE_BYTES = 1024 * 1024;
export const MAX_JOB_REQUEST_BYTES = 1024 * 1024;
export const JOB_KINDS = [
    "installedPlan",
    "sync",
    "candidatePlan",
    "verification",
    "diagnostics",
    "catalogRefresh",
] as const;
export type JobKind = (typeof JOB_KINDS)[number];
type Selection = {
    readonly scope: "all" | "selected";
    readonly selectors: string;
};
export type JobForm =
    | (Selection & {
          readonly kind: "installedPlan" | "sync" | "candidatePlan";
      })
    | {
          readonly kind: "verification";
          readonly mode: "new" | "full" | "revision";
          readonly runId: string;
          readonly revision: string;
      }
    | { readonly kind: "diagnostics"; readonly readOnly: boolean }
    | (Selection & {
          readonly kind: "catalogRefresh";
          readonly revisionScope: "current" | "retained";
          readonly tags: boolean;
          readonly technical: boolean;
      });
export interface CandidateFile {
    readonly name: string;
    readonly bytes: number;
}
export type JobIssue =
    | "invalid"
    | "bounds"
    | "scope"
    | "candidate"
    | "utf8"
    | "capacity"
    | "unavailable";
export class JobInputError extends Error {
    constructor(readonly reason: JobIssue) {
        super("The job input was refused.");
        this.name = "JobInputError";
    }
}
function refuse(reason: JobIssue): never {
    throw new JobInputError(reason);
}
function record(
    input: unknown,
    keys: readonly string[],
): Record<string, unknown> {
    if (input === null || typeof input !== "object" || Array.isArray(input))
        refuse("invalid");
    const prototype: unknown = Object.getPrototypeOf(input);
    if (prototype !== Object.prototype && prototype !== null) refuse("invalid");
    const fields = Reflect.ownKeys(input);
    if (
        fields.length !== keys.length ||
        fields.some((key) => typeof key !== "string" || !keys.includes(key))
    )
        refuse("invalid");
    const result: Record<string, unknown> = {};
    for (const key of keys) {
        const descriptor = Object.getOwnPropertyDescriptor(input, key);
        if (descriptor === undefined || !("value" in descriptor))
            refuse("invalid");
        result[key] = descriptor.value;
    }
    return result;
}
function text(value: unknown, maximum: number): string {
    if (typeof value !== "string") refuse("invalid");
    if (value.length > maximum) refuse("bounds");
    return value;
}
function choice<T extends string>(value: unknown, choices: readonly T[]): T {
    const matched = choices.find((item) => item === value);
    if (matched === undefined) refuse("invalid");
    return matched;
}
function flag(value: unknown): boolean {
    if (typeof value !== "boolean") refuse("invalid");
    return value;
}
export function defaultJobForm(kind: JobKind = "installedPlan"): JobForm {
    switch (kind) {
        case "installedPlan":
        case "sync":
        case "candidatePlan":
            return Object.freeze({ kind, scope: "all", selectors: "" });
        case "verification":
            return Object.freeze({
                kind,
                mode: "new",
                runId: "",
                revision: "",
            });
        case "diagnostics":
            return Object.freeze({ kind, readOnly: true });
        case "catalogRefresh":
            return Object.freeze({
                kind,
                scope: "all",
                selectors: "",
                revisionScope: "current",
                tags: true,
                technical: true,
            });
    }
}
export function parseJobForm(input: unknown): JobForm {
    if (input === null || typeof input !== "object") refuse("invalid");
    const descriptor = Object.getOwnPropertyDescriptor(input, "kind");
    const kind = choice(
        descriptor && "value" in descriptor ? descriptor.value : undefined,
        JOB_KINDS,
    );
    let result: JobForm;
    if (kind === "verification") {
        const row = record(input, ["kind", "mode", "runId", "revision"]);
        result = {
            kind,
            mode: choice(row.mode, ["new", "full", "revision"]),
            runId: text(row.runId, 32),
            revision: text(row.revision, 512),
        };
    } else if (kind === "diagnostics") {
        const row = record(input, ["kind", "readOnly"]);
        result = { kind, readOnly: flag(row.readOnly) };
    } else {
        const row = record(
            input,
            kind === "catalogRefresh"
                ? [
                      "kind",
                      "scope",
                      "selectors",
                      "revisionScope",
                      "tags",
                      "technical",
                  ]
                : ["kind", "scope", "selectors"],
        );
        const selected = {
            scope: choice(row.scope, ["all", "selected"]),
            selectors: text(row.selectors, 25800),
        };
        result =
            kind === "catalogRefresh"
                ? {
                      kind,
                      ...selected,
                      revisionScope: choice(row.revisionScope, [
                          "current",
                          "retained",
                      ]),
                      tags: flag(row.tags),
                      technical: flag(row.technical),
                  }
                : { kind, ...selected };
    }
    if (encodedBytes(result) > MAX_JOB_INPUT_BYTES) refuse("bounds");
    return Object.freeze(result);
}
function selectors(form: Selection): string[] {
    if (form.scope === "all") {
        if (form.selectors.trim() !== "") refuse("scope");
        return [];
    }
    const rows = form.selectors.split(/\r\n|\r|\n/u);
    if (rows.length > 100) refuse("bounds");
    const values = rows.map((row) => row.trim()).filter((row) => row !== "");
    if (values.length === 0) refuse("scope");
    if (values.some((row) => row.length > 256)) refuse("bounds");
    return [...new Set(values)].sort();
}
function wire(value: unknown) {
    return parseWireJson(JSON.stringify(value));
}
export type JobSubmissionIntent = Extract<
    SubmissionIntent,
    {
        action:
            | "sync"
            | "installedPlan"
            | "candidatePlan"
            | "readOnlyDiagnostics"
            | "probeDiagnostics"
            | "newVerification"
            | "fullVerification"
            | "revisionVerification"
            | "catalogRefresh";
    }
>;
export function buildJobIntent(
    input: JobForm,
    candidate: string | null = null,
): JobSubmissionIntent {
    const form = parseJobForm(input);
    try {
        let intent: JobSubmissionIntent;
        switch (form.kind) {
            case "sync":
                intent = {
                    action: "sync",
                    request: decodeRequestSyncSubmission(
                        wire({ selectors: selectors(form) }),
                    ),
                };
                break;
            case "installedPlan":
                intent = {
                    action: "installedPlan",
                    request: decodeRequestInstalledPlan(
                        wire({ selectors: selectors(form) }),
                    ),
                };
                break;
            case "candidatePlan":
                if (candidate === null || candidate.length === 0)
                    refuse("candidate");
                if (
                    new TextEncoder().encode(candidate).length >
                    MAX_CANDIDATE_FILE_BYTES
                )
                    refuse("bounds");
                intent = {
                    action: "candidatePlan",
                    request: decodeRequestLiteralCandidatePlan(
                        wire({ selectors: selectors(form), candidate }),
                    ),
                };
                break;
            case "diagnostics":
                intent = form.readOnly
                    ? {
                          action: "readOnlyDiagnostics",
                          request: decodeRequestReadOnlyDiagnostics(
                              wire({ read_only: true }),
                          ),
                      }
                    : {
                          action: "probeDiagnostics",
                          request: decodeRequestProbeDiagnostics(
                              wire({ read_only: false }),
                          ),
                      };
                break;
            case "verification":
                if (form.mode === "new") {
                    if (form.revision.trim() !== "") refuse("scope");
                    const runId = form.runId.trim();
                    intent = {
                        action: "newVerification",
                        request: decodeRequestNewVerification(
                            wire({
                                mode: "new",
                                ...(runId === "" ? {} : { run_id: runId }),
                            }),
                        ),
                    };
                } else if (form.mode === "full") {
                    if (form.runId.trim() !== "" || form.revision.trim() !== "")
                        refuse("scope");
                    intent = {
                        action: "fullVerification",
                        request: decodeRequestFullVerification(
                            wire({ mode: "full" }),
                        ),
                    };
                } else {
                    if (form.runId.trim() !== "") refuse("scope");
                    intent = {
                        action: "revisionVerification",
                        request: decodeRequestRevisionVerification(
                            wire({
                                mode: "revision",
                                revision: form.revision.trim(),
                            }),
                        ),
                    };
                }
                break;
            case "catalogRefresh":
                if (!form.tags && !form.technical) refuse("scope");
                intent = {
                    action: "catalogRefresh",
                    request: decodeRequestCatalogRefreshSubmission(
                        wire({
                            selectors: selectors(form),
                            revision_scope: form.revisionScope,
                            tags: form.tags,
                            technical: form.technical,
                        }),
                    ),
                };
                break;
        }
        if (encodedBytes(intent.request) > MAX_JOB_REQUEST_BYTES)
            refuse("bounds");
        return Object.freeze(intent);
    } catch (error) {
        if (error instanceof JobInputError) throw error;
        refuse("invalid");
    }
}
export interface JobDescription {
    readonly capability: "read" | "write";
    readonly scope: string;
    readonly effects: string;
}
export function describeJob(form: JobForm): JobDescription {
    const selected =
        "scope" in form && form.scope === "selected"
            ? "Only the explicit repository selectors."
            : "All configured repositories selected by the installed policy.";
    switch (form.kind) {
        case "installedPlan":
            return {
                capability: "read",
                scope: selected,
                effects:
                    "Contacts the installed Hub authority for sizing. Creates an operation receipt; no model downloads, configuration installation or archive writes.",
            };
        case "candidatePlan":
            return {
                capability: "write",
                scope:
                    form.scope === "selected"
                        ? "Only the explicit candidate repository selectors."
                        : "All repositories in the candidate configuration.",
                effects:
                    "Sizes the selected candidate file using installed Hub authority. Syntax validity does not prove authority compatibility. No configuration installation, model download or archive write.",
            };
        case "sync":
            return {
                capability: "write",
                scope: selected,
                effects:
                    "Contacts the Hub and can download, publish, update catalog metadata and apply installed retention policy. Server archive guards and locks remain authoritative.",
            };
        case "verification":
            return {
                capability: "write",
                scope:
                    form.mode === "new"
                        ? "New publications from the chosen original sync run, or the server's existing new-publication selection."
                        : form.mode === "full"
                          ? "Every retained publication."
                          : "Only the exact TYPE:repository@commit SHA.",
                effects:
                    "Offline private-worker verification hashes archive bytes and writes verification reports/catalog metadata. No Hub contact, repair or pruning.",
            };
        case "diagnostics":
            return {
                capability: form.readOnly ? "read" : "write",
                scope: "Checks the installed server configuration and Hub connectivity.",
                effects: form.readOnly
                    ? "Contacts the Hub but skips archive-write probes and the archive lock. Still creates an operation receipt."
                    : "Contacts the Hub and performs temporary archive health probes under the existing lock. Does not synchronize repositories.",
            };
        case "catalogRefresh":
            return {
                capability: "write",
                scope:
                    (form.scope === "selected"
                        ? "Only the explicit repository selectors."
                        : "The server's configured and archived repository union.") +
                    (form.revisionScope === "retained"
                        ? " Includes retained publications."
                        : " Uses current publications."),
                effects:
                    "Offline supplemental-metadata writes only. Technical capture may read bounded publication metadata and README bytes; no Hub download, whole-payload verification, repair or purge.",
            };
    }
}
export interface JobsSnapshot {
    readonly authGeneration: number;
    readonly generation: number;
    readonly form: JobForm;
    readonly candidateFile: CandidateFile | null;
    readonly pending: "submission" | "estimate" | "file" | null;
    readonly issue: JobIssue | null;
    readonly notice: string | null;
    readonly canSubmit: boolean;
    readonly canEstimate: boolean;
    readonly description: JobDescription;
    readonly capabilityAvailable: boolean;
    readonly availabilityReason: string;
    readonly readinessPhase: "checking" | "ready" | "unavailable";
    readonly lastAction: JobSubmissionIntent["action"] | null;
    readonly lastRecordId: string | null;
    readonly lastRecoveryState: RecoveryState | null;
    readonly lastRefusalExplanation: string | null;
    readonly submission: SubmissionResult | null;
    readonly observation: ObservationSnapshot | null;
    readonly estimate: QuerySnapshot<EstimatePayload, EmptyPayload> | null;
}
function readFile(
    file: File,
    assign: (reader: FileReader) => void,
): Promise<ArrayBuffer> {
    if (typeof FileReader === "undefined") return file.arrayBuffer();
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        assign(reader);
        reader.onload = () => {
            if (reader.result instanceof ArrayBuffer) resolve(reader.result);
            else reject(new JobInputError("candidate"));
        };
        reader.onerror = () => {
            reject(new JobInputError("candidate"));
        };
        reader.onabort = () => {
            reject(new JobInputError("unavailable"));
        };
        reader.readAsArrayBuffer(file);
    });
}
export function createJobsStore(controller: SessionController) {
    let session = controller.snapshot(),
        authGeneration = session.generation,
        generation = 0;
    let form = defaultJobForm(),
        candidate: string | null = null,
        candidateFile: CandidateFile | null = null;
    let pending: JobsSnapshot["pending"] = null,
        issue: JobIssue | null = null,
        notice: string | null = null;
    let lastAction: JobsSnapshot["lastAction"] = null,
        lastRecordId: string | null = null,
        submission: SubmissionResult | null = null;
    let slot = controller.createPrivateSlot(),
        estimate: QueryHandle<EstimatePayload, EmptyPayload> | null = null;
    let reader: FileReader | null = null,
        disposed = false;
    let unsubscribeEstimate = () => {},
        unsubscribeObservation = () => {};
    const listeners = new Set<() => void>();
    let snapshot: JobsSnapshot;
    let readinessActive = false;
    let readiness: JobReadiness | null = null;
    let readinessPhase: JobsSnapshot["readinessPhase"] = "unavailable";
    let readinessAt = 0,
        readinessSerial = 0;
    let readinessAbort: AbortController | null = null;
    let readinessTimer: ReturnType<typeof setTimeout> | null = null;
    function clearReadiness() {
        readinessSerial++;
        readinessAbort?.abort();
        readinessAbort = null;
        if (readinessTimer !== null) clearTimeout(readinessTimer);
        readinessTimer = null;
        readiness = null;
        readinessPhase = "unavailable";
    }
    function readinessCurrent(
        serial: number,
        auth: number,
        signal: AbortSignal,
    ) {
        return (
            !disposed &&
            !signal.aborted &&
            serial === readinessSerial &&
            authGeneration === auth
        );
    }
    async function recheckReadiness() {
        readinessActive = true;
        clearReadiness();
        if (
            disposed ||
            session.pageHidden ||
            session.connection !== "connected"
        )
            return;
        const serial = readinessSerial;
        const ownAuth = authGeneration;
        const abort = new AbortController();
        readinessAbort = abort;
        readinessPhase = "checking";
        publish();
        try {
            const result = await controller.readJobReadiness({
                signal: abort.signal,
            });
            if (!readinessCurrent(serial, ownAuth, abort.signal)) return;
            if (result.kind === "success") {
                readiness = result.payload;
                readinessAt = performance.now();
                readinessPhase = "ready";
                if (!retain()) {
                    readiness = null;
                    readinessPhase = "unavailable";
                }
                readinessTimer = setTimeout(() => {
                    clearReadiness();
                    publish();
                }, 30000);
            } else readinessPhase = "unavailable";
        } catch {
            if (serial === readinessSerial) readinessPhase = "unavailable";
        } finally {
            if (serial === readinessSerial) {
                readinessAbort = null;
                publish();
            }
        }
    }
    function availability(): { blocked: boolean; reason: string } {
        if (!session.canSubmit) {
            const active = session.registry.records.some((record) =>
                ["accepted", "observing"].includes(record.state),
            );
            return {
                blocked: true,
                reason:
                    session.connection !== "connected"
                        ? "Unavailable: reconnect to check job readiness."
                        : session.registry.storage !== "ready"
                          ? "Unavailable: original request recovery storage needs review."
                          : active
                            ? "Unavailable: an original job is active. Follow its original result in Operations."
                            : "Needs review: an original request is unresolved. Review it in Operations before starting a new job.",
            };
        }
        const fresh =
            readiness !== null && performance.now() - readinessAt < 30000;
        if (!fresh)
            return {
                blocked: false,
                reason:
                    readinessPhase === "checking"
                        ? "Checking job readiness. You may submit explicitly for fresh server checks."
                        : "Readiness unavailable. Recheck or submit explicitly for fresh server checks.",
            };
        const facts = readiness;
        if (facts === null)
            return { blocked: false, reason: "Readiness unavailable." };
        const archive =
            ["sync", "verification", "catalogRefresh"].includes(form.kind) ||
            (form.kind === "diagnostics" && !form.readOnly);
        const hub = ["installedPlan", "candidatePlan", "diagnostics"].includes(
            form.kind,
        );
        if (archive && facts.archive === false)
            return {
                blocked: true,
                reason: "Unavailable: archive writes are disabled.",
            };
        if (hub && facts.hub === false)
            return {
                blocked: true,
                reason: "Unavailable: Hub access is disabled.",
            };
        if (archive && facts.archive_writable === false)
            return {
                blocked: true,
                reason: "Unavailable: required archive storage is read-only.",
            };
        if (
            form.kind === "verification" &&
            facts.verification_available === false
        )
            return {
                blocked: true,
                reason: "Unavailable: the verification worker is unavailable.",
            };
        if (
            (archive &&
                (facts.archive === null || facts.archive_writable === null)) ||
            (hub && facts.hub === null) ||
            (form.kind === "verification" &&
                facts.verification_available === null)
        )
            return {
                blocked: false,
                reason: "Some readiness facts are unknown. Submit explicitly for fresh server checks or recheck.",
            };
        return {
            blocked: false,
            reason: "Observed readiness is available. The server checks authorization and storage freshly on submission.",
        };
    }

    function retain() {
        return slot.set({
            form,
            candidate,
            candidateFile,
            submission,
            readiness,
        });
    }
    let checkedForm: JobForm | null = null,
        checkedCandidate: string | null = null;
    let inputIssue: JobIssue | null = null;
    function publish() {
        if (disposed) return;
        const description = describeJob(form);
        const capabilityAvailable =
            session.connection === "connected" &&
            session.bootstrap.user.rest_capabilities.includes(
                description.capability,
            );
        if (checkedForm !== form || checkedCandidate !== candidate) {
            checkedForm = form;
            checkedCandidate = candidate;
            inputIssue = null;
            try {
                buildJobIntent(form, candidate);
            } catch (error) {
                inputIssue =
                    error instanceof JobInputError ? error.reason : "invalid";
            }
        }
        const available = availability();
        const lastRecord = session.registry.records.find(
            (record) => record.recordId === lastRecordId,
        );
        snapshot = Object.freeze({
            authGeneration,
            generation,
            form,
            candidateFile,
            pending,
            issue: issue ?? inputIssue,
            notice,
            canSubmit:
                !available.blocked &&
                inputIssue === null &&
                capabilityAvailable &&
                session.canSubmit &&
                pending === null,
            canEstimate:
                session.connection === "connected" &&
                session.bootstrap.user.rest_capabilities.includes("read") &&
                pending === null,
            description,
            capabilityAvailable,
            readinessPhase,
            availabilityReason: capabilityAvailable
                ? available.reason
                : "Unavailable: this session lacks the required REST capability.",
            lastAction,
            lastRecordId,
            lastRecoveryState: lastRecord?.state ?? null,
            lastRefusalExplanation:
                lastRecord?.disposition === null ||
                lastRecord?.disposition === undefined
                    ? null
                    : refusalExplanation(lastRecord.disposition.reason),
            submission,
            observation:
                lastRecordId === null
                    ? null
                    : controller.observer.snapshot(lastRecordId),
            estimate: estimate?.snapshot() ?? null,
        });
        for (const listener of listeners) {
            try {
                listener();
            } catch {
                /* A detached view cannot alter intent or drain. */
            }
        }
    }
    function stopFile() {
        reader?.abort();
        reader = null;
    }
    function clear() {
        clearReadiness();
        generation++;
        stopFile();
        unsubscribeEstimate();
        estimate?.invalidate();
        estimate = null;
        unsubscribeObservation();
        form = defaultJobForm();
        candidate = null;
        candidateFile = null;
        checkedForm = null;
        checkedCandidate = null;
        inputIssue = null;
        pending = null;
        issue = null;
        submission = null;
        lastAction = null;
        lastRecordId = null;
        slot.clear();
    }
    const unsubscribeSession = controller.subscribe(() => {
        const next = controller.snapshot();
        if (
            next.generation !== authGeneration ||
            next.connection !== "connected"
        ) {
            clear();
            authGeneration = next.generation;
            slot = controller.createPrivateSlot();
            notice =
                "Authentication or connection changed. The private job input was cleared; original handles remain in Operations.";
        }
        const visibilityChanged =
            next.visibilityEpoch !== session.visibilityEpoch ||
            next.pageHidden !== session.pageHidden;
        session = next;
        if (visibilityChanged) {
            clearReadiness();
            if (!next.pageHidden && readinessActive) void recheckReadiness();
        }
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
        recheckReadiness,
        setForm(input: unknown): boolean {
            if (
                disposed ||
                session.connection !== "connected" ||
                pending !== null
            )
                return false;
            try {
                const next = parseJobForm(input),
                    before = { form, candidate, candidateFile };
                const contextChanged =
                    next.kind !== form.kind ||
                    (next.kind === "verification" &&
                        form.kind === "verification" &&
                        next.mode !== form.mode) ||
                    (next.kind === "diagnostics" &&
                        form.kind === "diagnostics" &&
                        next.readOnly !== form.readOnly);
                form = next;
                if (next.kind !== "candidatePlan") {
                    candidate = null;
                    candidateFile = null;
                }
                if (!retain()) {
                    ({ form, candidate, candidateFile } = before);
                    refuse("capacity");
                }
                generation++;
                issue = null;
                notice = null;
                publish();
                if (contextChanged && readinessActive) void recheckReadiness();
                return true;
            } catch (error) {
                issue =
                    error instanceof JobInputError ? error.reason : "invalid";
                publish();
                return false;
            }
        },
        async selectCandidate(file: File): Promise<boolean> {
            if (
                disposed ||
                form.kind !== "candidatePlan" ||
                pending !== null ||
                session.connection !== "connected"
            )
                return false;
            const ownGeneration = ++generation;
            pending = "file";
            issue = null;
            notice = null;
            publish();
            try {
                if (
                    !Number.isSafeInteger(file.size) ||
                    file.size < 1 ||
                    file.size > MAX_CANDIDATE_FILE_BYTES
                )
                    refuse("bounds");
                if (
                    file.name.length > 255 ||
                    !/^[^\x00-\x1f\x7f/\\]+$/u.test(file.name)
                )
                    refuse("candidate");
                const bytes = await readFile(file, (value) => {
                    reader = value;
                });
                if (generation !== ownGeneration) return false;
                if (
                    bytes.byteLength !== file.size ||
                    bytes.byteLength > MAX_CANDIDATE_FILE_BYTES
                )
                    refuse("bounds");
                let decoded: string;
                try {
                    decoded = new TextDecoder("utf-8", {
                        fatal: true,
                        ignoreBOM: true,
                    }).decode(bytes);
                } catch {
                    refuse("utf8");
                }
                if (
                    encodedBytes({ candidate: decoded, selectors: [] }) >
                    MAX_JOB_REQUEST_BYTES
                )
                    refuse("bounds");
                const before = { candidate, candidateFile };
                candidate = decoded;
                candidateFile = Object.freeze({
                    name: file.name,
                    bytes: bytes.byteLength,
                });
                if (!retain()) {
                    ({ candidate, candidateFile } = before);
                    refuse("capacity");
                }
                return true;
            } catch (error) {
                if (generation === ownGeneration)
                    issue =
                        error instanceof JobInputError
                            ? error.reason
                            : "candidate";
                return false;
            } finally {
                if (generation === ownGeneration) {
                    reader = null;
                    pending = null;
                    publish();
                }
            }
        },
        clearCandidate() {
            if (pending !== null) return;
            candidate = null;
            candidateFile = null;
            generation++;
            issue = null;
            retain();
            publish();
        },
        reset() {
            if (pending === "submission") return;
            clear();
            notice =
                "Local job input cleared. Accepted operations and original handles were not cancelled.";
            retain();
            publish();
        },
        async submit() {
            if (!snapshot.canSubmit) {
                issue = "unavailable";
                publish();
                return;
            }
            let intent: JobSubmissionIntent;
            try {
                intent = buildJobIntent(form, candidate);
            } catch (error) {
                issue =
                    error instanceof JobInputError ? error.reason : "invalid";
                publish();
                return;
            }
            const ownAuth = authGeneration;
            pending = "submission";
            issue = null;
            notice = null;
            publish();
            try {
                const result = await controller.submit(intent);
                if (disposed || authGeneration !== ownAuth) return;
                submission = result.result;
                lastAction = intent.action;
                lastRecordId = result.recordId;
                const notAdmitted =
                    session.registry.records.find(
                        (record) => record.recordId === result.recordId,
                    )?.state === "not_admitted";
                if (notAdmitted) clearReadiness();
                if (!retain()) {
                    submission = null;
                    issue = "capacity";
                }
                unsubscribeObservation();
                unsubscribeObservation = controller.observer.subscribe(
                    result.recordId,
                    publish,
                );
                notice = notAdmitted
                    ? "Recheck job readiness before considering a distinct new job. The original request will not be retried."
                    : "Submission is not domain completion. Observe the original operation; no request was retried.";
            } catch {
                if (authGeneration === ownAuth) {
                    issue = "unavailable";
                    notice =
                        "Job admission is unavailable. Preserve original handles in Operations; no request was retried.";
                }
            } finally {
                if (authGeneration === ownAuth) {
                    pending = null;
                    publish();
                }
            }
        },
        async estimate() {
            if (!snapshot.canEstimate) return;
            const ownGeneration = generation,
                ownAuth = authGeneration;
            pending = "estimate";
            issue = null;
            publish();
            try {
                if (estimate === null) {
                    const api = controller.apiReads;
                    estimate = controller.queries.query(
                        { routeId: "estimate_default" },
                        (options) => api.readVerificationEstimate(options),
                    );
                    unsubscribeEstimate = estimate.subscribe(publish);
                }
                await estimate.refresh();
            } catch {
                if (ownAuth === authGeneration) issue = "unavailable";
            } finally {
                if (
                    ownAuth === authGeneration &&
                    ownGeneration === generation
                ) {
                    pending = null;
                    publish();
                }
            }
        },
        pause() {
            readinessActive = false;
            clearReadiness();
            if (pending === "file") {
                generation++;
                stopFile();
                pending = null;
            }
            if (pending === "estimate") {
                generation++;
                estimate?.invalidate();
                pending = null;
            }
            publish();
        },
        dispose() {
            clear();
            disposed = true;
            unsubscribeSession();
            listeners.clear();
        },
    });
}
export type JobsStore = ReturnType<typeof createJobsStore>;
