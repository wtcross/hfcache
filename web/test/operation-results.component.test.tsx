import { afterEach, expect, test, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import runReportFixture from "../../tests/fixtures/schemas/run-report.json";
import verificationReportFixture from "../../tests/fixtures/schemas/verification-report.json";
import { isRecord } from "../src/wire/runtime";
import { classifyOperationResult } from "../src/operations/history-state";
import { ApiClient } from "../src/api/client";
import { OperationResult } from "../src/components/OperationResult";
import { RunReport } from "../src/components/RunReport";
import { decodeReportPayload } from "../src/wire/generated";
import type { ReportPayload } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { jsonResponse, ARCHIVE_ID } from "./read-fixtures";
import { operationResponse, receipt, scope } from "./state-fixtures";

afterEach(cleanup);
function golden(name: string): Record<string, unknown> {
    const parsed: unknown = JSON.parse(
        JSON.stringify(
            name === "run-report"
                ? runReportFixture
                : verificationReportFixture,
        ),
    );
    if (!isRecord(parsed)) throw new Error("Invalid owned fixture");
    return parsed;
}
function report(change: Record<string, unknown> = {}): ReportPayload["report"] {
    return decodeReportPayload(
        parseWireJson(
            JSON.stringify({ report: { ...golden("run-report"), ...change } }),
        ),
    ).report;
}
async function result(
    command: string,
    data: unknown,
    exit = 0,
    code = "HFARG001",
    warning = false,
) {
    const response = operationResponse(command, data, exit !== 0);
    const value = {
        ...response,
        envelope: {
            ...response.envelope,
            exit_code: exit,
            outcome:
                exit !== 0
                    ? "failed"
                    : warning
                      ? "success_with_warnings"
                      : "success",
            errors:
                exit === 0
                    ? []
                    : [
                          {
                              code,
                              message: "Independent preserved diagnostic",
                              repository: null,
                              context: {},
                          },
                      ],
            warnings: warning
                ? [
                      {
                          code: "HFWRN001",
                          message: "Independent preserved warning",
                          repository: null,
                          context: {},
                      },
                  ]
                : [],
        },
    };
    const original = receipt({
        route:
            command === "doctor"
                ? "/api/v1/diagnostics"
                : command === "plan"
                  ? "/api/v1/plans"
                  : "/api/v1/syncs",
        state: exit === 0 ? "succeeded" : "failed",
        updated_at: "2026-10-20T12:00:03.000000Z",
        result_recorded: true,
        completed_at: "2026-10-20T12:00:02.000000Z",
    });
    const fetcher = vi.fn<typeof fetch>(() =>
        Promise.resolve(jsonResponse(value)),
    );
    return {
        value: await new ApiClient({ scope, fetcher }).readOperationResult(
            original,
        ),
        original,
        fetcher,
    };
}

test.each([
    [10, "validation"],
    [20, "preflight"],
    [30, "partial"],
    [40, "integrity"],
    [50, "unsupported"],
] as const)(
    "HTTP200 failed Envelope exit%s preserves its independent domain class",
    async (exit, classification) => {
        const actual = await result("sync", {}, exit);
        expect(actual.value.kind).toBe("domain_failure");
        expect(classifyOperationResult(actual.value)).toBe(classification);
        render(
            <OperationResult
                result={actual.value}
                operation={actual.original}
            />,
        );
        expect(screen.getByText("HFARG001")).toBeInTheDocument();
        expect(
            screen.getByText(/Independent preserved diagnostic/),
        ).toBeInTheDocument();
        expect(screen.getByText(String(exit))).toBeInTheDocument();
        expect(
            screen.queryByRole("button", {
                name: /cancel|retry|sync|prune|repair/i,
            }),
        ).not.toBeInTheDocument();
    },
);

test("HFMNT010 is explicitly benign busy even when delivered as a failed domain envelope", async () => {
    const actual = await result("sync", {}, 20, "HFMNT010");
    expect(classifyOperationResult(actual.value)).toBe("busy");
    render(<OperationResult result={actual.value} />);
    expect(
        screen.getByText(/Busy: the archive operation lock was held/),
    ).toBeInTheDocument();
    expect(screen.getByText("HFMNT010")).toBeInTheDocument();
});

test("a queued receipt without a stored result is uncertainty, with no completion or byte percentage", () => {
    render(
        <OperationResult
            result={null}
            operation={receipt({ state: "queued", domain_run_id: null })}
        />,
    );
    expect(screen.getByText("queued")).toBeInTheDocument();
    expect(screen.getByText(/does not prove nonexecution/)).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(
        screen.queryByText(/completed successfully/),
    ).not.toBeInTheDocument();
});

test("404, protocol and transport failures remain unknown and never print untrusted problem messages", () => {
    const { rerender } = render(
        <OperationResult
            result={{
                kind: "api_problem",
                status: 404,
                problem: {
                    request_id: "1".repeat(32),
                    code: "HFAPI003",
                    exit_code: 10,
                    message: "<script>private detail</script>",
                },
            }}
        />,
    );
    expect(screen.getByText(/HFAPI003/)).toBeInTheDocument();
    expect(screen.queryByText(/private detail/)).not.toBeInTheDocument();
    rerender(
        <OperationResult
            result={{ kind: "protocol_failure", reason: "bounds" }}
        />,
    );
    expect(screen.getByText(/Protocol reason: bounds/)).toBeInTheDocument();
    rerender(
        <OperationResult
            result={{ kind: "transport_failure", reason: "timeout" }}
        />,
    );
    expect(screen.getByText(/transport_failure/)).toBeInTheDocument();
    expect(screen.getByText(/Do not resubmit/)).toBeInTheDocument();
});

test("warnings and full diagnostics remain useful without inventing a report or mutating", async () => {
    const actual = await result(
        "doctor",
        {
            checks: [
                {
                    name: "archive",
                    outcome: "pass",
                    detail: "<img src=x onerror=alert(1)>literal",
                },
            ],
        },
        0,
        "HFARG001",
        true,
    );
    expect(actual.value.kind).toBe("success");
    expect(classifyOperationResult(actual.value)).toBe("warning");
    render(
        <OperationResult result={actual.value} operation={actual.original} />,
    );
    expect(screen.getByText("HFWRN001")).toBeInTheDocument();
    await userEvent.click(screen.getByText("result evidence: 1 loaded fields"));
    await userEvent.click(screen.getByText("checks: 1 loaded entries"));
    await userEvent.click(screen.getByText("1: 3 loaded fields"));
    expect(
        screen.getByText("<img src=x onerror=alert(1)>literal"),
    ).toBeInTheDocument();
    expect(document.querySelector("img")).toBe(null);
    expect(actual.fetcher).toHaveBeenCalledTimes(1);
});

test("report navigation uses exact domain run ID, kept separate from request and operation admission IDs", async () => {
    const actual = await result("plan", { repositories: [] });
    const open = vi.fn();
    render(
        <OperationResult
            result={actual.value}
            operation={actual.original}
            onReadReport={open}
        />,
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Read domain run report" }),
    );
    expect(open).toHaveBeenCalledExactlyOnceWith("3".repeat(32));
    expect(actual.fetcher).toHaveBeenCalledTimes(1);
    expect(screen.getByText(actual.original.operation_id)).toBeInTheDocument();
    expect(screen.getByText("1".repeat(32))).toBeInTheDocument();
});

test("sync partial report keeps successful and failed repositories, with25 rows and separately paged warnings", async () => {
    const base = runReportFixture.repositories[0];
    const value = report({
        outcome: "failed",
        exit_code: 30,
        repositories: Array.from({ length: 30 }, (_, n) => ({
            ...base,
            repository_id: "owned/entry" + String(n).padStart(2, "0"),
            status: n === 29 ? "failed" : "published",
            errors: n === 29 ? ["HFHUB001: failed original"] : [],
            warnings:
                n === 0
                    ? Array.from(
                          { length: 27 },
                          (_, i) => "warning" + String(i),
                      )
                    : [],
        })),
    });
    render(<RunReport report={value} />);
    const rows = screen.getByRole("region", { name: "repository results" });
    expect(within(rows).getAllByRole("heading", { level: 4 })).toHaveLength(25);
    expect(screen.queryByText("model owned/entry29")).not.toBeInTheDocument();
    const warnings = screen.getAllByRole("region", {
        name: "repository warnings",
    })[0];
    if (warnings === undefined)
        throw new Error("Expected first repository warning region");
    expect(within(warnings).getAllByRole("listitem")).toHaveLength(25);
    await userEvent.click(
        within(warnings).getByRole("button", {
            name: "Next repository warnings",
        }),
    );
    expect(screen.getByText("warning26")).toBeInTheDocument();
    await userEvent.click(
        screen.getByRole("button", { name: "Next repository results" }),
    );
    expect(screen.getByText("model owned/entry29")).toBeInTheDocument();
    expect(screen.getByText("HFHUB001: failed original")).toBeInTheDocument();
    expect(within(rows).getAllByRole("heading", { level: 4 })).toHaveLength(5);
});

test("verification findings retain exact publication and raw metadata as text, with bounded paging and no healing claim", async () => {
    const source = golden("verification-report");
    const row = verificationReportFixture.findings[0] ?? {
        repository_type: "model",
        repository_id: "owned/model",
        kind: "digest_mismatch",
        commit_sha: "a".repeat(40),
        publication_id: "b".repeat(32),
        path: "weights.bin",
        expected: "c".repeat(64),
        observed: "d".repeat(64),
    };
    const value = decodeReportPayload(
        parseWireJson(
            JSON.stringify({
                report: {
                    ...source,
                    findings: Array.from({ length: 26 }, (_, n) => ({
                        ...row,
                        path:
                            n === 25
                                ? "z-<script>finding</script>"
                                : "file" + String(n).padStart(2, "0"),
                    })),
                },
            }),
        ),
    ).report;
    render(<RunReport report={value} />);
    const findings = screen.getByRole("region", { name: "integrity findings" });
    expect(within(findings).getAllByRole("listitem")).toHaveLength(25);
    await userEvent.click(
        screen.getByRole("button", { name: "Next integrity findings" }),
    );
    expect(screen.getByText("z-<script>finding</script>")).toBeInTheDocument();
    expect(document.querySelector("script")).toBe(null);
    expect(
        screen.getByText(/No sync, prune or repair is submitted/),
    ).toBeInTheDocument();
});

test("changing domain report resets local repository paging and never labels historical policy current", async () => {
    const base = runReportFixture.repositories[0];
    const first = report({
        repositories: Array.from({ length: 26 }, (_, n) => ({
            ...base,
            repository_id: "owned/first" + String(n).padStart(2, "0"),
        })),
    });
    const { rerender } = render(<RunReport report={first} />);
    await userEvent.click(
        screen.getByRole("button", { name: "Next repository results" }),
    );
    expect(screen.getByText("model owned/first25")).toBeInTheDocument();
    rerender(
        <RunReport
            report={report({
                run_id: "f".repeat(32),
                repositories: [{ ...base, repository_id: "owned/fresh" }],
            })}
        />,
    );
    expect(screen.getByText("model owned/fresh")).toBeInTheDocument();
    expect(screen.queryByText("model owned/first25")).not.toBeInTheDocument();
    expect(
        screen.getByText("Historical configuration fingerprint"),
    ).toBeInTheDocument();
});

test("recovery reports bound remediations and preserve blocked outcomes without replay controls", async () => {
    const base = golden("run-report");
    delete base.repositories;
    delete base.totals;
    const value = decodeReportPayload(
        parseWireJson(
            JSON.stringify({
                report: {
                    ...base,
                    command: "recover",
                    remediations: Array.from({ length: 26 }, (_, n) => ({
                        evidence: {},
                        outcome: "blocked",
                        reason: "original evidence",
                        remedy: "preserve",
                        transaction_id: n.toString(16).padStart(32, "0"),
                    })),
                },
            }),
        ),
    ).report;
    render(<RunReport report={value} />);
    expect(
        within(
            screen.getByRole("region", { name: "recovery remediations" }),
        ).getAllByRole("listitem"),
    ).toHaveLength(25);
    await userEvent.click(
        screen.getByRole("button", { name: "Next recovery remediations" }),
    );
    expect(screen.getByText(/blocked · preserve/)).toBeInTheDocument();
    expect(
        screen.queryByRole("button", { name: /retry|apply|cancel/ }),
    ).not.toBeInTheDocument();
    expect(screen.getByText(ARCHIVE_ID)).toBeInTheDocument();
});

test("report distinguishes unresolved publication facts from zero and permits bounded return to earlier diagnostics", async () => {
    const base = runReportFixture.repositories[0];
    const value = report({
        repositories: [
            {
                ...base,
                repository_id: "owned/disabled",
                status: "disabled",
                resolved_commit_sha: null,
                publication_id: null,
                publication_generation: null,
                file_count: 0,
            },
            {
                ...base,
                repository_id: "owned/published",
                publication_generation: 2,
                pruned: {
                    commit_sha: "b".repeat(40),
                    publication_generation: 1,
                    logical_bytes: 99,
                },
            },
        ],
        errors: Array.from(
            { length: 26 },
            (_, n) => "retained-error-" + String(n),
        ),
    });
    render(<RunReport report={value} />);
    expect(screen.getByText("Not resolved")).toBeInTheDocument();
    expect(screen.getAllByText("Not published")).toHaveLength(2);
    expect(
        screen.getByText(/Pruned commit .*99 logical bytes/),
    ).toBeInTheDocument();
    await userEvent.click(
        screen.getByRole("button", { name: "Next report errors" }),
    );
    expect(screen.getByText("retained-error-25")).toBeInTheDocument();
    await userEvent.click(
        screen.getByRole("button", { name: "Previous report errors" }),
    );
    expect(screen.getByText("retained-error-0")).toBeInTheDocument();
    expect(screen.queryByText("retained-error-25")).not.toBeInTheDocument();
});

test("sizing preserves unknown quantities and disabled entries rather than manufacturing zero-byte success", async () => {
    const actual = await result("plan", {
        repositories: [
            {
                enabled: false,
                estimated_new_bytes: null,
                file_count: null,
                logical_bytes: null,
                projected_publication_bytes: null,
                publication_mode: "copy",
                repository_id: "owned/disabled",
                repository_type: "dataset",
                requested_revision: "main",
                resolved_commit_sha: null,
                upstream_state: "unknown",
            },
        ],
    });
    expect(actual.value.kind).toBe("success");
    render(<OperationResult result={actual.value} />);
    await userEvent.click(screen.getByText("result evidence: 1 loaded fields"));
    await userEvent.click(screen.getByText("repositories: 1 loaded entries"));
    await userEvent.click(screen.getByText("1: 11 loaded fields"));
    expect(screen.getByText("false")).toBeInTheDocument();
    expect(screen.getAllByText("Not available")).toHaveLength(5);
    expect(screen.getByText("unknown")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
});

test("an exact decoded verification finding hands off its original report attribution without submitting repair", async () => {
    const value = decodeReportPayload(
        parseWireJson(JSON.stringify({ report: verificationReportFixture })),
    ).report;
    const review = vi.fn();
    render(<RunReport report={value} onRepairFinding={review} />);
    expect(review).not.toHaveBeenCalled();
    await userEvent.click(
        screen.getByRole("button", { name: "Review repair from this finding" }),
    );
    expect(review).toHaveBeenCalledExactlyOnceWith({
        source: {
            archiveId: value.archive_id,
            runId: value.run_id,
            completedAt: value.completed_at,
        },
        finding: verificationReportFixture.findings[0],
    });
    expect(
        screen.queryByRole("button", { name: "Repair reviewed revision" }),
    ).not.toBeInTheDocument();
});

test.each(["ref_invalid", "manifest_invalid"] as const)(
    "%s findings remain evidence without a direct repair handoff",
    async (kind) => {
        const value = decodeReportPayload(
            parseWireJson(
                JSON.stringify({
                    report: {
                        ...verificationReportFixture,
                        findings: [
                            { ...verificationReportFixture.findings[0], kind },
                        ],
                    },
                }),
            ),
        ).report;
        const review = vi.fn();
        render(<RunReport report={value} onRepairFinding={review} />);
        const button = screen.getByRole("button", {
            name: "Review repair from this finding",
        });
        expect(button).toBeDisabled();
        await userEvent.click(button);
        expect(review).not.toHaveBeenCalled();
        expect(
            screen.getByText(/lacks safe exact repair attribution/),
        ).toBeInTheDocument();
    },
);

test("unattributed findings cannot become a blind revision repair form", () => {
    const value = decodeReportPayload(
        parseWireJson(
            JSON.stringify({
                report: {
                    ...verificationReportFixture,
                    findings: [
                        {
                            ...verificationReportFixture.findings[0],
                            commit_sha: null,
                            publication_id: null,
                            path: null,
                            kind: "ref_invalid",
                        },
                    ],
                },
            }),
        ),
    ).report;
    render(<RunReport report={value} onRepairFinding={vi.fn()} />);
    expect(
        screen.getByRole("button", { name: "Review repair from this finding" }),
    ).toBeDisabled();
    expect(screen.getAllByText("Not attributed")).toHaveLength(3);
});
