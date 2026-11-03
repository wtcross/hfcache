/** Component/controller boundary fixtures; installed domain acceptance runs separately. */
import { useSyncExternalStore } from "react";
import {
    act,
    cleanup,
    render,
    screen,
    waitFor,
    within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test } from "vitest";
import { MaintenanceWorkspace } from "../src/components/MaintenanceWorkspace";
import {
    setupMaintenance,
    prunePayload,
    purgePayload,
    recoveryPayload,
    quarantinePayload,
    repairFinding,
} from "./maintenance-fixtures";

const disposals: (() => void)[] = [];
afterEach(() => {
    cleanup();
    disposals
        .splice(0)
        .reverse()
        .forEach((dispose) => {
            dispose();
        });
    window.localStorage.clear();
});
function mounted(options?: Parameters<typeof setupMaintenance>[0]) {
    const fixture = setupMaintenance(options);
    disposals.push(() => {
        fixture.dispose();
    });
    function Connected() {
        const session = useSyncExternalStore(
            fixture.controller.subscribe,
            fixture.controller.snapshot,
        );
        return (
            <MaintenanceWorkspace
                store={fixture.store}
                controller={fixture.controller}
                session={session}
            />
        );
    }
    return { ...fixture, ...render(<Connected />) };
}
async function choose(label: string) {
    await userEvent.click(
        screen.getByRole("button", { name: /^Maintenance action:/ }),
    );
    await userEvent.click(
        within(
            screen.getByRole("listbox", { name: "Maintenance action" }),
        ).getByRole("option", { name: label }),
    );
}
function posts(fixture: ReturnType<typeof mounted>) {
    return fixture.fetcher.mock.calls.filter(
        ([, init]) => init?.method === "POST",
    );
}
async function previewReady(fixture: ReturnType<typeof mounted>) {
    await userEvent.click(
        screen.getByRole("button", { name: "Preview maintenance" }),
    );
    await waitFor(() => {
        const state = fixture.store.snapshot();
        expect(
            state.canConfirm,
            JSON.stringify({
                phase: state.previewObservation?.phase,
                failure: state.previewObservation?.failure,
                pauseReason: state.previewObservation?.pauseReason,
                issue: state.formIssue,
                requests: fixture.requests.map(({ method, path }) => ({
                    method,
                    path,
                })),
            }),
        ).toBe(true);
    });
    expect(
        screen.getByRole("button", { name: "Apply maintenance" }),
    ).toBeDisabled();
}

test("maintenance starts read-free and explains separate control and archive authority", () => {
    const fixture = mounted();
    expect(fixture.fetcher).not.toHaveBeenCalled();
    expect(
        screen.getByText(/Previews are keyed control-state jobs/),
    ).toBeInTheDocument();
    expect(
        screen.getByText(/One round removes at most one eligible/),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Confirm reviewed maintenance" }),
    ).toBeDisabled();
    expect(
        screen.getByRole("button", { name: "Apply maintenance" }),
    ).toBeDisabled();
    expect(
        screen.queryByRole("button", {
            name: /initialize|cancel|automatic cleanup/i,
        }),
    ).not.toBeInTheDocument();
});

test("prune reviews protected current and exact selected publication before one confirmed apply", async () => {
    const fixture = mounted();
    await previewReady(fixture);
    const plan = prunePayload().plans[0];
    if (plan === undefined) throw new Error("Missing owned prune fixture");
    const review = screen.getByRole("region", {
        name: "Maintenance preview review",
    });
    expect(
        within(review).getByText(plan.selected.publication_id),
    ).toBeInTheDocument();
    expect(within(review).getByText(/Protected current:/)).toHaveTextContent(
        plan.current.commit_sha,
    );
    expect(
        within(review).getByText(/does not freeze its deletion list/),
    ).toBeInTheDocument();
    expect(posts(fixture)).toHaveLength(1);
    await userEvent.click(
        screen.getByRole("button", { name: "Confirm reviewed maintenance" }),
    );
    expect(
        screen.getByRole("button", { name: "Apply maintenance" }),
    ).toBeEnabled();
    await userEvent.click(
        screen.getByRole("button", { name: "Apply maintenance" }),
    );
    await waitFor(() => {
        expect(posts(fixture)).toHaveLength(2);
    });
    expect(fixture.store.snapshot().confirmed).toBe(false);
    expect(
        screen.getByRole("button", { name: "Apply maintenance" }),
    ).toBeDisabled();
    await userEvent.click(
        screen.getByRole("button", { name: "Apply maintenance" }),
    );
    expect(posts(fixture)).toHaveLength(2);
});

