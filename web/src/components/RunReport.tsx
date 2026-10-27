import { useState } from "react";
import type { ReactNode } from "react";
import type { ReportPayload } from "../wire/generated";
import type { RepairFindingIntent } from "../operations/maintenance-state";

/** Local paging replaces rows; it never fetches or implies complete server history. */
export function ReportCollection<T>({
    values,
    name,
    identity,
    render,
}: {
    readonly values: readonly T[];
    readonly name: string;
    readonly identity: string;
    readonly render: (value: T, index: number) => ReactNode;
}) {
    const [position, setPosition] = useState({ identity, index: 0 });
    const page = position.identity === identity ? position.index : 0;
    const start = Math.min(
        page * 25,
        Math.max(0, Math.ceil(values.length / 25) - 1) * 25,
    );
    return (
        <section aria-label={name}>
            <p>
                {values.length === 0
                    ? `No ${name} in this result.`
                    : `Showing ${String(start + 1)}–${String(Math.min(start + 25, values.length))} of ${String(values.length)} loaded ${name}.`}
            </p>
            <ul>
                {values.slice(start, start + 25).map((value, index) => (
                    <li key={start + index}>{render(value, start + index)}</li>
                ))}
            </ul>
            {values.length > 25 && (
                <div>
                    <button
                        type="button"
                        disabled={start === 0}
                        onClick={() => {
                            setPosition({
                                identity,
                                index: Math.max(0, page - 1),
                            });
                        }}
                    >
                        Previous {name}
                    </button>
                    <button
                        type="button"
                        disabled={start + 25 >= values.length}
                        onClick={() => {
                            setPosition({ identity, index: page + 1 });
                        }}
                    >
                        Next {name}
                    </button>
                </div>
            )}
        </section>
    );
}
function Messages({
    values,
    name,
    identity,
}: {
    values: readonly string[];
    name: string;
    identity: string;
}) {
    return (
        <ReportCollection
            values={values}
            name={name}
            identity={identity}
            render={(value) => <span>{value}</span>}
        />
    );
}
export function RunReport({
    report,
    onRepairFinding,
}: {
    readonly report: ReportPayload["report"];
    readonly onRepairFinding?: (intent: RepairFindingIntent) => void;
}) {
    const identity = report.run_id + ":" + report.completed_at;
    return (
        <article aria-label="Run report">
            <h3>Domain run report</h3>
            <dl className="recovery-facts">
                <dt>Domain run ID</dt>
                <dd>
                    <code>{report.run_id}</code>
                </dd>
                <dt>Archive ID</dt>
                <dd>
                    <code>{report.archive_id}</code>
                </dd>
                <dt>Historical configuration fingerprint</dt>
                <dd>
                    <code>{report.config_fingerprint}</code>
                </dd>
                <dt>Command</dt>
                <dd>{report.command}</dd>
                <dt>Outcome</dt>
                <dd>{report.outcome}</dd>
                <dt>Exit code</dt>
                <dd>{report.exit_code}</dd>
                <dt>Started</dt>
                <dd>{report.started_at}</dd>
                <dt>Completed</dt>
                <dd>{report.completed_at}</dd>
            </dl>
            <p>
                This report is historical evidence for its domain run, not
                current archive health or an operation admission receipt.
            </p>
            <Messages
                values={report.errors}
                name="report errors"
                identity={identity}
            />
            <Messages
                values={report.warnings}
                name="report warnings"
                identity={identity}
            />
            {"repositories" in report && (
                <>
                    <dl className="recovery-facts">
                        {Object.entries(report.totals).map(([key, value]) => (
                            <div key={key}>
                                <dt>{key.replaceAll("_", " ")}</dt>
                                <dd>{value} bytes</dd>
                            </div>
                        ))}
                    </dl>
                    <ReportCollection
                        values={report.repositories}
                        name="repository results"
                        identity={identity}
                        render={(row, index) => (
                            <article>
                                <h4>
                                    {row.repository_type} {row.repository_id}
                                </h4>
                                <p>Status: {row.status}.</p>
                                <dl className="recovery-facts">
                                    <dt>Requested revision</dt>
                                    <dd>{row.requested_revision}</dd>
                                    <dt>Resolved commit SHA</dt>
                                    <dd>
                                        {row.resolved_commit_sha ??
                                            "Not resolved"}
                                    </dd>
                                    <dt>Publication ID</dt>
                                    <dd>
                                        {row.publication_id ?? "Not published"}
                                    </dd>
                                    <dt>Publication generation</dt>
                                    <dd>
                                        {row.publication_generation ??
                                            "Not published"}
                                    </dd>
                                    <dt>Files</dt>
                                    <dd>{row.file_count}</dd>
                                    <dt>Downloaded bytes</dt>
                                    <dd>{row.downloaded_bytes}</dd>
                                    <dt>Reused bytes</dt>
                                    <dd>{row.reused_bytes}</dd>
                                    <dt>Hashed bytes</dt>
                                    <dd>{row.hashed_bytes}</dd>
                                    <dt>Duration seconds</dt>
                                    <dd>{row.duration_seconds}</dd>
                                </dl>
                                {row.pruned !== null && (
                                    <p>
                                        Pruned commit {row.pruned.commit_sha},
                                        generation{" "}
                                        {row.pruned.publication_generation}:{" "}
                                        {row.pruned.logical_bytes} logical
                                        bytes.
                                    </p>
                                )}
                                <Messages
                                    values={row.errors}
                                    name="repository errors"
                                    identity={identity + String(index)}
                                />
                                <Messages
                                    values={row.warnings}
                                    name="repository warnings"
                                    identity={identity + String(index)}
                                />
                            </article>
                        )}
                    />
                </>
            )}
            {"findings" in report && (
                <>
                    <h4>Offline verification: {report.verification_outcome}</h4>
                    <p>
                        Mode: {report.mode}. Scope: {report.scope.repositories}{" "}
                        repositories, {report.scope.revisions} revisions;{" "}
                        {report.scope.unique_objects_read} objects and{" "}
                        {report.scope.unique_bytes_read} bytes read.
                    </p>
                    {report.findings.length > 0 && (
                        <p>
                            Integrity findings require review of this exact
                            evidence. No sync, prune or repair is submitted by
                            this view.
                        </p>
                    )}
                    <ReportCollection
                        values={report.findings}
                        name="integrity findings"
                        identity={identity}
                        render={(row) => (
                            <div>
                                <dl className="recovery-facts">
                                    <dt>Repository</dt>
                                    <dd>
                                        {row.repository_type}{" "}
                                        {row.repository_id}
                                    </dd>
                                    <dt>Finding</dt>
                                    <dd>{row.kind}</dd>
                                    <dt>Commit SHA</dt>
                                    <dd>
                                        {row.commit_sha ?? "Not attributed"}
                                    </dd>
                                    <dt>Publication ID</dt>
                                    <dd>
                                        {row.publication_id ?? "Not attributed"}
                                    </dd>
                                    <dt>Path</dt>
                                    <dd>{row.path ?? "Not attributed"}</dd>
                                    <dt>Expected</dt>
                                    <dd>{row.expected ?? "Not available"}</dd>
                                    <dt>Observed</dt>
                                    <dd>{row.observed ?? "Not available"}</dd>
                                </dl>
                                {onRepairFinding !== undefined && (
                                    <button
                                        type="button"
                                        disabled={
                                            row.commit_sha === null ||
                                            row.publication_id === null ||
                                            row.kind === "ref_invalid" ||
                                            row.kind === "manifest_invalid"
                                        }
                                        onClick={() => {
                                            onRepairFinding({
                                                source: {
                                                    archiveId:
                                                        report.archive_id,
                                                    runId: report.run_id,
                                                    completedAt:
                                                        report.completed_at,
                                                },
                                                finding: row,
                                            });
                                        }}
                                    >
                                        Review repair from this finding
                                    </button>
                                )}
                                {(row.commit_sha === null ||
                                    row.publication_id === null ||
                                    row.kind === "ref_invalid" ||
                                    row.kind === "manifest_invalid") && (
                                    <p>
                                        This finding lacks safe exact repair
                                        attribution. Preserve the evidence and
                                        follow the recovery runbook.
                                    </p>
                                )}
                            </div>
                        )}
                    />
                </>
            )}
            {"remediations" in report && (
                <ReportCollection
                    values={report.remediations}
                    name="recovery remediations"
                    identity={identity}
                    render={(row) => (
                        <>
                            <p>
                                Transaction {row.transaction_id}: {row.outcome}{" "}
                                · {row.remedy} · {row.reason}
                            </p>
                            <p>
                                Additional protected evidence is not expanded
                                into management actions.
                            </p>
                        </>
                    )}
                />
            )}
        </article>
    );
}
