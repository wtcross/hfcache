/** WEB030: deterministic request reduction; fixture delay is not production latency. */
import { expect, test } from "@playwright/test";
import { SOURCE_FIXTURE_ORIGIN, sourceFixture } from "./source-fixture";

test("built Library compatible paging reads freshly and avoids repeated facets", async ({
    page,
}, testInfo) => {
    const phase = process.env.HFCACHE_LIBRARY_PAGINATION_CAPTURE ?? "after";
    const fixture = await sourceFixture(page, {
        library: true,
        facetDelayMs: 75,
    });
    const stages: {
        stage: string;
        apiGets: number;
        facets: number;
        elapsedMs: number;
        otherGets: number;
    }[] = [];
    const api = () =>
        fixture.requests.filter((request) =>
            request.path.startsWith("/api/v1/"),
        );
    let offset = 0;
    let requestOffset = 0;
    const record = (stage: string, started: number, firstRow = 0) => {
        const requests = api().slice(offset);
        const otherGets = fixture.requests
            .slice(requestOffset)
            .filter((request) => !request.path.startsWith("/api/v1/")).length;
        if (stage !== "initial") expect(otherGets).toBe(0);
        expect(requests[0]?.path.startsWith("/api/v1/catalog/search?")).toBe(
            true,
        );
        const enrichment = requests.filter((request) => {
            const path = new URL(request.path, SOURCE_FIXTURE_ORIGIN).pathname;
            return [
                "/api/v1/repositories",
                "/api/v1/status",
                "/api/v1/repositories/revisions",
            ].includes(path);
        });
        expect(enrichment).toHaveLength(3);
        const expectedSelectors = Array.from(
            { length: 25 },
            (_, index) =>
                `model:owned/model-${String(firstRow + index).padStart(2, "0")}`,
        );
        for (const request of enrichment)
            expect(
                new URL(
                    request.path,
                    SOURCE_FIXTURE_ORIGIN,
                ).searchParams.getAll("selector"),
            ).toEqual(expectedSelectors);
        stages.push({
            stage,
            apiGets: requests.length,
            facets: requests.filter((request) =>
                request.path.startsWith("/api/v1/catalog/facets?"),
            ).length,
            elapsedMs: performance.now() - started,
            otherGets,
        });
        offset = api().length;
        requestOffset = fixture.requests.length;
    };
    const settled = async (id: string) => {
        await expect(
            page.getByRole("link", { name: id, exact: true }),
        ).toBeVisible();
        await expect(
            page.getByRole("button", { name: "Refresh library" }),
        ).toBeEnabled();
        await expect(page.locator(".library-table tbody tr")).toHaveCount(25);
        const row = page
            .locator(".library-table tbody tr")
            .filter({ has: page.getByRole("link", { name: id, exact: true }) });
        await expect(row).toContainText("17 B");
        await expect(row).toContainText("d".repeat(32));
    };
    try {
        let started = performance.now();
        await page.goto(SOURCE_FIXTURE_ORIGIN + "/ui/library");
        await settled("model-00");
        record("initial", started);
        started = performance.now();
        await page
            .getByRole("button", { name: "Next page", exact: true })
            .click();
        await settled("model-25");
        await expect(
            page.getByRole("link", { name: "model-00", exact: true }),
        ).toHaveCount(0);
        record("Next", started, 25);
        started = performance.now();
        await page
            .getByRole("button", { name: "Previous page", exact: true })
            .click();
        await settled("model-00");
        record("Previous", started);
        started = performance.now();
        await page
            .getByRole("button", { name: "Refresh library", exact: true })
            .click();
        await settled("model-00");
        record("explicit Refresh", started);
        expect(stages.map((stage) => stage.apiGets)).toEqual(
            phase === "before" ? [8, 8, 8, 8] : [8, 4, 4, 8],
        );
        expect(stages.map((stage) => stage.facets)).toEqual(
            phase === "before" ? [4, 4, 4, 4] : [4, 0, 0, 4],
        );
        expect(fixture.apiPeak()).toBeLessThanOrEqual(2);
        expect(
            fixture.requests.every((request) => request.method === "GET"),
        ).toBe(true);
        expect(fixture.unexpected).toEqual([]);
        expect(fixture.cspViolations).toEqual([]);
        expect(fixture.pageErrors).toEqual([]);
    } finally {
        await testInfo.attach("source-library-pagination", {
            contentType: "application/json",
            body: JSON.stringify(
                {
                    scope: "built source Chromium; synthetic API with75ms facet delays; deterministic request reduction is separate from fixture walltime and proves no production latency",
                    phase,
                    viewport: page.viewportSize(),
                    manifest: fixture.manifest,
                    stages,
                    peakApiHandlers: fixture.apiPeak(),
                    apiTimings: fixture.apiTimings,
                    requests: fixture.requests,
                    unexpected: fixture.unexpected,
                    cspViolations: fixture.cspViolations,
                    pageErrors: fixture.pageErrors,
                },
                null,
                2,
            ),
        });
    }
});