test("editing scope retires an already confirmed review without submitting a replacement", async () => {
    const fixture = mounted();
    await previewReady(fixture);
    await userEvent.click(
        screen.getByRole("button", { name: "Confirm reviewed maintenance" }),
    );
    await userEvent.click(
        screen.getByRole("radio", { name: "Selected whole repositories" }),
    );
    await userEvent.type(
        screen.getByRole("textbox", {
            name: "Repository selectors (one per line)",
        }),
        "model:owned/another",
    );
    expect(
        screen.getByRole("button", { name: "Apply maintenance" }),
    ).toBeDisabled();
    expect(
        screen.queryByRole("region", { name: "Maintenance preview review" }),
    ).not.toBeInTheDocument();
    expect(posts(fixture)).toHaveLength(1);
});

test("unmanaged purge explicitly distinguishes current removal and disabled managed protection", async () => {
    const fixture = mounted();
    const plan = purgePayload().plans[0];
    if (plan === undefined) throw new Error("Missing owned purge fixture");
    await choose("Purge unmanaged repositories");
    act(() => {
        fixture.store.setForm({
            kind: "purge",
            scope: "selected",
            selectors: `${plan.repository_type}:${plan.repository_id}`,
        });
    });
    await previewReady(fixture);
    expect(
        screen.getByText(
            /Enabled and disabled configured repositories remain managed/,
        ),
    ).toBeInTheDocument();
    expect(
        screen.getByText(/includes its current reference/),
    ).toHaveTextContent(plan.current.commit_sha);
    expect(
        screen.getByRole("button", { name: "Apply maintenance" }),
    ).toBeDisabled();
    expect(posts(fixture)).toHaveLength(1);
});

test("empty prune preview is truthful and never arms a destructive apply", async () => {
    const fixture = mounted({ payload: () => ({ plans: [], applied: [] }) });
    await userEvent.click(
        screen.getByRole("button", { name: "Preview maintenance" }),
    );
    expect(
        await screen.findByText("Nothing eligible. No Apply is available."),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Confirm reviewed maintenance" }),
    ).toBeDisabled();
    expect(
        screen.getByRole("button", { name: "Apply maintenance" }),
    ).toBeDisabled();
    expect(posts(fixture)).toHaveLength(1);
});

test("blocked recovery retains transaction diagnostics and refuses confirmation", async () => {
    const value = recoveryPayload();
    const fixture = mounted({
        payload: () => ({
            ...value,
            actionable: 0,
            blocked: value.plan.length,
            plan: value.plan.map((plan) => ({
                ...plan,
                remedy: "operator",
                state: "needs_operator",
                reason: "unknown evidence is preserved",
            })),
        }),
    });
    await choose("Recover unfinished transactions");
    await userEvent.click(
        screen.getByRole("button", { name: "Preview maintenance" }),
    );
    await waitFor(() => {
        expect(fixture.store.snapshot().pending).toBeNull();
        expect(fixture.store.snapshot().previewObservation?.phase).toBe(
            "settled",
        );
    });
    expect(
        screen.getByRole("button", { name: "Confirm reviewed maintenance" }),
    ).toBeDisabled();
    expect(
        screen.getByRole("button", { name: "Apply maintenance" }),
    ).toBeDisabled();
    expect(screen.getByText(/Apply is blocked/)).toBeInTheDocument();
    const plan = value.plan[0];
    if (plan !== undefined)
        expect(screen.getByText(plan.transaction_id)).toBeInTheDocument();
    expect(posts(fixture)).toHaveLength(1);
});

