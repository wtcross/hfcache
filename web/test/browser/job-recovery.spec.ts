/** Built app with bounded owned HTTPS responses; no installed host acceptance. */
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { SOURCE_FIXTURE_ORIGIN, sourceFixture } from "./source-fixture";

for (const width of [390, 1440]) {
    test(`built job availability and causal refusal preserve one original at ${String(width)}px`, async ({
        page,
    }, testInfo) => {
        await page.setViewportSize({ width, height: 1000 });
        const fixture = await sourceFixture(page, { jobs: "empty" });
        fixture.setJobReadiness({ archive: false });
        await page.goto(SOURCE_FIXTURE_ORIGIN + "/ui/operations");
        const submit = page.getByRole("button", {
            name: "Submit job",
            exact: true,
        });
        const recheck = page.getByRole("button", {
            name: "Recheck job readiness",
        });
        await expect(recheck).toBeEnabled();
        await page.getByRole("button", { name: /^Job: /u }).click();
        await page.getByRole("option", { name: "Sync", exact: true }).click();
        await expect(submit).toHaveAccessibleDescription(
            "Unavailable: archive writes are disabled.",
        );
        await expect(submit).toBeDisabled();
        expect(
            fixture.requests.filter((r) => r.path === "/api/v1/jobs/readiness"),
        ).toHaveLength(2);
        fixture.setJobReadiness({ archive: true, archive_writable: false });
        await recheck.focus();
        await page.keyboard.press("Enter");
        await expect(submit).toHaveAccessibleDescription(
            "Unavailable: required archive storage is read-only.",
        );
        await expect(submit).toBeDisabled();
        expect(
            fixture.requests.filter((r) => r.method === "POST"),
        ).toHaveLength(0);
        fixture.setJobReadiness({ archive: null, archive_writable: null });
        await recheck.click();
        await expect(submit).toHaveAccessibleDescription(
            /Some readiness facts are unknown/u,
        );
        await expect(submit).toBeEnabled();
        expect(
            fixture.requests.filter((r) => r.path === "/api/v1/jobs/readiness"),
        ).toHaveLength(4);
        await submit.click();
        await expect(
            page.getByText(
                /Not admitted\. This request was refused before admission/u,
            ),
        ).toBeVisible();
        expect(fixture.requests.filter((r) => r.method === "POST")).toEqual([
            { method: "POST", path: "/api/v1/syncs" },
        ]);
        expect(
            fixture.requests.filter(
                (r) => r.path === "/api/v1/operations/intent",
            ),
        ).toHaveLength(1);
        await page.reload();
        await expect(
            page.getByText(
                /Not admitted\. This request was refused before admission/u,
            ),
        ).toBeVisible();
        expect(
            fixture.requests.filter(
                (r) => r.path === "/api/v1/operations/intent",
            ),
        ).toHaveLength(2);
        expect(
            fixture.requests.filter((r) => r.method === "POST"),
        ).toHaveLength(1);
        const accessibility = await new AxeBuilder({ page }).analyze();
        expect(accessibility.violations).toEqual([]);
        expect(
            await page.evaluate(
                () => document.documentElement.scrollWidth <= innerWidth,
            ),
        ).toBe(true);
        expect(fixture.unexpected).toEqual([]);
        expect(fixture.cspViolations).toEqual([]);
        expect(fixture.pageErrors).toEqual([]);
        await testInfo.attach("job-readiness-and-refusal", {
            contentType: "application/json",
            body: JSON.stringify({
                scope: "built source Chromium, synthetic API only",
                width,
                requests: fixture.requests,
                manifest: fixture.manifest,
            }),
        });
    });
}

for (const retainedId of [false, true]) {
    test(`built restored schema1 unknown retained-ID=${String(retainedId)} reconciles GET-only and requires deliberate reviewed retirement`, async ({
        page,
    }, testInfo) => {
        const fixture = await sourceFixture(page, {
            jobs: retainedId ? "unknown-id" : "unknown",
        });
        await page.goto(SOURCE_FIXTURE_ORIGIN + "/ui/operations");
        await expect(
            page.getByRole("button", {
                name: "Review original request",
                exact: true,
            }),
        ).toBeVisible();
        await expect(
            page.getByRole("button", { name: "Submit job", exact: true }),
        ).toBeDisabled();
        expect(
            fixture.requests.filter(
                (r) => r.path === "/api/v1/operations/intent",
            ),
        ).toHaveLength(1);
        expect(
            fixture.requests.filter((r) => r.method === "POST"),
        ).toHaveLength(0);
        const saved = await page.evaluate(() =>
            localStorage.getItem("hfcache.web.operations.v1"),
        );
        expect(saved).toContain('"schemaVersion":2');
        expect(saved).toContain('"key":"owned-original-key"');
        const review = page.getByRole("button", {
            name: "Review original request",
            exact: true,
        });
        await review.focus();
        await page.keyboard.press("Enter");
        const confirm = page.getByRole("button", {
            name: "Confirm review and retire original request",
        });
        await expect(confirm).toBeVisible();
        expect(
            fixture.requests.filter((r) => r.method === "POST"),
        ).toHaveLength(0);
        await confirm.focus();
        await page.keyboard.press("Enter");
        await expect(
            page.getByText(
                /Historical outcome unknown; request retired\. You may start a new job/u,
            ),
        ).toBeVisible();
        expect(fixture.requests.filter((r) => r.method === "POST")).toEqual([
            { method: "POST", path: "/api/v1/operations/intent/retire" },
        ]);
        await page.reload();
        await expect(
            page.getByText(
                /Historical outcome unknown; request retired\. You may start a new job/u,
            ),
        ).toBeVisible();
        expect(
            fixture.requests.filter((r) => r.method === "POST"),
        ).toHaveLength(1);
        expect(
            fixture.requests.filter(
                (r) => r.path === "/api/v1/operations/intent",
            ),
        ).toHaveLength(2);
        const restored = await page.evaluate(() =>
            localStorage.getItem("hfcache.web.operations.v1"),
        );
        expect(restored).toContain(
            retainedId
                ? '"operationId":"' + "a".repeat(32) + '"'
                : '"operationId":null',
        );
        expect(fixture.unexpected).toEqual([]);
        expect(fixture.cspViolations).toEqual([]);
        expect(fixture.pageErrors).toEqual([]);
        await testInfo.attach("preserved-original-review", {
            contentType: "application/json",
            body: JSON.stringify({
                requests: fixture.requests,
                original: saved,
            }),
        });
    });
}

test("built authenticated reconciliation preserves a failed admitted original result without POST", async ({
    page,
}) => {
    const fixture = await sourceFixture(page, { jobs: "failed" });
    await page.goto(SOURCE_FIXTURE_ORIGIN + "/ui/operations");
    await expect(
        page.getByText(
            "Failed. The original admitted job result is preserved.",
            { exact: true },
        ),
    ).toBeVisible();
    expect(fixture.requests.filter((r) => r.method === "POST")).toHaveLength(0);
    expect(
        fixture.requests.filter((r) => r.path === "/api/v1/operations/intent"),
    ).toHaveLength(1);
    expect(
        fixture.requests.filter((r) => r.path.endsWith("/result")),
    ).toHaveLength(1);
    expect(fixture.unexpected).toEqual([]);
    expect(fixture.cspViolations).toEqual([]);
    expect(fixture.pageErrors).toEqual([]);
});
