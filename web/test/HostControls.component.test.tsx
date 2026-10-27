/** Actual controls over the canonical session/query/client boundary; no host effects. */
import { useSyncExternalStore } from "react";
import {
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
    within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test } from "vitest";
import { HostControls } from "../src/components/HostControls";
import {
    hostControlsFixture,
    expectedObserver,
} from "./host-controls-fixtures";
import { ARCHIVE_ID, jsonResponse } from "./read-fixtures";

const owned: ReturnType<typeof hostControlsFixture>[] = [];
function Connected({
    fixture,
}: {
    fixture: ReturnType<typeof hostControlsFixture>;
}) {
    const session = useSyncExternalStore(
        fixture.controller.subscribe,
        fixture.controller.snapshot,
    );
    return (
        <HostControls
            store={fixture.store}
            controller={fixture.controller}
            session={session}
        />
    );
}
function mount(options: Parameters<typeof hostControlsFixture>[0] = {}) {
    const fixture = hostControlsFixture(options);
    owned.push(fixture);
    return { ...fixture, ...render(<Connected fixture={fixture} />) };
}
async function read() {
    await userEvent.click(
        screen.getByRole("button", { name: "Read schedule and observer" }),
    );
    await waitFor(() => {
        expect(
            screen.getByRole("button", { name: "Edit sync schedule" }),
        ).toBeEnabled();
    });
}
afterEach(() => {
    cleanup();
    for (const f of owned) f.dispose();
    owned.length = 0;
});

