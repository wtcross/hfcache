import { afterEach, expect, test } from "vitest";
import {
    hostControlsFixture,
    expectedObserver,
} from "./host-controls-fixtures";
import {
    deferred,
    receipt,
    OPERATION_ID,
    operationResponse,
} from "./state-fixtures";
import { ARCHIVE_ID, jsonResponse } from "./read-fixtures";

const owned: ReturnType<typeof hostControlsFixture>[] = [];
function fixture(options: Parameters<typeof hostControlsFixture>[0] = {}) {
    const value = hostControlsFixture(options);
    owned.push(value);
    return value;
}
async function ready(value: ReturnType<typeof hostControlsFixture>) {
    value.store.setPageActive(true);
    await value.store.readHost();
    expect(value.store.snapshot().canSchedule).toBe(true);
}
afterEach(() => {
    for (const value of owned) value.dispose();
    owned.length = 0;
});

test("constructor and activation own no GET or effect; shared host handle is reused", async () => {
    const f = fixture();
    f.store.setPageActive(true);
    expect(f.calls).toEqual([]);
    await f.store.readHost();
    expect(f.calls.map((c) => c.method)).toEqual(["GET", "GET"]);
    expect(f.controller.hostStatus.snapshot().result?.kind).toBe("success");
});
test("schedule remains usable when observer MAC authority is unproved", async () => {
    const f = fixture({ observer: false, running: true });
    await ready(f);
    expect(f.store.snapshot().canReviewObserver).toBe(false);
    f.store.reviewSchedule("pause");
    f.store.confirmSchedule(true);
    expect(f.store.snapshot().canApply).toBe(true);
});
test("every raw edit, including an invalid edit, retires exact validation and confirmation", async () => {
    const f = fixture();
    await ready(f);
    f.store.edit();
    await f.store.validate();
    f.store.reviewSchedule("replace");
    f.store.confirmSchedule(true);
    expect(f.store.snapshot().canApply).toBe(true);
    f.store.setDraft("calendar", "daily\nunsafe");
    expect(f.store.snapshot().validation).toBeNull();
    expect(f.store.snapshot().canApply).toBe(false);
    expect(f.store.snapshot().canValidate).toBe(false);
    expect(f.calls.filter((c) => c.method === "POST")).toHaveLength(1);
});
test("late validation cannot authorize a newer raw draft", async () => {
    const pending = deferred<Response>();
    const f = fixture({ validation: () => pending.promise });
    await ready(f);
    f.store.edit();
    const run = f.store.validate();
    f.store.setDraft("calendar", "weekly UTC");
    pending.resolve(
        jsonResponse(
            f.wire("host schedule validate", {
                schema_version: 1,
                archive_id: ARCHIVE_ID,
                on_calendar: "daily UTC",
                randomized_delay_sec: "30m",
                normalized_on_calendar: "*-*-* 00:00:00 UTC",
                normalized_randomized_delay_sec: "30m",
                next_elapse: null,
            }),
        ),
    );
    await run;
    expect(f.store.snapshot().draft.calendar).toBe("weekly UTC");
    expect(f.store.snapshot().validation).toBeNull();
    expect(f.store.snapshot().canApply).toBe(false);
});
test("one reviewed replacement consumes consent before exactly one keyed controller POST", async () => {
    const f = fixture();
    await ready(f);
    f.store.edit();
    f.store.setDraft("calendar", "weekly UTC");
    await f.store.validate();
    f.store.reviewSchedule("replace");
    f.store.confirmSchedule(true);
    await Promise.all([f.store.applySchedule(), f.store.applySchedule()]);
    const attempts = f.calls.filter((c) => c.path.endsWith("/changes"));
    expect(attempts).toHaveLength(1);
    expect(attempts[0]?.body).toEqual({
        action: "replace",
        expected_revision: "e".repeat(64),
        on_calendar: "weekly UTC",
        randomized_delay_sec: "30m",
    });
    expect(attempts[0]?.key).toBeTruthy();
    expect(f.saved()).toContain(attempts[0]?.key);
    expect(f.store.snapshot().scheduleReview).toBeNull();
    expect(f.store.snapshot().canApply).toBe(false);
    expect(f.controller.snapshot().registry.records[0]?.state).toBe(
        "uncertain",
    );
});
test.each(["pause", "resume", "reset"] as const)(
    "%s reviews exact original revision and emits no calendar fields",
    async (action) => {
        const f = fixture();
        await ready(f);
        f.store.reviewSchedule(action);
        f.store.confirmSchedule(true);
        await f.store.applySchedule();
        expect(f.calls.find((c) => c.key !== null)?.body).toEqual({
            action,
            expected_revision: "e".repeat(64),
        });
    },
);
test("host refresh and changed revision retire existing review even when raw draft is unchanged", async () => {
    const f = fixture();
    await ready(f);
    f.store.edit();
    await f.store.validate();
    f.store.reviewSchedule("replace");
    f.store.confirmSchedule(true);
    const facts = f.host().facts;
    if (facts === null) throw new Error("Missing owned facts");
    f.setHost({
        ...f.host(),
        facts: {
            ...facts,
            sync_schedule: { ...facts.sync_schedule, revision: "f".repeat(64) },
        },
    });
    await f.store.readHost();
    expect(f.store.snapshot().scheduleReview).toBeNull();
    expect(f.store.snapshot().validation).toBeNull();
    expect(f.store.snapshot().dirty).toBe(true);
});
test("original observer tuple is reviewed and transmitted unchanged, never a unit selector", async () => {
    const f = fixture({ running: true });
    await ready(f);
    f.store.reviewObserver();
    f.store.confirmObserver(true);
    await f.store.stopObserver();
    expect(f.calls.find((c) => c.path.endsWith("/stops"))?.body).toEqual({
        expected: expectedObserver,
    });
    expect(f.store.snapshot().observerReview).toBeNull();
    expect(f.store.snapshot().canStop).toBe(false);
});
test("a replacement observer invocation invalidates the old confirmation", async () => {
    const f = fixture({ running: true });
    await ready(f);
    f.store.reviewObserver();
    f.store.confirmObserver(true);
    f.setObserver({
        ...f.observer(),
        expected: { ...expectedObserver, main_pid: 4322 },
    });
    await f.store.readHost();
    expect(f.store.snapshot().observerReview).toBeNull();
    await f.store.stopObserver();
    expect(f.calls.filter((c) => c.key)).toEqual([]);
});
test("route pause retires readiness but keeps the bounded dirty draft; reconnect clears it", async () => {
    const f = fixture();
    await ready(f);
    f.store.edit();
    await f.store.validate();
    f.store.reviewSchedule("replace");
    f.store.confirmSchedule(true);
    f.store.setPageActive(false);
    expect(f.store.snapshot().dirty).toBe(true);
    expect(f.store.snapshot().validation).toBeNull();
    expect(f.store.snapshot().host).toBeNull();
    f.controller.disconnect();
    expect(f.store.snapshot().dirty).toBe(false);
    expect(f.store.snapshot().draft.calendar).toBe("");
    await f.controller.reconnect();
    expect(f.store.snapshot().canApply).toBe(false);
});
test("journal source selection is read-free; explicit pages replace rather than accumulate", async () => {
    const f = fixture({
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
                    next_cursor: "opaque-next",
                    gap: true,
                    truncated: true,
                }),
            ),
    });
    f.store.setPageActive(true);
    f.store.setJournalSource("verify-observer");
    expect(f.calls).toEqual([]);
    await f.store.readJournal();
    expect(f.store.snapshot().journal?.result?.kind).toBe("success");
    await f.store.nextJournal();
    expect(f.store.snapshot().journalPage).toBe(2);
    expect(f.calls[1]?.query).toContain("cursor=opaque-next");
    f.store.setJournalSource("sync-observer");
    expect(f.calls).toHaveLength(2);
    expect(f.store.snapshot().journal).toBeNull();
});
test("journal continuation stops after32 explicit positions without an extra GET", async () => {
    const f = fixture({
        journal: (url) =>
            jsonResponse(
                f.wire("host journal", {
                    schema_version: 1,
                    archive_id: ARCHIVE_ID,
                    source: url.searchParams.get("source"),
                    entries: [],
                    next_cursor: "opaque-" + String(f.calls.length),
                    gap: false,
                    truncated: false,
                }),
            ),
    });
    f.store.setPageActive(true);
    await f.store.readJournal();
    for (let n = 1; n < 32; n++) await f.store.nextJournal();
    expect(f.calls).toHaveLength(32);
    expect(f.store.snapshot().canNextJournal).toBe(false);
    await f.store.nextJournal();
    expect(f.calls).toHaveLength(32);
});
test("denied Basic host-read performs no request and creates no readiness", async () => {
    const f = fixture({ hostRead: false });
    f.store.setPageActive(true);
    await f.store.readHost();
    await f.store.readJournal();
    expect(f.calls).toEqual([]);
    expect(f.store.snapshot().canSchedule).toBe(false);
});

