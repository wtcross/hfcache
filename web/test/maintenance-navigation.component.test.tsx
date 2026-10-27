import { useSyncExternalStore } from "react";
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test } from "vitest";
import { App } from "../src/App";
import { createHistoryStore } from "../src/operations/history-state";
import { createRepositoryStore } from "../src/repository/repository-state";
import { createJobsStore } from "../src/operations/jobs-state";
import {
    setupMaintenance,
    repairFinding,
    manifest,
    reference,
} from "./maintenance-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";
import { ARCHIVE_ID, jsonResponse, statusPayload } from "./read-fixtures";
import { operationResponse } from "./state-fixtures";
import verificationReport from "../../tests/fixtures/schemas/verification-report.json";

const disposals: (() => void)[] = [];
afterEach(() => {
    cleanup();
    disposals
        .splice(0)
        .reverse()
        .forEach((dispose) => {
            dispose();
        });
    window.history.replaceState(null, "", "/ui/");
});
function mounted(path = "/ui/operations") {
    window.history.replaceState(null, "", path);
    const finding = repairFinding();
    const report = { ...verificationReport, findings: [finding.finding] };
    const fixture = setupMaintenance({
        bootstrap: {
            ...uiBootstrapFixture(),
            configured_origin: window.location.origin,
            configured_archive_id: ARCHIVE_ID,
        },
        fetch: (url) => {
            if (url.pathname === "/api/v1/runs")
                return jsonResponse(
                    operationResponse("runs", { runs: [report.run_id] }),
                );
            if (url.pathname === "/api/v1/repositories")
                return jsonResponse(
                    operationResponse("list", {
                        repositories: [
                            {
                                repository_type: reference.repository_type,
                                repository_id: reference.repository_id,
                                enabled: false,
                                managed: true,
                                retained_revisions: 1,
                                current_commit_sha: reference.commit_sha,
                                current_publication_id:
                                    reference.publication_id,
                            },
                        ],
                    }),
                );
            if (url.pathname === "/api/v1/status")
                return jsonResponse(
                    operationResponse("status", statusPayload(true)),
                );
            return url.pathname === "/api/v1/runs/" + report.run_id
                ? jsonResponse({
                      ...operationResponse("runs read", { report }),
                      envelope: {
                          ...operationResponse("runs read", { report })
                              .envelope,
                          run_id: report.run_id,
                      },
                  })
                : undefined;
        },
    });
    const repository = createRepositoryStore(fixture.controller);
    const history = createHistoryStore(fixture.controller),
        jobs = createJobsStore(fixture.controller);
    disposals.push(() => {
        history.dispose();
        repository.dispose();
        jobs.dispose();
        fixture.dispose();
    });
    function Connected() {
        const session = useSyncExternalStore(
            fixture.controller.subscribe,
            fixture.controller.snapshot,
        );
        return (
            <App
                basePath="/ui/"
                bootstrap={session.bootstrap}
                controller={fixture.controller}
                session={session}
                jobs={jobs}
                history={history}
                maintenance={fixture.store}
                repository={repository}
            />
        );
    }
    return {
        ...fixture,
        history,
        repository,
        report,
        ...render(<Connected />),
    };
}

