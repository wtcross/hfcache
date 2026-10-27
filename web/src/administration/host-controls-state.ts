/** INV021/022, ADR145/156: bounded RAM intent; only the controller sends effects. */
import type { ReadResult } from "../api/types";
import type { QueryHandle, QuerySnapshot } from "../state/query-state";
import type { ObservationSnapshot } from "../state/operation-observation";
import type {
    HostActionOutcomeObservation,
    SessionController,
    SubmissionIntent,
} from "../state/session-controller";
import type {
    EmptyPayload,
    HostJournalPage,
    HostObserverStatus,
    HostStatus,
    ObserverExpected,
    RequestScheduleChangeRequest,
    ScheduleValidation,
} from "../wire/generated";

export const JOURNAL_PAGE_SIZE = 25;
export const MAX_JOURNAL_PAGES = 32;
export type JournalSource = HostJournalPage["source"];
type ScheduleAction = RequestScheduleChangeRequest["action"];
type HostQuery = QuerySnapshot<HostStatus, EmptyPayload>;
type ObserverQuery = QuerySnapshot<HostObserverStatus, EmptyPayload>;
type JournalQuery = QuerySnapshot<HostJournalPage, EmptyPayload>;
type ValidationResult = ReadResult<ScheduleValidation, EmptyPayload>;
interface ScheduleReview {
    readonly action: ScheduleAction;
    readonly request: RequestScheduleChangeRequest;
    readonly authority: string;
}
interface ObserverReview {
    readonly expected: ObserverExpected;
    readonly authority: string;
}
export interface HostControlsSnapshot {
    readonly active: boolean;
    readonly dirty: boolean;
    readonly editing: boolean;
    readonly draft: { readonly calendar: string; readonly delay: string };
    readonly pending: "read" | "validation" | "submit" | "outcome" | null;
    readonly host: HostQuery | null;
    readonly observer: ObserverQuery | null;
    readonly validation: ValidationResult | null;
    readonly scheduleReview: ScheduleReview | null;
    readonly scheduleConfirmed: boolean;
    readonly observerReview: ObserverReview | null;
    readonly observerConfirmed: boolean;
    readonly recordId: string | null;
    readonly operation: ObservationSnapshot | null;
    readonly outcome: HostActionOutcomeObservation | null;
    readonly journalSource: JournalSource;
    readonly journal: JournalQuery | null;
    readonly journalPage: number;
    readonly canRead: boolean;
    readonly canSchedule: boolean;
    readonly canValidate: boolean;
    readonly canApply: boolean;
    readonly canReviewObserver: boolean;
    readonly canStop: boolean;
    readonly canPreviousJournal: boolean;
    readonly canNextJournal: boolean;
    readonly notice: string | null;
}

function safeLine(value: string, maximum: number): boolean {
    if (
        value.length > maximum ||
        value.trim().length === 0 ||
        value.includes("\\")
    )
        return false;
    for (let i = 0; i < value.length; i++) {
        if (value.charCodeAt(i) < 32 || value.charCodeAt(i) > 126) return false;
    }
    return true;
}

