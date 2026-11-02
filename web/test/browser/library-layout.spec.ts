/** Matching source-fixture layout captures; no installed/production acceptance. */
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { SOURCE_FIXTURE_ORIGIN, sourceFixture } from "./source-fixture";

for (const viewport of [
    { width: 390, height: 844 },
    { width: 1440, height: 1000 },
]) {
    test(`built Library initial viewport ${String(viewport.width)} by ${String(viewport.height)}`, async ({
        page,
    }, testInfo) => {
        const phase = process.env.HFCACHE_LIBRARY_CAPTURE ?? "after";
        const fixture = await sourceFixture(page, { library: true });
        await page.setViewportSize(viewport);
        await page.goto(SOURCE_FIXTURE_ORIGIN + "/ui/library");
        await expect(
            page.getByRole("link", { name: "model-00", exact: true }),
        ).toBeVisible();
        await expect(
            page.getByRole("button", { name: "Refresh library" }),
        ).toBeEnabled();
        const search = page.getByRole("searchbox", {
            name: "Find repositories",
        });
        const identity = page.getByRole("link", {
            name: "model-00",
            exact: true,
        });
        const table = page.getByRole("region", {
            name: "Repository table, scroll horizontally on narrow screens",
        });
        const measure = async (locator: typeof search) =>
            locator.evaluate((element) => {
                const box = element.getBoundingClientRect();
                return {
                    top: box.top,
                    bottom: box.bottom,
                    left: box.left,
                    right: box.right,
                };
            });
        const measurements = {
            phase,
            viewport: page.viewportSize(),
            browser: await page.evaluate(() => ({
                innerWidth,
                innerHeight,
                dpr: devicePixelRatio,
                scrollX,
                scrollY,
                scrollWidth: document.documentElement.scrollWidth,
            })),
            search: await measure(search),
            identity: await measure(identity),
            table: await measure(table),
            loadedRows: await page.locator(".library-table tbody tr").count(),
            apiGets: fixture.requests.filter((request) =>
                request.path.startsWith("/api/v1/"),
            ).length,
        };
        await page.screenshot({
            path: testInfo.outputPath(
                `library-${phase}-${String(viewport.width)}x${String(viewport.height)}.png`,
            ),
        });
        await testInfo.attach("source-library-viewport", {
            contentType: "application/json",
            body: JSON.stringify(
                {
                    scope: "built source Chromium; fixed authenticated25row incomplete-coverage synthetic API fixture; no installed/production acceptance",
                    manifest: fixture.manifest,
                    measurements,
                    requests: fixture.requests,
                    unexpected: fixture.unexpected,
                    cspViolations: fixture.cspViolations,
                    pageErrors: fixture.pageErrors,
                },
                null,
                2,
            ),
        });
        expect(measurements.loadedRows).toBe(25);
        expect(measurements.browser.scrollY).toBe(0);
        expect(fixture.unexpected).toEqual([]);
        expect(fixture.cspViolations).toEqual([]);
        expect(fixture.pageErrors).toEqual([]);
        expect(
            fixture.requests.every((request) => request.method === "GET"),
        ).toBe(true);
        if (phase === "after") {
            expect(measurements.search.top).toBeGreaterThanOrEqual(0);
            expect(measurements.search.bottom).toBeLessThanOrEqual(
                viewport.height,
            );
            expect(measurements.identity.top).toBeGreaterThanOrEqual(0);
            expect(measurements.identity.bottom).toBeLessThanOrEqual(
                viewport.height,
            );
            expect(measurements.browser.scrollWidth).toBeLessThanOrEqual(
                viewport.width,
            );
            const axe = await new AxeBuilder({ page }).analyze();
            expect(axe.violations).toEqual([]);
        }
    });
}
