/** Bounded explicit maintenance intent; original operations remain controller-owned. */
import type { ExactPublication } from "../api/identity";
import { publicationIdentity, repositorySegments } from "../api/identity";
import type {
    SessionController,
    SubmissionIntent,
} from "../state/session-controller";
import type { RecordId } from "../state/authority";
import type { ObservationSnapshot } from "../state/operation-observation";
import type { QueryHandle, QuerySnapshot } from "../state/query-state";
import { encodedBytes } from "../state/retention-budget";
import { ACTION_ROUTES } from "../state/operation-registry";
import * as wire from "../wire/generated";
import type {
    EmptyPayload,
    Finding,
    ManifestPayload,
    PrunePayload,
    PurgePayload,
    QuarantinePayload,
    RecoveryPlanPayload,
    ReferencePayload,
} from "../wire/generated";
import { parseWireJson } from "../wire/json";

export type MaintenanceForm =
    | {
          readonly kind: "prune";
          readonly scope: "all" | "selected";
          readonly selectors: string;
      }
    | {
          readonly kind: "purge";
          readonly scope: "selected" | "all_unmanaged";
          readonly selectors: string;
      }
    | { readonly kind: "recovery" }
    | { readonly kind: "quarantine"; readonly transactionIds: string }
    | { readonly kind: "repair"; readonly reason: string };
export type MaintenanceIssue =
    "invalid" | "bounds" | "scope" | "capacity" | "unavailable";
export interface RepairFindingIntent {
    readonly source: {
        readonly archiveId: string;
        readonly runId: string;
        readonly completedAt: string;
    };
    readonly finding: Finding;
}
export type PairedReview =
    | { readonly kind: "prune"; readonly payload: PrunePayload }
    | { readonly kind: "purge"; readonly payload: PurgePayload }
    | { readonly kind: "recovery"; readonly payload: RecoveryPlanPayload }
    | { readonly kind: "quarantine"; readonly payload: QuarantinePayload };
export type MaintenanceIntent = Extract<
    SubmissionIntent,
    {
        action:
            | "prunePreview"
            | "pruneApply"
            | "purgePreview"
            | "purgeApply"
            | "recoveryPreview"
            | "recoveryApply"
            | "quarantinePreview"
            | "quarantineApply"
            | "repair";
    }
