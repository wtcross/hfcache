import { useEffect, useSyncExternalStore } from "react";
import { act, render, screen, waitFor } from "@testing-library/react";
import { expect, test } from "vitest";
import { createQueryStore } from "../src/state/query-state";
import type { QueryHandle } from "../src/state/query-state";
import {
    createReadCoordinator,
    createRetentionBudget,
} from "../src/state/retention-budget";
import { session, versionResult, deferred } from "./state-fixtures";
import type { VersionResult } from "./state-fixtures";
import type { EmptyPayload, VersionPayload } from "../src/wire/generated";

function View({ query }: { query: QueryHandle<VersionPayload, EmptyPayload> }) {
    const state = useSyncExternalStore(
        query.subscribe,
        query.snapshot,
        query.snapshot,
    );
    useEffect(() => {
        void query.refresh();
    }, [query]);
    return (
        <output>
            {state.result?.kind === "success"
                ? state.result.payload.application
                : state.phase}
        </output>
    );
}

test("React unmount/remount uses original ownership handle and auth clear hides data before late completion", async () => {
    const retention = createRetentionBudget();
    const store = createQueryStore({
        session,
        retention,
        reads: createReadCoordinator(),
        onUnauthorized: () => {},
    });
    const pending = deferred<VersionResult>();
    let first = true;
    const query = store.query({ routeId: "version_default" }, () => {
        if (first) {
            first = false;
            return versionResult("owned-first");
        }
        return pending.promise;
    });
    const mounted = render(<View query={query} />);
    await screen.findByText("owned-first");
    mounted.unmount();
    const second = render(<View query={query} />);
    await screen.findByText("owned-first");
    await act(async () => {
        store.clearPrivate("authentication");
        await Promise.resolve();
    });
    await screen.findByText("unavailable");
    pending.resolve(await versionResult("late-private"));
    await waitFor(() => {
        expect(query.snapshot().result).toBeNull();
    });
    expect(screen.queryByText("late-private")).not.toBeInTheDocument();
    second.unmount();
    store.dispose();
    expect(retention.usedBytes).toBe(0);
});