test("built Library changed intent and incompatible evidence refresh all facets", async ({
    page,
}, testInfo) => {
    const fixture = await sourceFixture(page, {
        library: true,
        facetDelayMs: 75,
    });
    const stages: { stage: string; apiGets: number; facets: number }[] = [];
    const api = () =>
        fixture.requests.filter((request) =>
            request.path.startsWith("/api/v1/"),
        );
    let offset = 0;
    const record = (stage: string, expected: number) => {
        const requests = api().slice(offset);
        const facets = requests.filter((request) =>
            request.path.startsWith("/api/v1/catalog/facets?"),
        );
        stages.push({ stage, apiGets: requests.length, facets: facets.length });
        expect(requests).toHaveLength(expected);
        expect(facets).toHaveLength(expected === 4 ? 0 : 4);
        expect(requests[0]?.path.startsWith("/api/v1/catalog/search?")).toBe(
            true,
        );
        offset = api().length;
    };
    const settled = async (id: string, rows = 25) => {
        await expect(
            page.getByRole("link", { name: id, exact: true }),
        ).toBeVisible();
        await expect(
            page.getByRole("button", { name: "Refresh library" }),
        ).toBeEnabled();
        await expect(page.locator(".library-table tbody tr")).toHaveCount(rows);
    };
    try {
        await page.goto(SOURCE_FIXTURE_ORIGIN + "/ui/library");
        await settled("model-00");
        record("initial", 8);
        fixture.setLibraryEvidence({ identity: "b".repeat(64) });
        await page
            .getByRole("button", { name: "Next page", exact: true })
            .click();
        await settled("model-00");
        record("changed catalog identity Next restarts first page", 9);
        await page
            .getByRole("button", { name: "Next page", exact: true })
            .click();
        await settled("model-25");
        record("compatible Next after fresh identity", 4);
        fixture.setLibraryEvidence({ missing: 26 });
        await page
            .getByRole("button", { name: "Previous page", exact: true })
            .click();
        await settled("model-00");
        record("changed whole coverage Previous", 8);
        await page
            .getByRole("button", { name: "Next page", exact: true })
            .click();
        await settled("model-25");
        record("compatible Next after fresh coverage", 4);
        await page
            .getByRole("searchbox", { name: "Find repositories" })
            .fill("owned");
        await expect(page).toHaveURL(/q=owned/u);
        await settled("model-00");
        record("changed text predicate", 8);
        const advanced = page
            .locator("summary")
            .filter({ hasText: "Filters and page size" });
        await advanced.click();
        await page
            .getByRole("button", { name: "Rows per page: 25", exact: true })
            .click();
        await page.getByRole("option", { name: "50", exact: true }).click();
        await settled("model-49", 50);
        record("changed page size", 8);
        await page
            .getByRole("button", { name: "Clear filters", exact: true })
            .click();
        await settled("model-00");
        record("cleared predicates and page size", 8);
        await page.goBack();
        await settled("model-49", 50);
        record("Back restores changed predicate and size", 8);
        await page.goForward();
        await settled("model-00");
        record("Forward restores default intent", 8);
        expect(fixture.apiPeak()).toBeLessThanOrEqual(2);
        expect(
            fixture.requests.every((request) => request.method === "GET"),
        ).toBe(true);
        expect(fixture.unexpected).toEqual([]);
        expect(fixture.cspViolations).toEqual([]);
        expect(fixture.pageErrors).toEqual([]);
    } finally {
        await testInfo.attach("source-library-pagination-invalidation", {
            contentType: "application/json",
            body: JSON.stringify(
                {
                    scope: "built source Chromium; owned75ms-delay fixture; fresh catalog+qualified scope, no global snapshot or production acceptance",
                    manifest: fixture.manifest,
                    stages,
                    peakApiHandlers: fixture.apiPeak(),
                    apiTimings: fixture.apiTimings,
                    requests: fixture.requests,
                    unexpected: fixture.unexpected,
                    cspViolations: fixture.cspViolations,
                    pageErrors: fixture.pageErrors,
                },
                null,
                2,
            ),
        });
    }
});
