/** Explicit ports of schemas18.7's closed host-action evidence invariants. */
import { WireError } from "./json";
import { isRecord } from "./runtime";

function check(value: boolean): void {
    if (!value) throw new WireError("semantic");
}
function record(value: unknown): Record<string, unknown> {
    if (!isRecord(value)) throw new WireError("semantic");
    return value;
}
const events = new Set([
    "run.started",
    "preflight.failed",
    "repository.resolved",
    "repository.queued",
    "repository.skipped",
    "download.started",
    "download.completed",
    "hash.started",
    "hash.completed",
    "verification.completed",
    "dependency.undeclared",
    "publication.completed",
    "retention.pruned",
    "retention.deferred",
    "quarantine.cleaned",
    "repository.failed",
    "run.completed",
    "mcp.diagnostic",
    "catalog.capture_incomplete",
]);
const prefix = "hfcache.host_actions_models.";
export const hostActionSemanticIds: readonly string[] = [
    "hfcache.host_actions_models._printable",
    "hfcache.host_actions_models._schedule_text",
    "hfcache.host_actions_models._journal_message",
    "hfcache.host_actions_models.ScheduleValidation.coherent_delay",
    "hfcache.host_actions_models.ScheduleChangeRequest.exact_action",
    "hfcache.host_actions_models.HostObserverStatus.coherent_authority",
    "hfcache.host_actions_models.ScheduleChangeOutcome.coherent_effect",
    "hfcache.host_actions_models.ObserverStopOutcome.coherent_effect",
    "hfcache.host_actions_models.HostJournalPage.bounded_page",
];

export function applyHostActionSemantic(id: string, value: unknown): void {
    switch (id.slice(prefix.length)) {
        case "_printable":
        case "_schedule_text":
        case "_journal_message": {
            check(
                typeof value === "string" &&
                    /^[\x20-\x7e]+$/u.exec(value)?.[0] === value,
            );
            if (typeof value !== "string") throw new WireError("semantic");
            if (id === prefix + "_schedule_text")
                check(value.trim().length > 0 && !value.includes("\\"));
            if (id === prefix + "_journal_message") {
                const match =
                    /^event=([a-z][a-z0-9_.-]{0,63}) level=(debug|info|warning|error|critical) run_id=([0-9a-f]{32})$/u.exec(
                        value,
                    );
                check(match?.[0] === value && events.has(match[1] ?? ""));
            }
            return;
        }
        case "ScheduleValidation.coherent_delay": {
            const data = record(value);
            check(
                (data.randomized_delay_sec === null) ===
                    (data.normalized_randomized_delay_sec === null),
            );
            return;
        }
        case "ScheduleChangeRequest.exact_action": {
            const data = record(value),
                keys = Object.keys(data);
            const fields =
                data.action === "replace"
                    ? [
                          "action",
                          "expected_revision",
                          "on_calendar",
                          "randomized_delay_sec",
                      ]
                    : ["action", "expected_revision"];
            check(
                keys.length === fields.length &&
                    fields.every((field) => Object.hasOwn(data, field)) &&
                    (data.action !== "replace" || data.on_calendar !== null),
            );
            return;
        }
        case "HostObserverStatus.coherent_authority": {
            const data = record(value),
                permissions = record(data.permissions),
                reasons = record(data.permission_reasons);
            check((data.profile === null) === (data.host_binding === null));
            if (data.host_binding !== null)
                check(record(data.host_binding).archive_id === data.archive_id);
            const known =
                data.state === "observed" || data.state === "inactive";
            if (known)
                check(
                    data.profile === "native" &&
                        data.host_binding !== null &&
                        data.reason === null &&
                        (data.expected !== null) ===
                            (data.state === "observed"),
                );
            else check(data.reason !== null && data.expected === null);
            for (const name of ["schedule", "observer"])
                check(
                    (permissions[name] === true) ===
                        (reasons[name] === "granted") &&
                        (known || permissions[name] === false),
                );
            if (data.profile === "rootless")
                check(
                    data.state === "unavailable" &&
                        data.reason === "profile-unproved" &&
                        reasons.schedule === "profile-unproved" &&
                        reasons.observer === "profile-unproved",
                );
            return;
        }
        case "ScheduleChangeOutcome.coherent_effect": {
            const data = record(value);
            if (data.state !== "unknown")
                check(
                    [
                        data.action,
                        data.expected_revision,
                        data.stored_revision,
                    ].every((item) => item !== null),
                );
            check((data.action === null) === (data.expected_revision === null));
            if (data.action === null)
                check(
                    [
                        data.stored_revision,
                        data.timer_was_active,
                        data.timer_is_active,
                    ].every((item) => item === null),
                );
            if (data.state === "prepared" || data.state === "unchanged")
                check(
                    data.file_state === "unchanged" &&
                        data.manager_state === "not_sent" &&
                        (data.state !== "prepared" ||
                            (data.pending === true &&
                                data.expected_revision ===
                                    data.stored_revision)) &&
                        (data.state !== "unchanged" ||
                            (data.pending === false &&
                                data.timer_was_active !== null &&
                                data.timer_is_active ===
                                    data.timer_was_active)),
                );
            if (data.state === "confirmed") {
                check(
                    data.timer_was_active !== null &&
                        data.timer_is_active !== null,
                );
                if (data.action === "pause" || data.action === "resume")
                    check(
                        data.file_state === "unchanged" &&
                            data.expected_revision === data.stored_revision &&
                            data.manager_state === "timer_acknowledged" &&
                            data.timer_is_active === (data.action === "resume"),
                    );
                else
                    check(
                        (data.action === "replace"
                            ? data.file_state === "installed"
                            : data.file_state === "removed" ||
                              data.file_state === "unchanged") &&
                            data.timer_is_active === data.timer_was_active &&
                            data.manager_state ===
                                (data.timer_was_active === true
                                    ? "timer_acknowledged"
                                    : "reload_acknowledged"),
                    );
            }
            return;
        }
        case "ObserverStopOutcome.coherent_effect": {
            const data = record(value);
            check(
                (data.state === "unknown" || data.expected !== null) &&
                    (data.state !== "confirmed" ||
                        data.stop_state === "exit_confirmed"),
            );
            if (data.state === "prepared" || data.state === "unchanged")
                check(
                    data.stop_state === "not_sent" &&
                        (data.state !== "prepared" || data.pending === true),
                );
            return;
        }
        case "HostJournalPage.bounded_page": {
            const data = record(value);
            if (!Array.isArray(data.entries)) throw new WireError("semantic");
            let bytes = 0;
            for (const entry of data.entries) {
                const message = record(entry).message;
                if (typeof message !== "string")
                    throw new WireError("semantic");
                bytes += new TextEncoder().encode(message).length;
            }
            check(
                bytes <= 65536 &&
                    new TextEncoder().encode(JSON.stringify(data)).length <=
                        524288,
            );
            return;
        }
        default:
            throw new WireError("semantic");
    }
}
