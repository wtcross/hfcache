import {
    useEffect,
    useMemo,
    useRef,
    useState,
    useSyncExternalStore,
} from "react";
import type { RecoveryRecord } from "../state/operation-registry";
import type {
    HostActionOutcomeObservation,
    SessionController,
} from "../state/session-controller";

function OutcomeObservation({
    controller,
    record,
    canRead,
}: {
    controller: SessionController;
    record: RecoveryRecord;
    canRead: boolean;
}) {
    const slot = useMemo(() => controller.createPrivateSlot(), [controller]);
    const alive = useRef(true);
    const [pending, setPending] = useState(false);
    const [observation, setObservation] =
        useState<HostActionOutcomeObservation | null>(null);
    const [message, setMessage] = useState<string | null>(null);
    useEffect(() => {
        alive.current = true;
        return () => {
            alive.current = false;
            slot.clear();
        };
    }, [slot]);
    async function observe() {
        if (!canRead || pending) return;
        setObservation(null);
        slot.clear();
        setMessage(null);
        setPending(true);
        try {
            const result = await controller.observeHostActionOutcome(
                record.recordId,
            );
            if (!alive.current) return;
            if (slot.set(result)) setObservation(result);
            else
                setMessage(
                    "Browser read capacity is unavailable. Protected effects remain unconfirmed; preserve the original handles.",
                );
        } catch {
            if (alive.current)
                setMessage(
                    "The original host outcome is unavailable for the current authority. Preserve the original handles; no write was retried.",
                );
        } finally {
            if (alive.current) setPending(false);
        }
    }
    const result = observation?.result;
    const outcome =
        observation?.kind === "outcome" && observation.result.kind === "success"
            ? observation.result.payload
            : null;
    return (
        <section aria-label="Original host outcome">
            <button
                type="button"
                disabled={!canRead || pending}
                onClick={() => {
                    void observe();
                }}
            >
                Observe original host outcome
            </button>
            <p>
                Read the original subject and key, then its protected host
                outcome. API receipt state, stored schedule, manager
                acknowledgement and observer exit are separate evidence. This
                never resubmits a schedule change or observer stop.
            </p>
            {pending && <p role="status">Reading original host outcome.</p>}
            {message !== null && <p role="status">{message}</p>}
            {result !== undefined && (
                <p>
                    Host outcome read: {result.kind}.
                    {result.kind === "api_problem" &&
                        ` Diagnostic code: ${result.problem.code}.`}
                    {observation?.kind === "lookup" &&
                        " Original subject/key lookup has not established a protected outcome. Missing history does not prove nonexecution."}
                </p>
            )}
            {observation?.kind === "outcome" && (
                <p>Original API receipt state: {observation.receipt.state}.</p>
            )}
            {outcome !== null && (
                <>
                    <dl className="recovery-facts">
                        <dt>Protected host outcome</dt>
                        <dd>{outcome.state}</dd>
                        <dt>Pending protected work</dt>
                        <dd>{outcome.pending ? "Yes" : "No"}</dd>
                        <dt>Original operation ID</dt>
                        <dd>
                            <code>{outcome.operation_id}</code>
                        </dd>
                        {"file_state" in outcome && (
                            <>
                                <dt>Stored schedule file</dt>
                                <dd>{outcome.file_state}</dd>
                                <dt>Manager acknowledgement</dt>
                                <dd>{outcome.manager_state}</dd>
                            </>
                        )}
                        {"stop_state" in outcome && (
                            <>
                                <dt>Original observer stop evidence</dt>
                                <dd>{outcome.stop_state}</dd>
                            </>
                        )}
                    </dl>
                    <p>
                        {outcome.pending ||
                        (outcome.state !== "confirmed" &&
                            outcome.state !== "unchanged")
                            ? "Protected effects remain unresolved. Preserve original handles and evidence; do not repeat the request."
                            : outcome.state === "unchanged"
                              ? "This original request is known unchanged. The requested host change is not confirmed."
                              : "The protected host outcome is confirmed. The original API receipt is unchanged; accepted backend work has its own outcome."}
                    </p>
                </>
            )}
        </section>
    );
}

/** RAM-only, charged original-outcome evidence is retired on auth or connection drift. */
export function HostActionRecovery({
    controller,
    record,
}: {
    controller: SessionController;
    record: RecoveryRecord;
}) {
    const session = useSyncExternalStore(
        controller.subscribe,
        controller.snapshot,
    );
    const canRead =
        session.connection === "connected" &&
        session.bootstrap.user.admin_permissions.some(
            (permission) =>
                permission.capability === "host-read" && permission.effective,
        );
    return (
        <OutcomeObservation
            key={String(session.generation) + ":" + session.connection}
            controller={controller}
            record={record}
            canRead={canRead}
        />
    );
}
