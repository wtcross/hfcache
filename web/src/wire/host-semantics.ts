/** Explicit ports of the bounded host reader's nonsecret authority invariants. */
import { WireError } from "./json";
import { isRecord } from "./runtime";

function check(value: boolean): void {
    if (!value) throw new WireError("semantic");
}
function record(value: unknown): Record<string, unknown> {
    if (!isRecord(value)) throw new WireError("semantic");
    return value;
}
const actions = [
    "archive",
    "hub",
    "control",
    "schedule",
    "configuration",
    "observer",
];
const units = [
    "hfcache-sync.service",
    "hfcache-verify.service",
    "hfcache-sync.timer",
    "hfcache-verify.timer",
];

export const hostSemanticIds: readonly string[] = [
    "hfcache.host_models._one",
    "hfcache.host_models._version",
    "hfcache.host_models.HostSyncSchedule.complete_schedule",
    "hfcache.host_models.HostFacts.exact_units",
    "hfcache.host_models.HostStatus.coherent_authority",
];

export function applyHostSemantic(id: string, value: unknown): void {
    switch (id) {
        case "hfcache.host_models._one":
            check(value === 1);
            return;
        case "hfcache.host_models._version":
            check(
                typeof value === "string" &&
                    /[0-9][A-Za-z0-9.+-]*/u.exec(value)?.[0] === value,
            );
            return;
        case "hfcache.host_models.HostSyncSchedule.complete_schedule": {
            const data = record(value);
            const required = [data.revision, data.source, data.on_calendar];
            const all = [...required, data.randomized_delay_sec];
            check(
                (data.state === "observed" &&
                    data.reason === null &&
                    required.every((item) => item !== null)) ||
                    (data.state === "unavailable" &&
                        data.reason !== null &&
                        all.every((item) => item === null)),
            );
            for (const field of [data.on_calendar, data.randomized_delay_sec])
                if (field !== null)
                    check(
                        typeof field === "string" &&
                            /^[\x20-\x7e]+$/u.exec(field)?.[0] === field,
                    );
            return;
        }
        case "hfcache.host_models.HostFacts.exact_units": {
            const keys = Object.keys(record(record(value).units));
            check(
                keys.length === units.length &&
                    units.every((unit) => keys.includes(unit)),
            );
            return;
        }
        case "hfcache.host_models.HostStatus.coherent_authority": {
            const data = record(value);
            const known =
                data.state === "supported" || data.state === "guarded";
            check(
                known === (data.reason === null) &&
                    known === (data.profile !== null) &&
                    known === (data.binding !== null) &&
                    known === (data.facts !== null),
            );
            const permissions = record(data.permissions),
                reasons = record(data.permission_reasons);
            for (const action of actions)
                check(
                    (permissions[action] === true) ===
                        (reasons[action] === "granted") &&
                        (known || permissions[action] === false),
                );
            if (data.profile === "rootless")
                check(
                    permissions.schedule === false &&
                        permissions.observer === false,
                );
            if (data.facts !== null) {
                const held = record(data.facts).guard === "held";
                check(
                    (data.state === "guarded") === held &&
                        (!held || permissions.archive === false),
                );
            }
            return;
        }
        default:
            throw new WireError("semantic");
    }
}