test("an identical raw edit still consumes prior validation", async () => {
    const f = fixture();
    await ready(f);
    f.store.edit();
    await f.store.validate();
    f.store.setDraft("calendar", f.store.snapshot().draft.calendar);
    expect(f.store.snapshot().validation).toBeNull();
    f.store.reviewSchedule("replace");
    expect(f.store.snapshot().scheduleReview).toBeNull();
});

test("a shared host-query invalidation retires ready review without a new read or effect", async () => {
    const f = fixture();
    await ready(f);
    f.store.reviewSchedule("reset");
    f.store.confirmSchedule(true);
    const before = f.calls.length;
    f.controller.hostStatus.invalidate();
    expect(f.store.snapshot().scheduleReview).toBeNull();
    expect(f.store.snapshot().canApply).toBe(false);
    expect(f.calls).toHaveLength(before);
});

test("late validation after disconnect never restores private draft or readiness", async () => {
    const pending = deferred<Response>();
    const f = fixture({ validation: () => pending.promise });
    await ready(f);
    f.store.edit();
    const run = f.store.validate();
    f.controller.disconnect();
    pending.resolve(
        jsonResponse(
            f.wire("host schedule validate", {
                schema_version: 1,
                archive_id: ARCHIVE_ID,
                on_calendar: "daily UTC",
                randomized_delay_sec: "30m",
                normalized_on_calendar: "*-*-* 00:00:00 UTC",
                normalized_randomized_delay_sec: "30m",
                next_elapse: null,
            }),
        ),
    );
    await run;
    expect(f.store.snapshot().draft.calendar).toBe("");
    expect(f.store.snapshot().validation).toBeNull();
    expect(f.store.snapshot().canApply).toBe(false);
});