test("an exact run finding navigates through the charged maintenance owner without submitting repair", async () => {
    const fixture = mounted();
    expect(fixture.fetcher).not.toHaveBeenCalled();
    await act(async () => {
        await fixture.history.selectRun(fixture.report.run_id);
    });
    await userEvent.click(
        await screen.findByRole("button", {
            name: "Review repair from this finding",
        }),
    );
    expect(window.location.pathname).toBe("/ui/maintenance");
    const finding = fixture.store.snapshot().finding;
    expect(finding?.source).toEqual({
        archiveId: fixture.report.archive_id,
        runId: fixture.report.run_id,
        completedAt: fixture.report.completed_at,
    });
    expect(finding?.finding).toEqual(fixture.report.findings[0]);
    expect(
        screen.getByRole("region", { name: "Original repair finding" }),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Repair reviewed revision" }),
    ).toBeDisabled();
    expect(
        fixture.requests.filter((request) => request.method === "POST"),
    ).toEqual([]);
    await userEvent.click(
        screen.getByRole("button", { name: "Check repair evidence" }),
    );
    await waitFor(() => {
        expect(fixture.store.snapshot().repairProof).toBe("ready");
    });
    expect(
        screen.getByRole("region", { name: "Fresh repair evidence" }),
    ).toHaveTextContent(finding?.finding.publication_id ?? "missing");
    expect(
        screen.getByText(/not an atomic publication precondition/),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Repair reviewed revision" }),
    ).toBeDisabled();
    expect(
        fixture.requests.filter((request) => request.method === "POST"),
    ).toEqual([]);
});

test("ordinary navigation and repeated Maintenance navigation retire confirmed preview readiness", async () => {
    const fixture = mounted("/ui/maintenance");
    await userEvent.click(
        screen.getByRole("button", { name: "Preview maintenance" }),
    );
    await waitFor(() => {
        expect(fixture.store.snapshot().canConfirm).toBe(true);
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Confirm reviewed maintenance" }),
    );
    expect(fixture.store.snapshot().canApply).toBe(true);
    await userEvent.click(screen.getByRole("link", { name: "Maintenance" }));
    expect(fixture.store.snapshot().canApply).toBe(false);
    expect(fixture.store.snapshot().confirmed).toBe(false);
    await userEvent.click(screen.getByRole("link", { name: "Library" }));
    expect(window.location.pathname).toBe("/ui/library");
    expect(fixture.controller.snapshot().registry.records).toHaveLength(1);
    expect(
        fixture.requests.filter((request) => request.method === "POST"),
    ).toHaveLength(1);
});

test("loaded repository Activity hands its real finding to maintenance and releases the exact manifest query before fresh repair proof", async () => {
    const fixture = mounted(
        "/ui/repositories/model/organization/model-name#tab=activity",
    );
    const openReport = await screen.findByRole("button", {
        name: "Open run report in Operations " + fixture.report.run_id,
    });
    expect(fixture.repository.snapshot().manifest.phase).toBe("ready");
    const bookmark = fixture.repository.snapshot().view;
    expect(bookmark.pair).toEqual({
        commitSha: manifest.commit_sha,
        publicationId: manifest.publication_id,
    });
    await userEvent.click(openReport);
    expect(window.location.pathname).toBe("/ui/operations");
    await userEvent.click(
        await screen.findByRole("button", {
            name: "Review repair from this finding",
        }),
    );
    expect(window.location.pathname).toBe("/ui/maintenance");
    expect(fixture.repository.snapshot().manifest.result).toBeNull();
    expect(fixture.repository.snapshot().view).toEqual(bookmark);
    expect(fixture.store.snapshot().finding?.finding).toEqual(
        fixture.report.findings[0],
    );
    const before = fixture.requests.length;
    await userEvent.click(
        screen.getByRole("button", { name: "Check repair evidence" }),
    );
    await waitFor(() => {
        expect(fixture.store.snapshot().repairProof).toBe("ready");
    });
    const proof = fixture.requests.slice(before);
    expect(proof.map((row) => row.path)).toEqual([
        "/api/v1/repositories/model/organization/model-name/references/" +
            reference.commit_sha,
        "/api/v1/repositories/model/organization/model-name/manifests/" +
            manifest.commit_sha +
            "/" +
            manifest.publication_id,
        "/api/v1/repositories/model/organization/model-name/references/" +
            reference.commit_sha,
    ]);
    expect(proof.every((row) => row.method === "GET")).toBe(true);
    expect(fixture.requests.filter((row) => row.method === "POST")).toEqual([]);
    expect(
        screen.getByRole("region", { name: "Fresh repair evidence" }),
    ).toHaveTextContent(reference.publication_id);
});