>;
export class MaintenanceInputError extends Error {
    constructor(readonly reason: MaintenanceIssue) {
        super("The maintenance input was refused.");
        this.name = "MaintenanceInputError";
    }
}
function refuse(reason: MaintenanceIssue): never {
    throw new MaintenanceInputError(reason);
}
function object(
    input: unknown,
    keys: readonly string[],
): Record<string, unknown> {
    if (input === null || typeof input !== "object" || Array.isArray(input))
        refuse("invalid");
    const prototype: unknown = Object.getPrototypeOf(input);
    if (prototype !== Object.prototype && prototype !== null) refuse("invalid");
    const own = Reflect.ownKeys(input);
    if (
        own.length !== keys.length ||
        own.some((k) => typeof k !== "string" || !keys.includes(k))
    )
        refuse("invalid");
    const result: Record<string, unknown> = {};
    for (const k of keys) {
        const d = Object.getOwnPropertyDescriptor(input, k);
        if (!d || !("value" in d)) refuse("invalid");
        result[k] = d.value;
    }
    return result;
}
function text(value: unknown, maximum: number): string {
    if (typeof value !== "string") refuse("invalid");
    if (value.length > maximum) refuse("bounds");
    return value;
}
function choice<T extends string>(value: unknown, choices: readonly T[]): T {
    const found = choices.find((v) => v === value);
    if (found === undefined) refuse("invalid");
    return found;
}
const canonical = (value: unknown) => parseWireJson(JSON.stringify(value));
export function defaultMaintenanceForm(
    kind: MaintenanceForm["kind"] = "prune",
): MaintenanceForm {
    switch (kind) {
        case "prune":
            return Object.freeze({ kind, scope: "all", selectors: "" });
        case "purge":
            return Object.freeze({ kind, scope: "selected", selectors: "" });
        case "recovery":
            return Object.freeze({ kind });
        case "quarantine":
            return Object.freeze({ kind, transactionIds: "" });
        case "repair":
            return Object.freeze({ kind, reason: "operator_requested" });
    }
}
export function parseMaintenanceForm(input: unknown): MaintenanceForm {
    if (input === null || typeof input !== "object") refuse("invalid");
    const d = Object.getOwnPropertyDescriptor(input, "kind"),
        kind = choice(d && "value" in d ? d.value : undefined, [
            "prune",
            "purge",
            "recovery",
            "quarantine",
            "repair",
        ]);
    let result: MaintenanceForm;
    if (kind === "prune" || kind === "purge") {
        const row = object(input, ["kind", "scope", "selectors"]),
            selectors = text(row.selectors, 25800);
        result =
            kind === "prune"
                ? {
                      kind,
                      scope: choice(row.scope, ["all", "selected"]),
                      selectors,
                  }
                : {
                      kind,
                      scope: choice(row.scope, ["selected", "all_unmanaged"]),
                      selectors,
                  };
    } else if (kind === "recovery") {
        object(input, ["kind"]);
        result = { kind };
    } else if (kind === "quarantine") {
        const row = object(input, ["kind", "transactionIds"]);
        result = { kind, transactionIds: text(row.transactionIds, 3400) };
    } else {
        const row = object(input, ["kind", "reason"]);
        const reason = text(row.reason, 8192);
        if (Array.from(reason).length > 2048) refuse("bounds");
        result = { kind, reason };
    }
    if (encodedBytes(result) > 2 * 1024 * 1024) refuse("bounds");
    return Object.freeze(result);
}
function lines(source: string): string[] {
    const rows = source.split(/\r\n|\r|\n/u);
    if (rows.length > 100) refuse("bounds");
    const values = rows.map((v) => v.trim()).filter((v) => v !== "");
    if (values.length === 0) refuse("scope");
    return [...new Set(values)].sort();
}
function selected(
    form: Extract<MaintenanceForm, { kind: "prune" | "purge" }>,
): readonly string[] {
    if (form.scope !== "selected") {
        if (form.selectors.trim() !== "") refuse("scope");
        return [];
    }
    const values = lines(form.selectors);
    if (values.some((v) => v.length > 256 || v.includes("@"))) refuse("scope");
    return (
        wire.decodeRequestPurgeSubmission(
            canonical({ selectors: values, all_unmanaged: false }),
        ).selectors ?? []
    );
}
export function buildMaintenanceIntent(
    input: MaintenanceForm,
    apply = false,
    finding: RepairFindingIntent | null = null,
): MaintenanceIntent {
    const form = parseMaintenanceForm(input);
    try {
        switch (form.kind) {
            case "prune":
                return {
                    action: apply ? "pruneApply" : "prunePreview",
                    request: wire.decodeRequestPruneSubmission(
                        canonical({ selectors: selected(form) }),
                    ),
                };
            case "purge":
                return {
                    action: apply ? "purgeApply" : "purgePreview",
                    request: wire.decodeRequestPurgeSubmission(
                        canonical({
                            selectors: selected(form),
                            all_unmanaged: form.scope === "all_unmanaged",
                        }),
                    ),
                };
            case "recovery":
                return {
                    action: apply ? "recoveryApply" : "recoveryPreview",
                    request: wire.decodeRequestRecoverySubmission(
                        canonical({}),
                    ),
                };
            case "quarantine":
                return {
                    action: apply ? "quarantineApply" : "quarantinePreview",
                    request: wire.decodeRequestQuarantineSubmission(
                        canonical({
                            transaction_ids: lines(form.transactionIds),
                        }),
                    ),
                };
            case "repair": {
                if (!apply || finding === null) refuse("scope");
                const f = finding.finding,
                    commitSha = f.commit_sha,
                    publicationId = f.publication_id;
                if (commitSha === null || publicationId === null)
                    refuse("scope");
                publicationIdentity({
                    repositoryType: f.repository_type,
                    repositoryId: f.repository_id,
                    commitSha,
                    publicationId,
                });
                return {
                    action: "repair",
                    request: wire.decodeRequestRepairSubmission(
                        canonical({
                            revision: `${f.repository_type}:${f.repository_id}@${commitSha}`,
                            reason: form.reason,
                        }),
                    ),
                };
            }
        }
    } catch (error) {
        if (error instanceof MaintenanceInputError) throw error;
        refuse("scope");
    }
}
const REMEDIES = [
    "quarantine_staging",
    "quarantine_tree",
    "complete_publication",
    "rollback_prune",
    "complete_prune",
    "complete_repair",
    "finish_repair_cleanup",
    "close_journal",
];
function reviewPayload(
    form: MaintenanceForm,
    value: unknown,
): { review: PairedReview; eligibility: MaintenanceSnapshot["eligibility"] } {
    if (encodedBytes(value) > 8 * 1024 * 1024) refuse("capacity");
    if (form.kind === "repair") refuse("scope");
    let review: PairedReview;
    switch (form.kind) {
        case "prune":
            review = {
                kind: form.kind,
                payload: wire.decodePrunePayload(canonical(value)),
            };
            break;
        case "purge":
            review = {
                kind: form.kind,
                payload: wire.decodePurgePayload(canonical(value)),
            };
            break;
        case "recovery":
            review = {
                kind: form.kind,
                payload: wire.decodeRecoveryPlanPayload(canonical(value)),
            };
            break;
        case "quarantine":
            review = {
                kind: form.kind,
                payload: wire.decodeQuarantinePayload(canonical(value)),
            };
            break;
    }
    let eligibility: MaintenanceSnapshot["eligibility"] = "ready";
    if (review.kind === "recovery") {
        const p = review.payload,
            ids = p.plan.map((v) => v.transaction_id);
        if (
            new Set(ids).size !== ids.length ||
            p.plan.some(
                (v) => ![...REMEDIES, "operator", "wait"].includes(v.remedy),
            ) ||
            p.actionable !==
                p.plan.filter((v) => REMEDIES.includes(v.remedy)).length ||
            p.blocked !== p.plan.filter((v) => v.remedy === "operator").length
        )
            refuse("scope");
        eligibility =
            p.blocked > 0
                ? "blocked"
                : p.actionable === 0
                  ? "nothing_eligible"
                  : "ready";
    } else {
        if (review.payload.applied.length !== 0) refuse("scope");
        if (review.kind === "quarantine") {
            const wanted = buildMaintenanceIntent(form).request;
            if (!("transaction_ids" in wanted)) refuse("scope");
            const ids = review.payload.plans.map((v) => v.transaction_id);
            if (
                ids.length !== wanted.transaction_ids.length ||
                new Set(ids).size !== ids.length ||
                ids.some((v) => !wanted.transaction_ids.includes(v))
            )
                refuse("scope");
            eligibility = review.payload.plans.every((v) => v.already_absent)
                ? "nothing_eligible"
                : "ready";
        } else {
            const repos = review.payload.plans.map(
                    (v) => `${v.repository_type}:${v.repository_id}`,
                ),
                plans = review.payload.plans.map((v) => v.plan_id);
            if (
                new Set(repos).size !== repos.length ||
                new Set(plans).size !== plans.length
            )
                refuse("scope");
            if (form.kind !== "prune" && form.kind !== "purge") refuse("scope");
            const wanted = selected(form);
            if (
                form.scope === "selected" &&
                repos.some((v) => !wanted.includes(v))
            )
                refuse("scope");
            if (
                review.kind === "prune" &&
                review.payload.plans.some(
                    (p) => p.selected.commit_sha === p.current.commit_sha,
                )
            )
                refuse("scope");
            eligibility =
                review.payload.plans.length === 0
                    ? "nothing_eligible"
                    : "ready";
        }
    }
    return { review: Object.freeze(review), eligibility };
}
export interface MaintenanceSnapshot {
    readonly connected: boolean;
    readonly authGeneration: number;
    readonly generation: number;
    readonly form: MaintenanceForm;
    readonly formIssue: MaintenanceIssue | null;
    readonly pending: "preview" | "apply" | "repairProof" | null;
    readonly previewRecordId: RecordId | null;
    readonly previewObservation: ObservationSnapshot | null;
    readonly review: PairedReview | null;
    readonly reviewGeneration: number;
    readonly eligibility:
        "ready" | "nothing_eligible" | "blocked" | "unconfirmed";
    readonly confirmed: boolean;
    readonly canPreview: boolean;
    readonly canConfirm: boolean;
    readonly canApply: boolean;
    readonly effectRecordId: RecordId | null;
    readonly effectObservation: ObservationSnapshot | null;
    readonly effectFinding: RepairFindingIntent | null;
    readonly effectPublication: ExactPublication | null;
    readonly finding: RepairFindingIntent | null;
    readonly repairProof:
        "idle" | "reading" | "ready" | "changed" | "unavailable" | "failed";
    readonly freshPublication: ExactPublication | null;
    readonly freshPublicationGeneration: number | null;
    readonly reference: QuerySnapshot<ReferencePayload, EmptyPayload> | null;
    readonly manifest: QuerySnapshot<ManifestPayload, EmptyPayload> | null;
    readonly canCheckRepair: boolean;
    readonly canRepair: boolean;
    readonly notice: string | null;
}
export function createMaintenanceStore(controller: SessionController) {
    let session = controller.snapshot(),
        authGeneration = session.generation,
        generation = 0,
        reviewGeneration = 0;
    let form = defaultMaintenanceForm(),
        formIssue: MaintenanceIssue | null = null,
        pending: MaintenanceSnapshot["pending"] = null,
        notice: string | null = null;
    let previewRecordId: RecordId | null = null,
        effectRecordId: RecordId | null = null,
        review: PairedReview | null = null,
        eligibility: MaintenanceSnapshot["eligibility"] = "unconfirmed",
        confirmed = false;
    let finding: RepairFindingIntent | null = null,
        effectFinding: RepairFindingIntent | null = null,
        effectPublication: ExactPublication | null = null;
    let repairProof: MaintenanceSnapshot["repairProof"] = "idle",
        freshPublication: ExactPublication | null = null,
        freshPublicationGeneration: number | null = null;
    let reference: QueryHandle<ReferencePayload, EmptyPayload> | null = null,
        manifest: QueryHandle<ManifestPayload, EmptyPayload> | null = null;
    let unsubscribeRef = () => {},
        unsubscribeManifest = () => {},
        unsubscribePreview = () => {},
        unsubscribeEffect = () => {};
    let slot = controller.createPrivateSlot(),
        disposed = false,
        taskSerial = 0,
        pendingToken: number | null = null;
    let owner: {
        generation: number;
        auth: number;
        kind: MaintenanceForm["kind"];
        form: MaintenanceForm;
        action: MaintenanceIntent["action"];
        request: string;
        recordId: RecordId;
    } | null = null;
    let seenResult: string | null = null;
    const listeners = new Set<() => void>();
    let snapshot: MaintenanceSnapshot;
    function retain() {
        if (disposed) return false;
        return slot.set({
            previewRequest: owner?.request ?? null,
            form,
            finding,
            review,
            effectFinding,
            effectPublication,
            freshPublication,
            freshPublicationGeneration,
        });
    }
    function dropProof() {
        unsubscribeRef();
        unsubscribeManifest();
        reference?.invalidate();
        manifest?.invalidate();
        reference = manifest = null;
        freshPublication = null;
        freshPublicationGeneration = null;
        repairProof = "idle";
    }
    function retire() {
        if (disposed) return;
        generation++;
        reviewGeneration++;
        confirmed = false;
        review = null;
        eligibility = "unconfirmed";
        owner = null;
        seenResult = null;
        dropProof();
        retain();
    }
    function reconcile() {
        const reviewedOwner = owner;
        if (
            reviewedOwner === null ||
            reviewedOwner.generation !== generation ||
            reviewedOwner.auth !== authGeneration ||
            session.connection !== "connected"
        )
            return;
        const observed = controller.observer.snapshot(reviewedOwner.recordId),
            record = session.registry.records.find(
                (v) => v.recordId === reviewedOwner.recordId,
            );
        const receipt = observed.receipt,
            result = observed.result;
        if (
            observed.phase !== "settled" ||
            !receipt ||
            receipt.state !== "succeeded" ||
            result?.kind !== "success"
        ) {
            if (review !== null) {
                review = null;
                confirmed = false;
                eligibility = "unconfirmed";
                retain();
            }
            return;
        }
        const signature =
            reviewedOwner.recordId + ":" + result.response.request_id;
        if (seenResult === signature) return;
        seenResult = signature;
        try {
            if (
                !record ||
                record.action !== reviewedOwner.action ||
                record.route !== ACTION_ROUTES[reviewedOwner.action] ||
                receipt.route !== record.route ||
                receipt.archive_id !==
                    session.bootstrap.configured_archive_id ||
                result.response.archive_id !== receipt.archive_id ||
                result.response.config_fingerprint !==
                    receipt.config_fingerprint ||
                result.response.envelope.exit_code !== 0 ||
                record.source !== "web" ||
                record.handles.kind !== "basic-key" ||
                record.receiptIdentity?.operation_id !== receipt.operation_id
            )
                refuse("scope");
            if (
                JSON.stringify(
                    buildMaintenanceIntent(reviewedOwner.form).request,
                ) !== reviewedOwner.request
            )
                refuse("scope");
            const parsed = reviewPayload(reviewedOwner.form, result.payload);
            review = parsed.review;
            eligibility = parsed.eligibility;
            if (!retain()) {
                review = null;
                eligibility = "unconfirmed";
                refuse("capacity");
            }
        } catch (error) {
            review = null;
            confirmed = false;
            eligibility = "unconfirmed";
            formIssue =
                error instanceof MaintenanceInputError ? error.reason : "scope";
            notice =
                "The original preview cannot authorize this form. Preserve its operation evidence.";
            retain();
        }
    }
    function revalidateRepairProof() {
        if (repairProof !== "ready") return;
        const ref = reference?.snapshot(),
            doc = manifest?.snapshot();
        let state: MaintenanceSnapshot["repairProof"] = "ready";
        if (
            ref?.phase !== "ready" ||
            ref.result?.kind !== "success" ||
            doc?.phase !== "ready" ||
            doc.result?.kind !== "success"
        )
            state = "unavailable";
        else {
            const a = ref.result.payload.reference,
                b = doc.result.payload.manifest,
                p = freshPublication;
            if (
                p === null ||
                a.repository_type !== p.repositoryType ||
                a.repository_id !== p.repositoryId ||
                a.commit_sha !== p.commitSha ||
                a.publication_id !== p.publicationId ||
                a.publication_generation !== freshPublicationGeneration ||
                b.repository_type !== p.repositoryType ||
                b.repository_id !== p.repositoryId ||
                b.commit_sha !== p.commitSha ||
                b.publication_id !== p.publicationId ||
                b.publication_generation !== freshPublicationGeneration ||
                b.tree !== "published/" + a.tree
            )
                state = "changed";
        }
        if (state !== "ready") {
            repairProof = state;
            confirmed = false;
            reviewGeneration++;
            freshPublication = null;
            freshPublicationGeneration = null;
            retain();
        }
    }
    function publish() {
        if (disposed) return;
        revalidateRepairProof();
        reconcile();
        let valid = true;
        try {
            buildMaintenanceIntent(form, form.kind === "repair", finding);
        } catch {
            valid = false;
        }
        const connected = session.connection === "connected",
            read =
                connected &&
                session.bootstrap.user.rest_capabilities.includes("read"),
            write =
                connected &&
                session.bootstrap.user.rest_capabilities.includes("write"),
            free = pending === null && session.canSubmit;
        const ready =
            form.kind === "repair"
                ? repairProof === "ready" &&
                  freshPublication !== null &&
                  finding !== null
                : review !== null && eligibility === "ready";
        snapshot = Object.freeze({
            connected,
            authGeneration,
            generation,
            form,
            formIssue,
            pending,
            previewRecordId,
            previewObservation:
                previewRecordId === null
                    ? null
                    : controller.observer.snapshot(previewRecordId),
            review,
            reviewGeneration,
            eligibility,
            confirmed,
            canPreview: read && free && valid && form.kind !== "repair",
            canConfirm:
                connected &&
                session.canSubmit &&
                pending === null &&
                ready &&
                !confirmed,
            canApply:
                write && free && ready && confirmed && form.kind !== "repair",
            effectRecordId,
            effectObservation:
                effectRecordId === null
                    ? null
                    : controller.observer.snapshot(effectRecordId),
            effectFinding,
            effectPublication,
            finding,
            repairProof,
            freshPublication,
            freshPublicationGeneration,
            reference: reference?.snapshot() ?? null,
            manifest: manifest?.snapshot() ?? null,
            canCheckRepair:
                read &&
                pending === null &&
                form.kind === "repair" &&
                finding !== null &&
                valid,
            canRepair:
                write && free && ready && confirmed && form.kind === "repair",
            notice,
        });
        for (const listener of listeners) {
            try {
                listener();
            } catch {
                /* Detached views cannot alter original operation evidence. */
            }
        }
    }
    function start(kind: NonNullable<MaintenanceSnapshot["pending"]>) {
        const token = ++taskSerial;
        pendingToken = token;
        pending = kind;
        return token;
    }
    function finish(token: number, auth: number) {
        if (!disposed && authGeneration === auth && pendingToken === token) {
            pending = null;
            pendingToken = null;
            publish();
        }
    }
    function clearPrivate() {
        retire();
        unsubscribePreview();
        unsubscribeEffect();
        previewRecordId = effectRecordId = null;
        finding = effectFinding = null;
        effectPublication = null;
        form = defaultMaintenanceForm();
        formIssue = null;
        pending = null;
        pendingToken = null;
        slot.clear();
        owner = null;
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
            notice =
                "Authentication or connection changed. Original operations remain in recovery.";
        }
        session = next;
        publish();
    });
    function sessionIsCurrent(auth: number): boolean {
        return (
            !disposed &&
            authGeneration === auth &&
            session.connection === "connected"
        );
    }
    function intentIsCurrent(auth: number, intentGeneration: number): boolean {
        return sessionIsCurrent(auth) && generation === intentGeneration;
    }
    async function submitEffect(repair: boolean) {
        if (disposed) return;
        const permitted = repair ? snapshot.canRepair : snapshot.canApply;
        // Capture the reviewed scope before any subscriber can edit local intent.
        const capturedFinding = finding,
            reviewedPublication = freshPublication;
        let intent: MaintenanceIntent | null = null;
        try {
            if (permitted)
                intent = buildMaintenanceIntent(form, true, capturedFinding);
        } catch {
            /* The first attempt still consumes its confirmation below. */
        }
        retire();
        if (!permitted || intent === null) {
            formIssue = "unavailable";
            publish();
            return;
        }
        const ownAuth = authGeneration,
            ownGeneration = generation;
        unsubscribeEffect();
        effectRecordId = null;
        effectFinding = repair ? capturedFinding : null;
        effectPublication = repair ? reviewedPublication : null;
        if (!retain()) {
            effectFinding = null;
            effectPublication = null;
            formIssue = "capacity";
            publish();
            return;
        }
        const token = start("apply");
        formIssue = null;
        notice = null;
        publish();
        try {
            if (!intentIsCurrent(ownAuth, ownGeneration)) return;
            const submitted = await controller.submit(intent);
            if (!sessionIsCurrent(ownAuth)) return;
            effectRecordId = submitted.recordId;
            unsubscribeEffect();
            unsubscribeEffect = controller.observer.subscribe(
                submitted.recordId,
                publish,
            );
            notice =
                "Observe the original result. The server re-evaluates current scope; no request was replayed.";
        } catch {
            if (ownAuth === authGeneration) {
                formIssue = "unavailable";
                notice =
                    "Preserve the original operation handle. No request was replayed.";
            }
        } finally {
            finish(token, ownAuth);
        }
    }
    publish();
    return Object.freeze({
        snapshot: () => snapshot,
        subscribe(listener: () => void) {
            listeners.add(listener);
            return () => {
                listeners.delete(listener);
            };
        },
        setForm(input: unknown): boolean {
            retire();
            if (
                disposed ||
                session.connection !== "connected" ||
                pending !== null
            ) {
                formIssue = "unavailable";
                publish();
                return false;
            }
            const previous = form;
            try {
                form = parseMaintenanceForm(input);
                if (!retain()) {
                    form = previous;
                    refuse("capacity");
                }
                formIssue = null;
                notice = null;
                publish();
                return true;
            } catch (error) {
                form = previous;
                formIssue =
                    error instanceof MaintenanceInputError
                        ? error.reason
                        : "invalid";
                publish();
                return false;
            }
        },
        setRepairFinding(input: RepairFindingIntent): boolean {
            retire();
            if (
                disposed ||
                session.connection !== "connected" ||
                pending !== null
            ) {
                formIssue = "unavailable";
                publish();
                return false;
            }
            const before = { form, finding };
            try {
                const row = object(input, ["source", "finding"]),
                    source = object(row.source, [
                        "archiveId",
                        "runId",
                        "completedAt",
                    ]);
                if (
                    source.archiveId !==
                        session.bootstrap.configured_archive_id ||
                    typeof source.runId !== "string" ||
                    !/^[0-9a-f]{32}$/u.test(source.runId) ||
                    typeof source.completedAt !== "string" ||
                    source.completedAt.length > 64 ||
                    !source.completedAt.endsWith("Z") ||
                    !Number.isFinite(Date.parse(source.completedAt))
                )
                    refuse("scope");
                const checked = wire.decodeFinding(canonical(row.finding));
                if (
                    checked.commit_sha === null ||
                    checked.publication_id === null ||
                    ["ref_invalid", "manifest_invalid"].includes(checked.kind)
                )
                    refuse("scope");
                publicationIdentity({
                    repositoryType: checked.repository_type,
                    repositoryId: checked.repository_id,
                    commitSha: checked.commit_sha,
                    publicationId: checked.publication_id,
                });
                finding = Object.freeze({
                    source: Object.freeze({
                        archiveId: source.archiveId,
                        runId: source.runId,
                        completedAt: source.completedAt,
                    }),
                    finding: checked,
                });
                form =
                    form.kind === "repair"
                        ? form
                        : defaultMaintenanceForm("repair");
                if (!retain()) {
                    ({ form, finding } = before);
                    refuse("capacity");
                }
                formIssue = null;
                notice = null;
                publish();
                return true;
            } catch (error) {
                ({ form, finding } = before);
                formIssue =
                    error instanceof MaintenanceInputError
                        ? error.reason
                        : "scope";
                publish();
                return false;
            }
        },
        async preview() {
            if (disposed) return;
            const permitted = snapshot.canPreview;
            retire();
            if (!permitted) {
                formIssue = "unavailable";
                publish();
                return;
            }
            const ownGen = generation,
                ownAuth = authGeneration,
                captured = form;
            let intent: MaintenanceIntent;
            try {
                intent = buildMaintenanceIntent(captured);
            } catch {
                formIssue = "scope";
                publish();
                return;
            }
            const token = start("preview");
            formIssue = null;
            notice = null;
            publish();
            try {
                if (!intentIsCurrent(ownAuth, ownGen)) return;
                const submitted = await controller.submit(intent);
                if (!sessionIsCurrent(ownAuth)) return;
                previewRecordId = submitted.recordId;
                unsubscribePreview();
                unsubscribePreview = controller.observer.subscribe(
                    submitted.recordId,
                    publish,
                );
                if (generation === ownGen) {
                    owner = {
                        generation: ownGen,
                        auth: ownAuth,
                        kind: captured.kind,
                        form: captured,
                        action: intent.action,
                        request: JSON.stringify(intent.request),
                        recordId: submitted.recordId,
                    };
                    if (!retain()) {
                        owner = null;
                        formIssue = "capacity";
                    }
                }
                if (submitted.result.kind !== "accepted")
                    formIssue = "unavailable";
            } catch {
                if (ownAuth === authGeneration) formIssue = "unavailable";
            } finally {
                finish(token, ownAuth);
            }
        },
        confirm(token: number): boolean {
            if (disposed) return false;
            if (token !== reviewGeneration || !snapshot.canConfirm)
                return false;
            confirmed = true;
            publish();
            return true;
        },
        clearConfirmation() {
            if (disposed) return;
            confirmed = false;
            reviewGeneration++;
            publish();
        },
        apply: () => submitEffect(false),
        repair: () => submitEffect(true),
        async checkRepair() {
            if (disposed) return;
            const permitted = snapshot.canCheckRepair;
            retire();
            if (!permitted || !finding) {
                formIssue = "unavailable";
                publish();
                return;
            }
            const ownGen = generation,
                ownAuth = authGeneration,
                f = finding.finding;
            const commitSha = f.commit_sha,
                publicationId = f.publication_id;
            if (commitSha === null || publicationId === null) {
                formIssue = "scope";
                publish();
                return;
            }
            const target: ExactPublication = {
                repositoryType: f.repository_type,
                repositoryId: f.repository_id,
                commitSha,
                publicationId,
            };
            const token = start("repairProof");
            repairProof = "reading";
            formIssue = null;
            notice = null;
            const api = controller.apiReads;
            const [namespace, name] = repositorySegments(
                target.repositoryType,
                target.repositoryId,
            );
            const own = () =>
                !disposed &&
                generation === ownGen &&
                authGeneration === ownAuth &&
                session.connection === "connected";
            try {
                reference = controller.queries.query(
                    {
                        routeId: "reference_default",
                        path: {
                            repository_type: target.repositoryType,
                            namespace,
                            name,
                            revision: target.commitSha,
                        },
                    },
                    (options) =>
                        api.readReference(
                            target.repositoryType,
                            target.repositoryId,
                            target.commitSha,
                            options,
                        ),
                );
                unsubscribeRef = reference.subscribe(publish);
                publish();
                if (!own()) return;
                await reference.refresh();
                if (!own()) return;
                const first = reference.snapshot();
                if (
                    first.phase !== "ready" ||
                    first.result?.kind !== "success"
                ) {
                    repairProof = "unavailable";
                    return;
                }
                const identity = (ref: ReferencePayload["reference"]) =>
                    JSON.stringify([
                        ref.repository_type,
                        ref.repository_id,
                        ref.commit_sha,
                        ref.publication_id,
                        ref.publication_generation,
                        ref.tree,
                        ref.manifest,
                    ]);
                const ref = first.result.payload.reference;
                if (
                    ref.repository_type !== target.repositoryType ||
                    ref.repository_id !== target.repositoryId ||
                    ref.commit_sha !== target.commitSha ||
                    ref.publication_id !== target.publicationId
                ) {
                    repairProof = "changed";
                    return;
                }
                const binding = identity(ref),
                    expectedGeneration = ref.publication_generation,
                    expectedTree = "published/" + ref.tree;
                manifest = controller.queries.query(
                    {
                        routeId: "manifest_default",
                        publication: target,
                        path: {
                            repository_type: target.repositoryType,
                            namespace,
                            name,
                            commit_sha: target.commitSha,
                            publication_id: target.publicationId,
                        },
                    },
                    (options) => api.readManifest(target, options),
                );
                unsubscribeManifest = manifest.subscribe(publish);
                publish();
                if (!own()) return;
                await manifest.refresh();
                if (!own()) return;
                {
                    const checked = manifest.snapshot();
                    if (
                        checked.phase !== "ready" ||
                        checked.result?.kind !== "success"
                    ) {
                        repairProof = "unavailable";
                        return;
                    }
                    const doc = checked.result.payload.manifest;
                    if (
                        doc.repository_type !== target.repositoryType ||
                        doc.repository_id !== target.repositoryId ||
                        doc.commit_sha !== target.commitSha ||
                        doc.publication_id !== target.publicationId ||
                        doc.publication_generation !== expectedGeneration ||
                        doc.tree !== expectedTree
                    ) {
                        repairProof = "changed";
                        return;
                    }
                }
                await reference.refresh();
                if (!own()) return;
                const last = reference.snapshot();
                if (last.phase !== "ready" || last.result?.kind !== "success") {
                    repairProof = "unavailable";
                    return;
                }
                if (identity(last.result.payload.reference) !== binding) {
                    repairProof = "changed";
                    return;
                }
                freshPublication = Object.freeze(target);
                freshPublicationGeneration = expectedGeneration;
                if (!retain()) {
                    freshPublication = null;
                    freshPublicationGeneration = null;
                    repairProof = "failed";
                    refuse("capacity");
                }
                repairProof = "ready";
            } catch (error) {
                if (own()) {
                    repairProof = "failed";
                    formIssue =
                        error instanceof MaintenanceInputError
                            ? error.reason
                            : "unavailable";
                }
            } finally {
                finish(token, ownAuth);
            }
        },
        reset() {
            if (disposed) return;
            retire();
            if (pending !== null) {
                formIssue = "unavailable";
                publish();
                return;
            }
            clearPrivate();
            retain();
            publish();
        },
        pause() {
            if (disposed) return;
            retire();
            notice =
                "Local confirmation retired. Accepted operations were not cancelled.";
            publish();
        },
        dispose() {
            if (disposed) return;
            clearPrivate();
            disposed = true;
            unsubscribeSession();
            listeners.clear();
            slot.clear();
        },
    });
}
export type MaintenanceStore = ReturnType<typeof createMaintenanceStore>;
