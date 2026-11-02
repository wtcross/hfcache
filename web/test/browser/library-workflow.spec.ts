/** WEB029: browser disclosure/filter/navigation evidence on owned synthetic API. */
import { expect, test } from "@playwright/test";
import type { Page, TestInfo } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { SOURCE_FIXTURE_ORIGIN, sourceFixture } from "./source-fixture";

async function loaded(page: Page) {
    await expect(
        page.getByRole("button", { name: "Refresh library" }),
    ).toBeEnabled();
}
async function clean(
    page: Page,
    fixture: Awaited<ReturnType<typeof sourceFixture>>,
    testInfo: TestInfo,
    state: string,
) {
    const axe = await new AxeBuilder({ page }).analyze();
    await testInfo.attach(state, {
        contentType: "application/json",
        body: JSON.stringify(
            {
                state,
                viewport: page.viewportSize(),
                manifest: fixture.manifest,
                requests: fixture.requests,
                cspViolations: fixture.cspViolations,
                unexpected: fixture.unexpected,
                pageErrors: fixture.pageErrors,
                violations: axe.violations,
            },
            null,
            2,
        ),
    });
    expect(axe.violations).toEqual([]);
    expect(fixture.cspViolations).toEqual([]);
    expect(fixture.unexpected).toEqual([]);
    expect(fixture.pageErrors).toEqual([]);
    expect(fixture.requests.every((request) => request.method === "GET")).toBe(
        true,
    );
}

test("built Library disclosures preserve raw fields and reveal hidden invalid inputs", async ({
    page,
}, testInfo) => {
    const fixture = await sourceFixture(page, { library: true });
    await page.goto(
        SOURCE_FIXTURE_ORIGIN +
            "/ui/library#bits=4&format=gguf&tag_all=project%3Afixture&revision_scope=retained&tag_source=current_only",
    );
    await expect(
        page.getByRole("heading", {
            name: "No known matches; metadata coverage is incomplete",
        }),
    ).toBeVisible();
    await loaded(page);
    const summary = page
        .locator("summary")
        .filter({ hasText: "Filters and page size" });
    const details = summary.locator("..");
    const applied = page.getByLabel("Applied Library filters");
    await expect(details).not.toHaveAttribute("open", "");
    await expect(applied).toContainText("gguf");
    await expect(applied).toContainText("4");
    await expect(applied).toContainText("project:fixture");
    await expect(applied).toContainText("Retained publications");
    await expect(applied).toContainText("Current tags only");
    const disclosureReads = fixture.requests.length;
    for (const label of [
        "Operator tags",
        "Scope and coverage",
        "Session and interface",
    ]) {
        const control = page.locator("summary").filter({ hasText: label });
        await control.focus();
        await page.keyboard.press("Enter");
        await expect(control.locator("..")).toHaveAttribute("open", "");
        await page.keyboard.press("Enter");
        await expect(control.locator("..")).not.toHaveAttribute("open", "");
        await expect(control).toBeFocused();
        expect(fixture.requests).toHaveLength(disclosureReads);
    }
    const reads = fixture.requests.length,
        fragment = new URL(page.url()).hash;
    await summary.focus();
    await page.keyboard.press("Enter");
    await expect(details).toHaveAttribute("open", "");
    const bits = page.getByLabel("Bits", { exact: true });
    const maximum = page.getByLabel("Maximum variant bytes", { exact: true });
    await expect(bits).toHaveValue("4");
    await maximum.fill("1024");
    await bits.fill("-2");
    await expect(page.getByText(/Unsubmitted form edits\./u)).toBeVisible();
    await clean(page, fixture, testInfo, "expanded-raw-edits");
    await summary.focus();
    await page.keyboard.press("Enter");
    await expect(details).not.toHaveAttribute("open", "");
    await expect(summary).toBeFocused();
    await expect(bits).toHaveValue("-2");
    await expect(maximum).toHaveValue("1024");
    expect(new URL(page.url()).hash).toBe(fragment);
    expect(fixture.requests).toHaveLength(reads);
    await page
        .getByRole("button", { name: "Apply filters", exact: true })
        .click();
    await expect(details).toHaveAttribute("open", "");
    await expect(bits).toBeFocused();
    expect(fixture.requests).toHaveLength(reads);
    await bits.fill("4");
    await summary.click();
    await page
        .getByRole("button", { name: "Apply filters", exact: true })
        .click();
    await loaded(page);
    await expect(page).toHaveURL(/max_variant_bytes=1024/u);
    await expect(applied).toContainText("1024");
    await expect(page.getByText(/Unsubmitted form edits\./u)).toHaveCount(0);
    await page.getByRole("button", { name: "Datasets", exact: true }).click();
    await loaded(page);
    await expect(
        page.getByText("Model-only variant filters were cleared for datasets."),
    ).toBeVisible();
    await summary.click();
    await expect(bits).toBeDisabled();
    await expect(bits).toHaveValue("");
    expect(new URL(page.url()).hash).not.toContain("bits=");
    await page
        .getByRole("button", { name: "Clear filters", exact: true })
        .click();
    await expect(
        page.getByRole("link", { name: "model-00", exact: true }),
    ).toBeVisible();
    await loaded(page);
    await expect(page.getByLabel("Format", { exact: true })).toHaveValue("");
    await clean(page, fixture, testInfo, "cleared-filters");
});