test("quarantine reviews explicit batch and retained replacement proof without path inputs", async () => {
    const base = quarantinePayload();
    const value = {
        ...base,
        plans: base.plans.map((plan) => ({
            ...plan,
            files: [
                {
                    path: "config.json",
                    size: 4,
                    sha256: "a".repeat(64),
                    retained_path: "published/owned/config.json",
                },
            ],
            directories: ["staging"],
            logical_bytes: 4,
        })),
    };
    const fixture = mounted({ payload: () => value });
    await choose("Clean proven quarantine");
    await userEvent.type(
        screen.getByRole("textbox", {
            name: "Quarantine transaction IDs (one per line)",
        }),
        value.plans.map((plan) => plan.transaction_id).join("\n"),
    );
    await previewReady(fixture);
    const review = screen.getByRole("region", {
        name: "Maintenance preview review",
    });
    for (const plan of value.plans) {
        expect(
            within(review).getByText(plan.transaction_id),
        ).toBeInTheDocument();
        for (const file of plan.files)
            expect(within(review).getByText(file.sha256)).toBeInTheDocument();
    }
    expect(
        screen.getByText(/There is no all-entry or path selector/),
    ).toBeInTheDocument();
    expect(
        screen.queryByRole("textbox", { name: /quarantine path/i }),
    ).not.toBeInTheDocument();
    expect(posts(fixture)).toHaveLength(1);
});

test("repair has no blind revision input and cannot submit without an exact finding", async () => {
    const fixture = mounted();
    await choose("Repair from an integrity finding");
    expect(
        screen.getByText(/Repair is unavailable without an attributed finding/),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Check repair evidence" }),
    ).toBeDisabled();
    expect(
        screen.getByRole("button", { name: "Confirm reviewed repair" }),
    ).toBeDisabled();
    expect(
        screen.getByRole("button", { name: "Repair reviewed revision" }),
    ).toBeDisabled();
    await userEvent.type(
        screen.getByRole("textbox", { name: "Repair reason" }),
        "Review original manifest expectations",
    );
    expect(posts(fixture)).toHaveLength(0);
    expect(fixture.fetcher).toHaveBeenCalledTimes(2);
    expect(
        fixture.fetcher.mock.calls.every(
            ([url, init]) =>
                (url instanceof URL ? url.pathname : "") ===
                    "/api/v1/jobs/readiness" && init?.method === "GET",
        ),
    ).toBe(true);
});

test("leaving maintenance retires confirmation while preserving the original preview handle", async () => {
    const fixture = mounted();
    await previewReady(fixture);
    await userEvent.click(
        screen.getByRole("button", { name: "Confirm reviewed maintenance" }),
    );
    const records = fixture.controller.snapshot().registry.records;
    fixture.unmount();
    expect(fixture.store.snapshot().confirmed).toBe(false);
    expect(fixture.store.snapshot().canApply).toBe(false);
    expect(fixture.controller.snapshot().registry.records).toEqual(records);
    expect(posts(fixture)).toHaveLength(1);
});

test("repair results retain the finding reviewed for that operation when the editable finding changes", async () => {
    const fixture = mounted();
    const original = repairFinding();
    act(() => {
        fixture.store.setRepairFinding(original);
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Check repair evidence" }),
    );
    await waitFor(() => {
        expect(fixture.store.snapshot().repairProof).toBe("ready");
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Confirm reviewed repair" }),
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Repair reviewed revision" }),
    );
    await waitFor(() => {
        expect(fixture.store.snapshot().effectObservation?.phase).toBe(
            "settled",
        );
    });
    const actual = screen.getByRole("region", {
        name: "Actual repair identities",
    });
    expect(within(actual).getByText(original.source.runId)).toBeInTheDocument();
    expect(
        within(actual).getAllByText(
            original.finding.publication_id ?? "missing",
        ),
    ).toHaveLength(3);
    act(() => {
        fixture.store.setRepairFinding({
            ...original,
            source: { ...original.source, runId: "c".repeat(32) },
            finding: { ...original.finding, publication_id: "d".repeat(32) },
        });
    });
    expect(
        screen.getByRole("region", { name: "Original repair finding" }),
    ).toHaveTextContent("d".repeat(32));
    expect(within(actual).getByText(original.source.runId)).toBeInTheDocument();
    expect(
        within(actual).queryByText(/identities differ from/),
    ).not.toBeInTheDocument();
    expect(posts(fixture)).toHaveLength(1);
    expect(fixture.store.snapshot().confirmed).toBe(false);
});
