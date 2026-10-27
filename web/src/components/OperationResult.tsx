import { useState } from "react";
import type { OriginalResultRead } from "../state/operation-observation";
import type { ClientOperation, ReportPayload } from "../wire/generated";
import { ReportCollection, RunReport } from "./RunReport";

import { classifyOperationResult } from "../operations/history-state";
import type { ResultClassification } from "../operations/history-state";
import { isRecord } from "../wire/runtime";

const guidance: Record<ResultClassification, string> = {
    success:
        "The original command completed successfully. This result does not establish current archive health.",
    warning:
        "The original command completed with warnings. Review the preserved warnings and repository outcomes.",
    busy: "Busy: the archive operation lock was held. This is a benign busy refusal, not an integrity failure. Nothing is retried automatically.",
    validation:
        "The original command refused configuration, input or permission. Review its diagnostic codes before making a new explicit intent.",
    preflight:
        "The original command failed a preflight or environment check. Accepted admission does not prove execution readiness.",
    partial:
        "The original command has a partial or repository failure. Successful repository results remain useful; failed entries are not hidden.",
    integrity:
        "Integrity evidence requires review of the exact findings. Do not infer healing or blindly sync, prune or repair.",
    unsupported:
        "The original command encountered an unsupported or unknown format. Existing evidence must be preserved.",
    failed: "The original command failed. Preserve its original handles and diagnostic codes.",
    unknown:
        "The original result is unavailable or unconfirmed. Missing history, an interrupted observer or a refused read does not prove nonexecution. Do not resubmit to recover it.",
};
/** Already decoded data only. Nested collections expand explicitly and never fetch. */
function Data({
    value,
    name,
    identity,
    depth = 0,
}: {
    readonly value: unknown;
    readonly name: string;
    readonly identity: string;
    readonly depth?: number;
}) {
    const [open, setOpen] = useState(false);
    if (value === null) return <span>Not available</span>;
    if (
        typeof value === "string" ||
        typeof value === "number" ||
        typeof value === "boolean"
    )
        return <span>{String(value)}</span>;
    if (depth >= 8)
        return <span>Nested evidence exceeds this view's display depth.</span>;
    const array: readonly unknown[] | null = Array.isArray(value)
        ? value
        : null;
    const object = isRecord(value) ? value : null;
    const fields = object === null ? [] : Object.keys(object);
    const count = array?.length ?? fields.length;
    return (
        <details
            open={open}
            onToggle={(event) => {
                setOpen(event.currentTarget.open);
            }}
        >
            <summary>
                {name}: {count} loaded {array === null ? "fields" : "entries"}
            </summary>
            {open &&
                (array !== null ? (
                    <ReportCollection
                        values={array}
                        name={name}
                        identity={identity}
                        render={(member, index) => (
                            <>
                                <strong>{index + 1}: </strong>
                                <Data
                                    value={member}
                                    name={String(index + 1)}
                                    identity={identity + ":" + String(index)}
                                    depth={depth + 1}
                                />
                            </>
                        )}
                    />
                ) : (
                    <ReportCollection
                        values={fields}
                        name={name}
                        identity={identity}
                        render={(key) => (
                            <>
                                <strong>{key.replaceAll("_", " ")}: </strong>
                                <Data
                                    value={object?.[key]}
                                    name={key.replaceAll("_", " ")}
                                    identity={identity + ":" + key}
                                    depth={depth + 1}
                                />
                            </>
                        )}
                    />
                ))}
        </details>
    );
}
function embeddedReport(value: unknown): value is ReportPayload["report"] {
    return (
        value !== null &&
        typeof value === "object" &&
        "run_id" in value &&
        "command" in value &&
        "archive_id" in value &&
        "config_fingerprint" in value &&
        "errors" in value &&
        "warnings" in value &&
        "exit_code" in value &&
        ("repositories" in value || "findings" in value)
    );
}
export function OperationResult({
    result,
    operation,
    onReadReport,
}: {
    readonly result: OriginalResultRead | null;
    readonly operation?: ClientOperation;
    readonly onReadReport?: (runId: string) => void;
}) {
    const classification = classifyOperationResult(result);
    const available =
        result?.kind === "success" || result?.kind === "domain_failure";
    const response = available ? result.response : null;
    const value = available ? result.payload : null;
    const report = embeddedReport(value) ? value : null;
    return (
        <section aria-label="Original operation result">
            <h3>Original command result</h3>
            {operation !== undefined && (
                <dl className="recovery-facts">
                    <dt>Operation admission ID</dt>
                    <dd>
                        <code>{operation.operation_id}</code>
                    </dd>
                    <dt>Backend receipt state</dt>
                    <dd>{operation.state}</dd>
                    <dt>Domain run ID from receipt</dt>
                    <dd>{operation.domain_run_id ?? "Not assigned"}</dd>
                </dl>
            )}
            <p role={classification === "unknown" ? "status" : undefined}>
                {guidance[classification]}
            </p>
            {result !== null && !available && (
                <p>
                    Read classification: {result.kind}.
                    {result.kind === "api_problem"
                        ? ` Diagnostic code: ${result.problem.code}.`
                        : ""}
                    {result.kind === "protocol_failure"
                        ? ` Protocol reason: ${result.reason}.`
                        : ""}
                </p>
            )}
            {response !== null && (
                <>
                    <dl className="recovery-facts">
                        <dt>Request ID</dt>
                        <dd>
                            <code>{response.request_id}</code>
                        </dd>
                        <dt>Domain run ID</dt>
                        <dd>
                            <code>{response.envelope.run_id}</code>
                        </dd>
                        <dt>Command</dt>
                        <dd>{response.envelope.command}</dd>
                        <dt>Domain outcome</dt>
                        <dd>{response.envelope.outcome}</dd>
                        <dt>Exit code</dt>
                        <dd>{response.envelope.exit_code}</dd>
                    </dl>
                    <ReportCollection
                        values={response.envelope.errors}
                        name="command errors"
                        identity={response.request_id}
                        render={(row) => (
                            <p>
                                <strong>{row.code}</strong>: {row.message}
                                {row.repository === null
                                    ? ""
                                    : ` · ${row.repository}`}
                            </p>
                        )}
                    />
                    <ReportCollection
                        values={response.envelope.warnings}
                        name="command warnings"
                        identity={response.request_id}
                        render={(row) => (
                            <p>
                                <strong>{row.code}</strong>: {row.message}
                                {row.repository === null
                                    ? ""
                                    : ` · ${row.repository}`}
                            </p>
                        )}
                    />
                    {onReadReport !== undefined && (
                        <button
                            type="button"
                            onClick={() => {
                                onReadReport(response.envelope.run_id);
                            }}
                        >
                            Read domain run report
                        </button>
                    )}
                    {report !== null ? (
                        <RunReport report={report} />
                    ) : (
                        <Data
                            key={response.request_id}
                            value={value}
                            name="result evidence"
                            identity={response.request_id}
                        />
                    )}
                </>
            )}
        </section>
    );
}
