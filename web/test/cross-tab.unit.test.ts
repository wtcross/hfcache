import { afterEach, expect, test, vi } from "vitest";
import { createApiScope } from "../src/api/identity";
import { stableAuthorityIdentity } from "../src/state/authority";
import {
    createCrossTabAdvice,
    CROSS_TAB_CHANNEL,
    MAX_ADVICE_BYTES,
    MAX_ADVICE_SUBSCRIBERS,
} from "../src/state/cross-tab";
import type { AdviceChannel } from "../src/state/cross-tab";
import { ARCHIVE_ID } from "./read-fixtures";

const scope = createApiScope({
    origin: "https://archive.invalid",
    publicPrefix: "/management",
    authorityEpoch: "first",
    subject: "administrator",
    credentialClass: "rest-writer",
    instanceId: "a".repeat(32),
    archiveId: ARCHIVE_ID,
    configFingerprint: "b".repeat(64),
});
const recordId = "c".repeat(32);

class Channel implements AdviceChannel {
    readonly listeners = new Set<(event: MessageEvent<unknown>) => void>();
    readonly sent: string[] = [];
    closed = false;
    postMessage(message: string): void {
        this.sent.push(message);
    }
    addEventListener(
        _type: "message",
        listener: (event: MessageEvent<unknown>) => void,
    ): void {
        this.listeners.add(listener);
    }
    removeEventListener(
        _type: "message",
        listener: (event: MessageEvent<unknown>) => void,
    ): void {
        this.listeners.delete(listener);
    }
    close(): void {
        this.closed = true;
    }
    receive(data: unknown): void {
        for (const listener of this.listeners)
            listener(new MessageEvent("message", { data }));
    }
}

function fixture() {
    const channel = new Channel();
    const channelFactory = vi.fn(() => channel);
    const advice = createCrossTabAdvice({ scope, channelFactory });
    return { channel, channelFactory, advice };
}

function wire(overrides: Readonly<Record<string, unknown>> = {}): string {
    return JSON.stringify({
        schemaVersion: 1,
        kind: "registry-stale",
        scope: stableAuthorityIdentity(scope),
        recordId,
        ...overrides,
    });
}

afterEach(() => vi.unstubAllGlobals());

test("publishes only bounded scope/record advice, never an outcome or original key", () => {
    const { channel, channelFactory, advice } = fixture();
    expect(channelFactory).toHaveBeenCalledWith(CROSS_TAB_CHANNEL);
    expect(advice.publish(recordId)).toBe(true);
    expect(channel.sent).toEqual([wire()]);
    expect(new TextEncoder().encode(channel.sent[0]).byteLength).toBeLessThan(
        MAX_ADVICE_BYTES,
    );
    expect(Object.keys(advice).sort()).toEqual([
        "dispose",
        "publish",
        "subscribe",
    ]);
    for (const invalid of ["", "A".repeat(32), "f".repeat(33), "hf_secret"])
        expect(advice.publish(invalid)).toBe(false);
    expect(channel.sent).toHaveLength(1);
    advice.dispose();
});

test("only exact stable scope matches; API epochs can change without authority rebinding", () => {
    const { channel, advice } = fixture();
    const listener = vi.fn();
    advice.subscribe(listener);
    const compatible = createApiScope({
        ...scope,
        instanceId: "d".repeat(32),
        authorityEpoch: "second",
        configFingerprint: "e".repeat(64),
    });
    channel.receive(wire({ scope: stableAuthorityIdentity(compatible) }));
    expect(listener).toHaveBeenCalledExactlyOnceWith(recordId);
    for (const change of [
        { origin: "https://other.invalid" },
        { publicPrefix: "/other" },
        { subject: "another-administrator" },
        { credentialClass: "rest-reader" as const },
        { archiveId: "11111111-1111-1111-1111-111111111111" },
    ])
        channel.receive(
            wire({ scope: stableAuthorityIdentity({ ...scope, ...change }) }),
        );
    expect(listener).toHaveBeenCalledTimes(1);
    advice.dispose();
});