test("built Library320px keeps warning, table keyboard access, selections and history", async ({
    page,
}, testInfo) => {
    const fixture = await sourceFixture(page, { library: true });
    await page.setViewportSize({ width: 320, height: 844 });
    await page.goto(SOURCE_FIXTURE_ORIGIN + "/ui/library");
    await expect(
        page.getByRole("link", { name: "model-00", exact: true }),
    ).toBeVisible();
    await loaded(page);
    const table = page.getByRole("region", {
        name: "Repository table, scroll horizontally on narrow screens",
    });
    await table.focus();
    await page.keyboard.press("ArrowRight");
    await expect
        .poll(() => table.evaluate((element) => element.scrollLeft))
        .toBeGreaterThan(0);
    await page
        .getByRole("checkbox", { name: "Select loaded page", exact: true })
        .check();
    await expect(
        page.getByText("25 selected from 25 loaded rows"),
    ).toBeVisible();
    await page
        .getByRole("button", { name: "Copy selectors", exact: true })
        .click();
    await page.getByRole("button", { name: "Next page", exact: true }).click();
    await expect(
        page.getByRole("link", { name: "model-25", exact: true }),
    ).toBeVisible();
    await loaded(page);
    await expect(
        page.getByText("0 selected from 25 loaded rows"),
    ).toBeVisible();
    await page
        .getByRole("button", { name: "Previous page", exact: true })
        .click();
    await expect(
        page.getByRole("link", { name: "model-00", exact: true }),
    ).toBeVisible();
    await loaded(page);
    const search = page.getByRole("searchbox", { name: "Find repositories" });
    await search.fill("owned-no-known-match");
    await expect(
        page.getByRole("heading", {
            name: "No known matches; metadata coverage is incomplete",
        }),
    ).toBeVisible();
    await loaded(page);
    await expect(
        page
            .getByText(
                "Coverage is incomplete. Zero known matches does not prove absence.",
                { exact: true },
            )
            .first(),
    ).toBeVisible();
    await clean(page, fixture, testInfo, "320px-zero-known-incomplete-warning");
    await page.goBack();
    await expect(search).toHaveValue("");
    await expect(
        page.getByRole("link", { name: "model-00", exact: true }),
    ).toBeVisible();
    await page.goForward();
    await expect(search).toHaveValue("owned-no-known-match");
    await expect(
        page.getByRole("heading", {
            name: "No known matches; metadata coverage is incomplete",
        }),
    ).toBeVisible();
    expect(
        await page.evaluate(() => document.documentElement.scrollWidth),
    ).toBe(320);
    await page.screenshot({
        path: testInfo.outputPath("library-after-320-warning.png"),
    });
    await clean(page, fixture, testInfo, "320px-history-restored");
});