export function createHostControlsStore(controller: SessionController) {
    let session = controller.snapshot();
    let auth = session.generation;
    let active = false;
    let disposed = false;
    let epoch = 0;
    let editing = false;
    let draft: HostControlsSnapshot["draft"] = Object.freeze({
        calendar: "",
        delay: "",
    });
    let pending: HostControlsSnapshot["pending"] = null;
    let notice: string | null = null;
    let host: HostQuery | null = null;
    let observer: ObserverQuery | null = null;
    let validation: ValidationResult | null = null;
    let validatedAuthority: string | null = null;
    let scheduleReview: ScheduleReview | null = null;
    let scheduleConfirmed = false;
    let observerReview: ObserverReview | null = null;
    let observerConfirmed = false;
    let recordId: string | null = null;
    let operation: ObservationSnapshot | null = null;
    let outcome: HostActionOutcomeObservation | null = null;
    let source: JournalSource = "sync-observer";
    let journal: JournalQuery | null = null;
    let cursors: (string | null)[] = [null];
    let page = 0;
    let abort: AbortController | null = null;
    let observerHandle: QueryHandle<HostObserverStatus, EmptyPayload> | null =
        null;
    let journalHandle: QueryHandle<HostJournalPage, EmptyPayload> | null = null;
    let unsubscribeHost = () => {};
    let unsubscribeObserver = () => {};
    let unsubscribeJournal = () => {};
    let unsubscribeOperation = () => {};
    let slot = controller.createPrivateSlot();
    const listeners = new Set<() => void>();
    let snapshot: HostControlsSnapshot;
    const permitted = (
        capability: "host-read" | "schedule-write" | "observer-stop",
    ) =>
        !disposed &&
        active &&
        session.connection === "connected" &&
        session.bootstrap.user.admin_permissions.some(
            (p) => p.capability === capability && p.effective,
        );
    function current(ownAuth: number) {
        return (
            !disposed && ownAuth === auth && session.connection === "connected"
        );
    }
    function currentView(ownAuth: number) {
        return active && current(ownAuth);
    }
    function hostPayload() {
        return host?.phase === "ready" && host.result?.kind === "success"
            ? host.result.payload
            : null;
    }
    function observerPayload() {
        return observer?.phase === "ready" &&
            observer.result?.kind === "success"
            ? observer.result.payload
            : null;
    }
    function authority(): string | null {
        const h = hostPayload(),
            o = observerPayload();
        if (
            !h?.binding ||
            !o?.host_binding ||
            JSON.stringify(h.binding) !== JSON.stringify(o.host_binding)
        )
            return null;
        return JSON.stringify([
            auth,
            h.binding,
            h.permissions,
            h.facts,
            o.permissions,
            o.state,
            o.expected,
        ]);
    }
    function scheduleAllowed() {
        return (
            permitted("schedule-write") &&
            hostPayload()?.facts?.sync_schedule.state === "observed" &&
            hostPayload()?.facts?.sync_schedule.revision !== null &&
            observerPayload()?.permissions.schedule === true &&
            authority() !== null
        );
    }
    function observerAllowed() {
        const value = observerPayload();
        return (
            permitted("observer-stop") &&
            value?.permissions.observer === true &&
            value.state === "observed" &&
            value.expected !== null
        );
    }
    function retire() {
        epoch++;
        abort?.abort();
        abort = null;
        validation = null;
        validatedAuthority = null;
        scheduleReview = null;
        scheduleConfirmed = false;
        observerReview = null;
        observerConfirmed = false;
        if (pending === "validation") pending = null;
    }
    function publish() {
        if (disposed) return;
        if (
            session.connection === "connected" &&
            !slot.set({
                draft,
                editing,
                validation,
                scheduleReview,
                observerReview,
                outcome,
                cursors,
            })
        ) {
            retire();
            editing = false;
            draft = Object.freeze({ calendar: "", delay: "" });
            outcome = null;
            cursors = [null];
            page = 0;
            slot.clear();
            notice =
                "Browser capacity is unavailable. Review original handles; no submission was retried.";
        }
        const canRead = permitted("host-read");
        const available = pending === null;
        const currentAuthority = authority();
        snapshot = Object.freeze({
            active,
            dirty: editing,
            editing,
            draft,
            pending,
            host,
            observer,
            validation,
            scheduleReview,
            scheduleConfirmed,
            observerReview,
            observerConfirmed,
            recordId,
            operation,
            outcome,
            journalSource: source,
            journal,
            journalPage: page + 1,
            canRead,
            canSchedule: canRead && available && scheduleAllowed(),
            canValidate:
                canRead &&
                available &&
                editing &&
                scheduleAllowed() &&
                safeLine(draft.calendar, 4096) &&
                (draft.delay === "" || safeLine(draft.delay, 256)),
            canApply:
                available &&
                session.canSubmit &&
                scheduleAllowed() &&
                scheduleReview !== null &&
                scheduleConfirmed &&
                scheduleReview.authority === currentAuthority,
            canReviewObserver: canRead && available && observerAllowed(),
            canStop:
                available &&
                session.canSubmit &&
                observerAllowed() &&
                observerReview !== null &&
                observerConfirmed &&
                observerReview.authority === observerAuthority(),
            canPreviousJournal:
                canRead && page > 0 && journal?.phase !== "loading",
            canNextJournal:
                canRead &&
                page + 1 < MAX_JOURNAL_PAGES &&
                journal?.phase === "ready" &&
                journal.result?.kind === "success" &&
                journal.result.payload.next_cursor !== null,
            notice,
        });
        for (const listener of listeners) {
            try {
                listener();
            } catch {
                /* Detached views cannot strand work. */
            }
        }
    }
    function observerAuthority(): string | null {
        const o = observerPayload();
        return o?.host_binding
            ? JSON.stringify([
                  auth,
                  o.host_binding,
                  o.permissions,
                  o.state,
                  o.expected,
              ])
            : null;
    }
    function authorityChanged() {
        if (
            (validatedAuthority !== null &&
                validatedAuthority !== authority()) ||
            (scheduleReview !== null &&
                scheduleReview.authority !== authority()) ||
            (observerReview !== null &&
                observerReview.authority !== observerAuthority())
        ) {
            retire();
            notice =
                "Host authority or the original revision changed. Read and review again before a new action.";
        }
        publish();
    }
    function bindHost() {
        unsubscribeHost();
        unsubscribeObserver();
        const h = controller.hostStatus;
        host = h.snapshot();
        unsubscribeHost = h.subscribe(() => {
            if (active) {
                host = h.snapshot();
                authorityChanged();
            }
        });
        const api = controller.apiReads;
        observerHandle ??= controller.queries.query(
            { routeId: "host_observer_default" },
            (options) => api.readHostObserver(options),
        );
        const o = observerHandle;
        observer = o.snapshot();
        unsubscribeObserver = o.subscribe(() => {
            if (active) {
                observer = o.snapshot();
                authorityChanged();
            }
        });
    }
    function releaseReads() {
        unsubscribeHost();
        unsubscribeObserver();
        unsubscribeJournal();
        unsubscribeOperation();
        observerHandle?.invalidate();
        journalHandle?.invalidate();
        journalHandle = null;
        host = observer = journal = null;
        operation = null;
    }
    function clear() {
        retire();
        releaseReads();
        observerHandle = null;
        draft = Object.freeze({ calendar: "", delay: "" });
        editing = false;
        recordId = null;
        outcome = null;
        cursors = [null];
        page = 0;
        pending = null;
        slot.clear();
    }
    function followOperation() {
        unsubscribeOperation();
        if (recordId === null || !active) return;
        const id = recordId;
        operation = controller.observer.snapshot(id);
        unsubscribeOperation = controller.observer.subscribe(id, () => {
            if (!disposed && active && recordId === id) {
                operation = controller.observer.snapshot(id);
                publish();
            }
        });
    }
    async function submit(
        intent: Extract<
            SubmissionIntent,
            { readonly action: "scheduleChange" | "observerStop" }
        >,
    ) {
        const ownAuth = auth;
        retire();
        const ownEpoch = epoch;
        editing = false;
        pending = "submit";
        outcome = null;
        notice = null;
        publish();
        try {
            if (!currentView(ownAuth) || ownEpoch !== epoch) return;
            const submitted = await controller.submit(intent);
            if (
                disposed ||
                ownAuth !== auth ||
                session.connection !== "connected"
            )
                return;
            recordId = submitted.recordId;
            followOperation();
            controller.hostStatus.invalidate();
            observerHandle?.invalidate();
            notice =
                "Admission is separate from the host effect. Observe the original host outcome; no replacement request will be sent.";
        } catch {
            if (ownAuth === auth)
                notice =
                    "Submission was refused or is uncertain. Preserve original handles and review recovery; nothing was retried.";
        } finally {
            if (ownAuth === auth && !disposed) {
                pending = null;
                publish();
            }
        }
    }
    async function loadJournal(index: number) {
        if (!permitted("host-read") || journal?.phase === "loading") return;
        unsubscribeJournal();
        journalHandle?.invalidate();
        const api = controller.apiReads,
            selected = source,
            ownAuth = auth;
        const query = {
            source: selected,
            limit: JOURNAL_PAGE_SIZE,
            ...(cursors[index] === null ? {} : { cursor: cursors[index] }),
        };
        const handle = controller.queries.query(
            { routeId: "host_journal_default", predicates: query },
            (options) => api.readHostJournal(query, options),
        );
        journalHandle = handle;
        page = index;
        journal = handle.snapshot();
        unsubscribeJournal = handle.subscribe(() => {
            if (active && ownAuth === auth && journalHandle === handle) {
                journal = handle.snapshot();
                publish();
            }
        });
        publish();
        if (!currentView(ownAuth) || journalHandle !== handle) return;
        await handle.refresh();
        if (currentView(ownAuth) && journalHandle === handle) {
            journal = handle.snapshot();
            if (journal.result?.kind !== "success")
                notice =
                    "Journal page unavailable or cursor expired. Read the first page explicitly; logs never settle an operation.";
            else if (
                page + 1 === MAX_JOURNAL_PAGES &&
                journal.result.payload.next_cursor !== null
            )
                notice =
                    "Journal page limit reached. Start a new bounded read explicitly.";
            publish();
        }
    }
    const unsubscribeSession = controller.subscribe(() => {
        const next = controller.snapshot();
        if (next.generation !== auth || next.connection !== "connected") {
            clear();
            auth = next.generation;
            slot = controller.createPrivateSlot();
            notice =
                "Authentication or connection changed. Host drafts and confirmations were cleared; original handles remain in recovery.";
        }
        session = next;
        if (active && session.connection === "connected" && host === null)
            bindHost();
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
        setPageActive(value: boolean) {
            if (disposed || active === value) return;
            active = value;
            if (active && session.connection === "connected") {
                bindHost();
                followOperation();
            } else {
                retire();
                releaseReads();
            }
            publish();
        },
        async readHost() {
            if (!permitted("host-read") || pending !== null) return;
            retire();
            const ownAuth = auth,
                ownEpoch = epoch;
            pending = "read";
            notice = null;
            bindHost();
            publish();
            try {
                if (!currentView(ownAuth) || ownEpoch !== epoch) return;
                await Promise.all([
                    controller.hostStatus.refresh(),
                    observerHandle?.refresh(),
                ]);
            } finally {
                if (ownAuth === auth && !disposed) {
                    pending = null;
                    publish();
                }
            }
        },
        edit() {
            if (disposed || !snapshot.canSchedule) return;
            retire();
            const value = hostPayload()?.facts?.sync_schedule;
            draft = Object.freeze({
                calendar: value?.on_calendar ?? "",
                delay: value?.randomized_delay_sec ?? "",
            });
            editing = true;
            notice = null;
            publish();
        },
        setDraft(field: "calendar" | "delay", value: string) {
            if (
                !active ||
                session.connection !== "connected" ||
                !editing ||
                pending === "submit"
            )
                return;
            retire();
            notice = null;
            if (value.length <= (field === "calendar" ? 4096 : 256))
                draft = Object.freeze({ ...draft, [field]: value });
            else
                notice =
                    "The input exceeds the bounded calendar or delay field. Validation was retired.";
            publish();
        },
        discard() {
            retire();
            editing = false;
            draft = Object.freeze({ calendar: "", delay: "" });
            notice = null;
            publish();
        },
        async validate() {
            if (disposed || !snapshot.canValidate) return;
            retire();
            const ownEpoch = epoch,
                ownAuth = auth,
                key = authority();
            const request = {
                on_calendar: draft.calendar,
                randomized_delay_sec: draft.delay === "" ? null : draft.delay,
            };
            const controlled = new AbortController();
            abort = controlled;
            pending = "validation";
            notice = null;
            publish();
            try {
                if (!currentView(ownAuth) || ownEpoch !== epoch) return;
                const result = await controller.validateSchedule(request, {
                    signal: controlled.signal,
                });
                if (
                    !currentView(ownAuth) ||
                    ownEpoch !== epoch ||
                    key !== authority()
                )
                    return;
                validation = result;
                if (
                    result.kind === "success" &&
                    result.payload.on_calendar === request.on_calendar &&
                    result.payload.randomized_delay_sec ===
                        request.randomized_delay_sec
                )
                    validatedAuthority = key;
                else
                    notice =
                        "Schedule validation was unavailable or refused. No change is ready.";
            } catch {
                if (ownEpoch === epoch)
                    notice =
                        "Schedule validation was refused. No change is ready.";
            } finally {
                if (ownEpoch === epoch && current(ownAuth)) {
                    abort = null;
                    pending = null;
                    publish();
                }
            }
        },
        reviewSchedule(action: ScheduleAction) {
            if (disposed || !snapshot.canSchedule) return;
            const key = authority(),
                revision = hostPayload()?.facts?.sync_schedule.revision;
            if (
                !key ||
                !revision ||
                (action === "replace" &&
                    (!editing ||
                        validation?.kind !== "success" ||
                        validatedAuthority !== key))
            )
                return;
            scheduleReview = Object.freeze({
                action,
                authority: key,
                request: Object.freeze({
                    action,
                    expected_revision: revision,
                    ...(action === "replace"
                        ? {
                              on_calendar: draft.calendar,
                              randomized_delay_sec:
                                  draft.delay === "" ? null : draft.delay,
                          }
                        : {}),
                }),
            });
            scheduleConfirmed = false;
            observerReview = null;
            observerConfirmed = false;
            publish();
        },
        confirmSchedule(value: boolean) {
            scheduleConfirmed = scheduleReview !== null && value;
            publish();
        },
        async applySchedule() {
            if (!disposed && snapshot.canApply && scheduleReview)
                await submit({
                    action: "scheduleChange",
                    request: scheduleReview.request,
                });
        },
        reviewObserver() {
            if (disposed || !snapshot.canReviewObserver) return;
            const expected = observerPayload()?.expected,
                key = observerAuthority();
            if (!expected || !key) return;
            retire();
            observerReview = Object.freeze({
                authority: key,
                expected: Object.freeze({ ...expected }),
            });
            publish();
        },
        confirmObserver(value: boolean) {
            observerConfirmed = observerReview !== null && value;
            publish();
        },
        async stopObserver() {
            if (!disposed && snapshot.canStop && observerReview)
                await submit({
                    action: "observerStop",
                    request: { expected: observerReview.expected },
                });
        },
        async observeOutcome() {
            if (!snapshot.canRead || recordId === null || pending !== null)
                return;
            const ownAuth = auth,
                id = recordId;
            pending = "outcome";
            publish();
            try {
                const result = await controller.observeHostActionOutcome(id);
                if (
                    !disposed &&
                    active &&
                    ownAuth === auth &&
                    recordId === id
                ) {
                    outcome = result;
                    notice =
                        result.kind === "outcome" &&
                        result.result.kind === "success"
                            ? result.result.payload.pending ||
                              !["confirmed", "unchanged"].includes(
                                  result.result.payload.state,
                              )
                                ? "The original host effect remains unresolved. Preserve its original handles; do not retry the action."
                                : result.result.payload.state === "unchanged"
                                  ? "stored_revision" in
                                        result.result.payload &&
                                    result.result.payload.stored_revision !==
                                        result.result.payload.expected_revision
                                      ? "Expected schedule revision conflict. The original request is known unchanged; read the current schedule and review a new intent."
                                      : "The original host action is known unchanged. This is a refusal, not the requested effect; read and review a new intent explicitly."
                                  : "The original host effect is confirmed. Its API receipt and current host observations remain separate."
                            : "The original host outcome is unavailable. Missing history does not prove nonexecution.";
                }
            } catch {
                if (ownAuth === auth)
                    notice =
                        "Original host outcome unavailable. Preserve the original handles; no action was replayed.";
            } finally {
                if (!disposed && ownAuth === auth) {
                    pending = null;
                    publish();
                }
            }
        },
        setJournalSource(value: JournalSource) {
            if (disposed || source === value) return;
            unsubscribeJournal();
            journalHandle?.invalidate();
            journalHandle = null;
            journal = null;
            source = value;
            cursors = [null];
            page = 0;
            notice = null;
            publish();
        },
        async readJournal() {
            if (!snapshot.canRead || journal?.phase === "loading") return;
            cursors = [null];
            await loadJournal(0);
        },
        async previousJournal() {
            if (snapshot.canPreviousJournal) await loadJournal(page - 1);
        },
        async nextJournal() {
            if (!snapshot.canNextJournal || journal?.result?.kind !== "success")
                return;
            const cursor = journal.result.payload.next_cursor;
            if (cursor === null) return;
            cursors = [...cursors.slice(0, page + 1), cursor];
            await loadJournal(page + 1);
        },
        dispose() {
            clear();
            active = false;
            publish();
            slot.clear();
            disposed = true;
            unsubscribeSession();
            listeners.clear();
        },
    });
}

export type HostControlsStore = ReturnType<typeof createHostControlsStore>;