test.each([
    null,
    {},
    [],
    1,
    "not JSON",
    "[]",
    "null",
    wire({ schemaVersion: 2 }),
    wire({ schemaVersion: "1" }),
    wire({ kind: "settled" }),
    wire({ recordId: "not-an-id" }),
    wire({ body: "hostile secret content" }),
    wire({ result: { outcome: "success" } }),
    wire().replace('"schemaVersion":1', '"schemaVersion":1.0'),
    wire().replace('"schemaVersion":1', '"schemaVersion":1,"schemaVersion":1'),
    wire({ scope: [stableAuthorityIdentity(scope)] }),
    wire({ scope: { nested: { deeper: "not a scope" } } }),
    wire({ scope: "x".repeat(MAX_ADVICE_BYTES) }),
    wire({ scope: "界".repeat(2000) }),
])("ignores malformed, oversized or authority-bearing advice: %j", (data) => {
    const { channel, advice } = fixture();
    const listener = vi.fn();
    advice.subscribe(listener);
    channel.receive(data);
    expect(listener).not.toHaveBeenCalled();
    expect(channel.sent).toEqual([]);
    advice.dispose();
});

test("subscription failures are isolated and both listener count and lifetime are bounded", () => {
    const { channel, advice } = fixture();
    const failing = vi.fn(() => {
        throw new Error("a view failed");
    });
    const remove = advice.subscribe(failing);
    const observers = Array.from({ length: MAX_ADVICE_SUBSCRIBERS }, () =>
        vi.fn(),
    );
    const removals = observers.map((observer) => advice.subscribe(observer));
    channel.receive(wire());
    expect(failing).toHaveBeenCalledTimes(1);
    expect(observers[0]).toHaveBeenCalledExactlyOnceWith(recordId);
    expect(observers.at(-1)).not.toHaveBeenCalled();
    remove();
    removals[0]?.();
    advice.subscribe(observers.at(-1) ?? vi.fn());
    channel.receive(wire());
    expect(failing).toHaveBeenCalledTimes(1);
    expect(observers.at(-1)).toHaveBeenCalledExactlyOnceWith(recordId);
    const inFlight = [...channel.listeners];
    advice.dispose();
    advice.dispose();
    for (const listener of inFlight)
        listener(new MessageEvent("message", { data: wire() }));
    advice.subscribe(failing)();
    expect(failing).toHaveBeenCalledTimes(1);
    expect(channel.listeners.size).toBe(0);
    expect(channel.closed).toBe(true);
    expect(advice.publish(recordId)).toBe(false);
});

test("missing and failing transports are optional and cannot settle recovery state", () => {
    vi.stubGlobal("BroadcastChannel", undefined);
    const unavailable = createCrossTabAdvice({ scope });
    expect(unavailable.publish(recordId)).toBe(false);
    unavailable.dispose();
    const denied = createCrossTabAdvice({
        scope,
        channelFactory: () => {
            throw new Error("transport refused");
        },
    });
    expect(denied.publish(recordId)).toBe(false);
    denied.dispose();
    const { channel, advice } = fixture();
    vi.spyOn(channel, "postMessage").mockImplementation(() => {
        throw new Error("transport lost");
    });
    expect(advice.publish(recordId)).toBe(false);
    vi.spyOn(channel, "removeEventListener").mockImplementation(() => {
        throw new Error("unavailable");
    });
    expect(() => {
        advice.dispose();
    }).not.toThrow();
    expect(channel.closed).toBe(true);
});

test("partial channel setup closes its exact owned transport", () => {
    const channel = new Channel();
    vi.spyOn(channel, "addEventListener").mockImplementation(() => {
        throw new Error("listener refused");
    });
    const close = vi.spyOn(channel, "close").mockImplementation(() => {
        throw new Error("transport failed during close");
    });
    const advice = createCrossTabAdvice({
        scope,
        channelFactory: () => channel,
    });
    expect(close).toHaveBeenCalledTimes(1);
    expect(advice.publish(recordId)).toBe(false);
    advice.dispose();
});

test("oversized scope refuses before constructing any transport", () => {
    const channelFactory = vi.fn(() => new Channel());
    expect(() =>
        createCrossTabAdvice({
            scope: {
                ...scope,
                publicPrefix: "/" + "x".repeat(MAX_ADVICE_BYTES),
            },
            channelFactory,
        }),
    ).toThrow();
    expect(channelFactory).not.toHaveBeenCalled();
});

test("real BroadcastChannel delivers only a peer's advisory ID and closes normally", async () => {
    const sender = createCrossTabAdvice({ scope });
    const receiver = createCrossTabAdvice({ scope });
    const self = vi.fn();
    sender.subscribe(self);
    try {
        const received = new Promise<string>((resolve) =>
            receiver.subscribe(resolve),
        );
        expect(sender.publish(recordId)).toBe(true);
        expect(await received).toBe(recordId);
        expect(self).not.toHaveBeenCalled();
    } finally {
        sender.dispose();
        receiver.dispose();
    }
});
