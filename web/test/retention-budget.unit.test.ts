import { expect, test } from "vitest";
import {
    createReadCoordinator,
    createRetentionBudget,
    encodedBytes,
} from "../src/state/retention-budget";
import { deferred } from "./state-fixtures";

test("one encoded ledger replaces claims atomically and refuses growth without releasing old charge", () => {
    const budget = createRetentionBudget(10);
    expect(budget.claim("a", 8)).toBe(true);
    expect(budget.claim("b", 3)).toBe(false);
    expect(budget.usedBytes).toBe(8);
    expect(budget.claim("a", 4)).toBe(true);
    expect(budget.claim("b", 6)).toBe(true);
    budget.release("a");
    budget.release("a");
    expect(budget.usedBytes).toBe(6);
    expect(() => budget.claim("x", Number.NaN)).toThrow();
    expect(() => encodedBytes(undefined)).toThrow();
    expect(() => createRetentionBudget(33 * 1024 * 1024)).toThrow();
});

test("two global readers, one owner, cancelled predecessor drains before replacement starts", async () => {
    const reads = createReadCoordinator(),
        a = new AbortController(),
        b = new AbortController(),
        c = new AbortController();
    const first = deferred<number>(),
        second = deferred<number>();
    const started: string[] = [];
    const one = reads.run("a", a.signal, () => {
        started.push("a");
        return first.promise;
    });
    const two = reads.run("b", b.signal, () => {
        started.push("b");
        return second.promise;
    });
    await Promise.resolve();
    expect(reads.active).toBe(2);
    expect(started).toEqual(["a", "b"]);
    await expect(
        reads.run("a", c.signal, () => Promise.resolve(0)),
    ).rejects.toThrow();
    a.abort();
    const replacement = reads.run("a", c.signal, () => {
        started.push("replacement");
        return Promise.resolve(3);
    });
    await Promise.resolve();
    expect(started).toEqual(["a", "b"]);
    first.resolve(1);
    expect(await one).toBe(1);
    expect(await replacement).toBe(3);
    second.resolve(2);
    await two;
    expect(reads.active).toBe(0);
});

test("aborted queued reads never execute and release their queue position", async () => {
    const reads = createReadCoordinator(),
        first = deferred<number>(),
        second = deferred<number>();
    const live = new AbortController(),
        queued = new AbortController();
    const a = reads.run("a", live.signal, () => first.promise),
        b = reads.run("b", live.signal, () => second.promise);
    const pending = reads.run("c", queued.signal, () => {
        throw new Error("queued read executed");
    });
    queued.abort();
    await expect(pending).rejects.toThrow("Observation stopped");
    first.resolve(1);
    second.resolve(2);
    await Promise.all([a, b]);
    expect(reads.waiting).toBe(0);
    expect(reads.active).toBe(0);
});

test("bounded coordinator refuses overflow and never runs a pre-aborted read", async () => {
    const reads = createReadCoordinator(),
        hold = deferred<number>(),
        abort = new AbortController();
    const pending = [
        reads.run("active-a", abort.signal, () => hold.promise),
        reads.run("active-b", abort.signal, () => hold.promise),
    ];
    for (let i = 0; i < 64; i++)
        pending.push(
            reads.run("queued-" + String(i), abort.signal, () =>
                Promise.resolve(i),
            ),
        );
    await expect(
        reads.run("overflow", abort.signal, () => Promise.resolve(0)),
    ).rejects.toThrow();
    const preAborted = new AbortController();
    preAborted.abort();
    await expect(
        reads.run("pre-aborted", preAborted.signal, () => Promise.resolve(0)),
    ).rejects.toThrow("Observation stopped");
    hold.resolve(1);
    await Promise.all(pending);
    expect(reads.waiting).toBe(0);
});
