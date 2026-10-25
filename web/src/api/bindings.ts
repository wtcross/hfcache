/** Request/response bindings beyond the Pydantic object invariants. */
import type {
    ClientOperation,
    ClientProblem,
    ClientRead,
} from "../wire/generated";
import { WireError } from "../wire/json";
import { isRecord } from "../wire/runtime";
import {
    validateCatalogRead,
    validateCatalogRefresh,
} from "../wire/catalog-semantics";

function check(value: boolean): void {
    if (!value) throw new WireError("semantic");
}
function record(value: unknown): Record<string, unknown> {
    if (!isRecord(value)) throw new WireError("semantic");
    return value;
}
function array(value: unknown): readonly unknown[] {
    if (!Array.isArray(value)) throw new WireError("semantic");
    const result: unknown[] = value;
    return result;
}
function text(value: unknown): string {
    if (typeof value !== "string") throw new WireError("semantic");
    return value;
}
function number(value: unknown): number {
    if (typeof value !== "number" || !Number.isSafeInteger(value))
        throw new WireError("semantic");
    return value;
}

export const contextSemanticIds: readonly string[] = [
    "api.problem.classification",
    "catalog.facet",
    "catalog.publication",
    "catalog.response",
    "host.status",
    "operation.events",
    "operation.identity",
    "operation.result",
    "publication.manifest",
    "publication.reference",
    "run.report",
];

const classifications: Readonly<Record<string, number>> = {
    HFCFG: 10,
    HFARG: 10,
    HFAPI: 10,
    HFMNT: 20,
    HFTXN: 20,
    HFHUB: 30,
    HFSYN: 30,
    HFVER: 40,
    HFRET: 50,
    HFWRN: 0,
    HFDEP: 0,
};
const apiSafety = new Set([
    "HFAPI005",
    "HFAPI008",
    "HFAPI009",
    "HFAPI011",
    "HFAPI013",
    "HFAPI014",
    "HFAPI015",
    "HFAPI016",
    "HFAPI019",
    "HFAPI020",
    "HFAPI021",
    "HFAPI022",
]);
export function validateApiProblem(problem: ClientProblem): void {
    // Families remain extensible; an individual known-code enum would reject valid future diagnostics.
    check(
        problem.code.length === 8 && /^[0-9]{3}$/u.test(problem.code.slice(5)),
    );
    const classification = apiSafety.has(problem.code)
        ? 20
        : classifications[problem.code.slice(0, 5)];
    check(
        classification !== undefined &&
            classification !== 0 &&
            classification === problem.exit_code,
    );
}

export interface RequestBinding {
    readonly repositoryType?: "model" | "dataset";
    readonly repositoryId?: string;
    readonly commitSha?: string;
    readonly publicationId?: string;
    readonly revision?: string;
    readonly runId?: string;
    readonly operationId?: string;
    readonly operation?: ClientOperation;
    readonly after?: number;
    readonly limit?: number;
    readonly facet?: string;
}

function publicTree(
    type: unknown,
    repository: unknown,
    sha: unknown,
    publication: unknown,
): string {
    return `repos/${type === "model" ? "models" : "datasets"}/${text(repository)}/revisions/${text(sha)}/${text(publication)}`;
}