test("disposed controls cannot restart reads or submit effects", async () => {
    const f = fixture();
    await ready(f);
    const count = f.calls.length;
    f.store.dispose();
    await f.store.readHost();
    await f.store.readJournal();
    await f.store.validate();
    f.store.reviewSchedule("reset");
    f.store.confirmSchedule(true);
    await f.store.applySchedule();
    expect(f.calls).toHaveLength(count);
    expect(f.store.snapshot().active).toBe(false);
});

test.each(["pause", "discard"] as const)(
    "synchronous %s at submit notification retires intent before any POST",
    async (retirement) => {
        const f = fixture();
        await ready(f);
        f.store.reviewSchedule("resume");
        f.store.confirmSchedule(true);
        let retired = false;
        const unsubscribe = f.store.subscribe(() => {
            if (!retired && f.store.snapshot().pending === "submit") {
                retired = true;
                if (retirement === "pause") f.store.setPageActive(false);
                else f.store.discard();
            }
        });
        await f.store.applySchedule();
        unsubscribe();
        expect(retired).toBe(true);
        expect(f.calls.filter((c) => c.method === "POST")).toEqual([]);
        expect(f.controller.snapshot().registry.records).toEqual([]);
    },
);

test("synchronous route pause at read or validation notification starts no request", async () => {
    const f = fixture();
    f.store.setPageActive(true);
    let armed = true;
    const unsubscribe = f.store.subscribe(() => {
        if (armed && f.store.snapshot().pending === "read") {
            armed = false;
            f.store.setPageActive(false);
        }
    });
    await f.store.readHost();
    unsubscribe();
    expect(f.calls).toEqual([]);
    await ready(f);
    f.store.edit();
    const before = f.calls.length;
    armed = true;
    const stopValidation = f.store.subscribe(() => {
        if (armed && f.store.snapshot().pending === "validation") {
            armed = false;
            f.store.setPageActive(false);
        }
    });
    await f.store.validate();
    stopValidation();
    expect(f.calls).toHaveLength(before);
});

test("original outcome recovery uses only GET and pending host proof never releases uncertainty", async () => {
    let pending = true;
    const f = fixture({
        extra: (url, init) => {
            expect(init?.method).toBe("GET");
            const original = receipt({
                route: "/api/v1/host/sync-schedule/changes",
                state: "interrupted",
                completed_at: "2026-10-20T12:00:01.000000Z",
            });
            if (url.pathname.endsWith("/lookup"))
                return jsonResponse(
                    operationResponse("operations lookup", {
                        operation: original,
                    }),
                );
            expect(url.pathname).toBe(
                "/api/v1/host/sync-schedule/changes/" + OPERATION_ID,
            );
            return jsonResponse(
                f.wire("host schedule outcome", {
                    schema_version: 1,
                    archive_id: ARCHIVE_ID,
                    operation_id: OPERATION_ID,
                    request_digest: "b".repeat(64),
                    state: "confirmed",
                    pending,
                    action: "pause",
                    expected_revision: "e".repeat(64),
                    stored_revision: "e".repeat(64),
                    file_state: "unchanged",
                    manager_state: "timer_acknowledged",
                    timer_was_active: true,
                    timer_is_active: false,
                }),
            );
        },
    });
    await ready(f);
    f.store.reviewSchedule("pause");
    f.store.confirmSchedule(true);
    await f.store.applySchedule();
    const posts = f.calls.filter((c) => c.method === "POST").length;
    await f.store.observeOutcome();
    expect(f.store.snapshot().outcome).toMatchObject({
        kind: "outcome",
        result: { kind: "success" },
    });
    expect(f.store.snapshot().notice).toContain("unresolved");
    expect(f.controller.snapshot().canSubmit).toBe(false);
    pending = false;
    await f.store.observeOutcome();
    expect(f.store.snapshot().notice).toContain("effect is confirmed");
    expect(f.controller.snapshot().canSubmit).toBe(true);
    expect(f.calls.filter((c) => c.method === "POST")).toHaveLength(posts);
    expect(f.calls.filter((c) => c.path.endsWith("/lookup"))).toHaveLength(2);
});