test("mount sends zero requests and verification timer has only read-only presentation", async () => {
    const f = mount();
    expect(f.calls).toEqual([]);
    const panel = screen.getByRole("region", {
        name: "Verification timer (read-only)",
    });
    expect(within(panel).queryByRole("button")).not.toBeInTheDocument();
    expect(
        within(panel).getByText(
            "Verification timer observation is unavailable.",
        ),
    ).toBeInTheDocument();
    await read();
    expect(f.calls.every((c) => c.method === "GET")).toBe(true);
    expect(within(panel).getByText("linked")).toBeInTheDocument();
});
test("schedule replacement displays server timezone preview and requires one explicit reviewed consent", async () => {
    const f = mount();
    await read();
    await userEvent.click(
        screen.getByRole("button", { name: "Edit sync schedule" }),
    );
    fireEvent.change(screen.getByLabelText("OnCalendar expression"), {
        target: { value: "weekly UTC" },
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Validate schedule" }),
    );
    expect(
        await screen.findByText("Thu 2099-01-01 00:00:00 UTC"),
    ).toBeInTheDocument();
    expect(
        screen.getByText(/not converted to browser time/),
    ).toBeInTheDocument();
    await userEvent.click(
        screen.getByRole("button", { name: "Review replacement" }),
    );
    const apply = screen.getByRole("button", {
        name: "Apply reviewed schedule",
    });
    expect(apply).toBeDisabled();
    await userEvent.click(
        screen.getByRole("checkbox", {
            name: "Confirm reviewed schedule change",
        }),
    );
    expect(apply).toBeEnabled();
    await userEvent.click(apply);
    await waitFor(() => {
        expect(f.calls.filter((c) => c.path.endsWith("/changes"))).toHaveLength(
            1,
        );
    });
    expect(f.calls.find((c) => c.path.endsWith("/changes"))?.body).toEqual({
        action: "replace",
        expected_revision: "e".repeat(64),
        on_calendar: "weekly UTC",
        randomized_delay_sec: "30m",
    });
    expect(
        screen.queryByRole("button", { name: "Apply reviewed schedule" }),
    ).not.toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Observe original host outcome" }),
    ).toBeEnabled();
    expect(f.saved()).not.toContain("weekly UTC");
});
test("invalid raw edit removes validation and the visible ready action without a POST", async () => {
    const f = mount();
    await read();
    await userEvent.click(
        screen.getByRole("button", { name: "Edit sync schedule" }),
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Validate schedule" }),
    );
    await screen.findByRole("heading", { name: "Validated schedule" });
    await userEvent.click(
        screen.getByRole("button", { name: "Review replacement" }),
    );
    fireEvent.change(screen.getByLabelText("Randomized delay (optional)"), {
        target: { value: "bad\\delay" },
    });
    expect(
        screen.queryByRole("heading", { name: "Validated schedule" }),
    ).not.toBeInTheDocument();
    expect(
        screen.queryByRole("button", { name: "Apply reviewed schedule" }),
    ).not.toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Validate schedule" }),
    ).toBeDisabled();
    expect(f.calls.filter((c) => c.method === "POST")).toHaveLength(1);
});
test("pause resume and reset are separate reviewed actions with enablement and catch-up guidance", async () => {
    const f = mount();
    await read();
    for (const [review, apply] of [
        ["Review pause", "Pause sync timer"],
        ["Review resume", "Resume sync timer"],
        ["Review reset", "Reset to shipped schedule"],
    ] as const) {
        await userEvent.click(screen.getByRole("button", { name: review }));
        expect(screen.getByRole("button", { name: apply })).toBeDisabled();
        await userEvent.click(
            screen.getByRole("checkbox", {
                name: "Confirm reviewed schedule change",
            }),
        );
        expect(screen.getByRole("button", { name: apply })).toBeEnabled();
    }
    expect(screen.getByText(/Enablement never changes/)).toHaveTextContent(
        "Persistent catch-up",
    );
    expect(f.calls.filter((c) => c.method === "POST")).toEqual([]);
});
test("explicit observer review exposes original tuple and stops only that tuple", async () => {
    const f = mount({ running: true });
    await read();
    await userEvent.click(
        screen.getByRole("button", { name: "Review original observer" }),
    );
    const region = screen.getByRole("region", {
        name: "Reviewed original observer",
    });
    expect(region).toHaveTextContent(expectedObserver.boot_id);
    expect(region).toHaveTextContent(expectedObserver.invocation_id);
    const stop = screen.getByRole("button", {
        name: "Stop original sync observer",
    });
    expect(stop).toBeDisabled();
    await userEvent.click(
        screen.getByRole("checkbox", { name: "Confirm original observer" }),
    );
    await userEvent.click(stop);
    await waitFor(() => {
        expect(f.calls.filter((c) => c.path.endsWith("/stops"))).toHaveLength(
            1,
        );
    });
    expect(f.calls.find((c) => c.path.endsWith("/stops"))?.body).toEqual({
        expected: expectedObserver,
    });
    expect(
        screen.getByText(/does not cancel its accepted backend/),
    ).toBeInTheDocument();
});
test("denied observer authority leaves schedule controls available and explains independent permission", async () => {
    mount({ observer: false, running: true });
    await read();
    expect(screen.getByRole("button", { name: "Review pause" })).toBeEnabled();
    expect(
        screen.getByRole("button", { name: "Review original observer" }),
    ).toBeDisabled();
    expect(screen.getByText(/Observer-stop permission:/)).toHaveTextContent(
        "profile-unproved",
    );
});
test("journal radio selection is read-free and bounded pages expose gaps and truncation", async () => {
    const f = mount({
        journal: (url) =>
            jsonResponse(
                f.wire("host journal", {
                    schema_version: 1,
                    archive_id: ARCHIVE_ID,
                    source: url.searchParams.get("source"),
                    entries: [
                        {
                            at: null,
                            message:
                                "event=run.started level=info run_id=" +
                                "a".repeat(32),
                        },
                    ],
                    next_cursor: url.searchParams.has("cursor")
                        ? null
                        : "owned-cursor",
                    gap: true,
                    truncated: true,
                }),
            ),
    });
    await userEvent.click(
        screen.getByRole("radio", { name: "Verification observer" }),
    );
    expect(f.calls).toEqual([]);
    await userEvent.click(
        screen.getByRole("button", { name: "Read diagnostic journal" }),
    );
    await screen.findByRole("region", { name: "Loaded diagnostic journal" });
    expect(screen.getByText(/history has a gap/)).toBeInTheDocument();
    expect(screen.getByText(/output was truncated/)).toBeInTheDocument();
    await userEvent.click(
        screen.getByRole("button", { name: "Next journal page" }),
    );
    await screen.findByText("Loaded journal page 2; source verify-observer.");
    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(f.calls).toHaveLength(2);
    await userEvent.click(screen.getByRole("radio", { name: "Sync observer" }));
    expect(f.calls).toHaveLength(2);
    expect(
        screen.queryByRole("region", { name: "Loaded diagnostic journal" }),
    ).not.toBeInTheDocument();
});
test("malformed journal HTML is refused and never becomes active DOM", async () => {
    const f = mount({
        journal: (url) =>
            jsonResponse(
                f.wire("host journal", {
                    schema_version: 1,
                    archive_id: ARCHIVE_ID,
                    source: url.searchParams.get("source"),
                    entries: [
                        {
                            at: null,
                            message:
                                '<img src="/unexpected" onerror="alert(1)">',
                        },
                    ],
                    next_cursor: null,
                    gap: false,
                    truncated: false,
                }),
            ),
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Read diagnostic journal" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
        "Journal unavailable",
    );
    expect(document.querySelector("img,script,iframe")).toBeNull();
    expect(f.calls).toHaveLength(1);
});
test("unmount pauses controls, preserves only dirty RAM draft and retires validation", async () => {
    const f = mount();
    await read();
    await userEvent.click(
        screen.getByRole("button", { name: "Edit sync schedule" }),
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Validate schedule" }),
    );
    await screen.findByRole("heading", { name: "Validated schedule" });
    f.unmount();
    expect(f.store.snapshot().active).toBe(false);
    expect(f.store.snapshot().dirty).toBe(true);
    expect(f.store.snapshot().validation).toBeNull();
    expect(f.store.snapshot().canApply).toBe(false);
    expect(f.saved()).toBeNull();
});