export function applyBindings(
    ids: readonly string[],
    response: ClientRead,
    context: RequestBinding,
): void {
    for (const id of ids) {
        const payload = response.envelope.data;
        switch (id) {
            case "host.status": {
                if (response.envelope.exit_code !== 0) break;
                const binding = payload.binding;
                check(
                    binding === null ||
                        record(binding).archive_id === response.archive_id,
                );
                break;
            }
            case "catalog.response":
            case "catalog.facet":
            case "catalog.publication":
                validateCatalogRead(response, {
                    command: response.envelope.command,
                    ...context,
                });
                break;
            case "run.report": {
                if (response.envelope.exit_code !== 0) break;
                const report = record(payload.report),
                    command = text(report.command);
                check(
                    response.envelope.run_id === context.runId &&
                        report.run_id === context.runId &&
                        report.archive_id === response.archive_id,
                );
                if (command.startsWith("verify"))
                    check(Object.hasOwn(report, "verification_outcome"));
                else if (command.startsWith("recover"))
                    check(Object.hasOwn(report, "remediations"));
                else
                    check(
                        !Object.hasOwn(report, "verification_outcome") &&
                            !Object.hasOwn(report, "remediations"),
                    );
                break;
            }
            case "publication.reference": {
                if (response.envelope.exit_code !== 0) break;
                const ref = record(payload.reference);
                check(
                    ref.repository_type === context.repositoryType &&
                        ref.repository_id === context.repositoryId &&
                        (context.revision === "current" ||
                            ref.commit_sha === context.revision),
                );
                const tree = publicTree(
                    ref.repository_type,
                    ref.repository_id,
                    ref.commit_sha,
                    ref.publication_id,
                );
                const manifest = `manifests/${ref.repository_type === "model" ? "models" : "datasets"}/${text(ref.repository_id)}/${text(ref.commit_sha)}/${text(ref.publication_id)}.json`;
                check(
                    payload.locator_base === "published/" &&
                        ref.tree === tree &&
                        ref.manifest === manifest,
                );
                break;
            }
            case "publication.manifest": {
                if (response.envelope.exit_code !== 0) break;
                const manifest = record(payload.manifest);
                check(
                    payload.tree_base === "archive-root/" &&
                        manifest.repository_type === context.repositoryType &&
                        manifest.repository_id === context.repositoryId &&
                        manifest.commit_sha === context.commitSha &&
                        manifest.publication_id === context.publicationId,
                );
                check(
                    manifest.tree ===
                        "published/" +
                            publicTree(
                                manifest.repository_type,
                                manifest.repository_id,
                                manifest.commit_sha,
                                manifest.publication_id,
                            ),
                );
                break;
            }
            case "operation.identity": {
                if (response.envelope.exit_code !== 0) break;
                const operation = record(payload.operation);
                check(
                    (context.operationId === undefined ||
                        operation.operation_id === context.operationId) &&
                        operation.archive_id === response.archive_id &&
                        operation.config_fingerprint ===
                            response.config_fingerprint,
                );
                break;
            }
            case "operation.events": {
                if (response.envelope.exit_code !== 0) break;
                const operation = context.operation;
                if (operation === undefined) throw new WireError("semantic");
                const events = array(payload.events).map(record),
                    after = context.after ?? 0,
                    oldest = number(payload.oldest_sequence);
                const sequences = events.map((item) => number(item.sequence));
                check(
                    payload.operation_id === operation.operation_id &&
                        events.length <= (context.limit ?? 100) &&
                        response.archive_id === operation.archive_id &&
                        response.config_fingerprint ===
                            operation.config_fingerprint,
                );
                check(
                    payload.next_cursor === (sequences.at(-1) ?? after) &&
                        payload.truncated === after < oldest - 1,
                );
                if (sequences.length > 0)
                    check(sequences[0] === Math.max(after + 1, oldest));
                check(
                    sequences.every(
                        (sequence, index) =>
                            sequence > after &&
                            (index === 0 ||
                                sequence ===
                                    (sequences[index - 1] ?? sequence) + 1),
                    ),
                );
                break;
            }
            case "operation.result": {
                const operation = context.operation;
                if (operation === undefined) throw new WireError("semantic");
                check(
                    response.archive_id === operation.archive_id &&
                        response.config_fingerprint ===
                            operation.config_fingerprint &&
                        response.envelope.run_id === operation.domain_run_id,
                );
                check(
                    (operation.state === "succeeded") ===
                        (response.envelope.exit_code === 0),
                );
                if (response.envelope.command === "catalog refresh")
                    validateCatalogRefresh(response);
                break;
            }
            default:
                throw new WireError("semantic");
        }
    }
}

export function validateOperationTransition(
    old: ClientOperation | undefined,
    next: ClientOperation,
): void {
    if (old === undefined) return;
    const ranks: Readonly<Record<ClientOperation["state"], number>> = {
        queued: 0,
        waiting_lock: 1,
        running: 2,
        succeeded: 3,
        failed: 3,
        interrupted: 3,
    };
    // Inputs already passed canonical timestamp reconstruction; pad the optional
    // fraction to compare the original microseconds without Date rounding.
    function receiptTime(value: string): string {
        const fraction = value.slice(19, -1);
        return (
            value.slice(0, 19) +
            "." +
            (fraction.startsWith(".") ? fraction.slice(1) : "").padEnd(6, "0")
        );
    }
    check(
        old.operation_id === next.operation_id &&
            old.created_at === next.created_at &&
            ranks[next.state] >= ranks[old.state] &&
            receiptTime(next.updated_at) >= receiptTime(old.updated_at),
    );
    check(
        old.archive_id === next.archive_id &&
            old.config_fingerprint === next.config_fingerprint &&
            old.route === next.route &&
            old.principal === next.principal,
    );
    check(
        old.domain_run_id === null || old.domain_run_id === next.domain_run_id,
    );
    check(
        old.transaction_ids.every(
            (item, index) => next.transaction_ids[index] === item,
        ),
    );
    if (["succeeded", "failed", "interrupted"].includes(old.state))
        check(JSON.stringify(old) === JSON.stringify(next));
}
