/** INV-001/021: real built Chromium, synthetic API; never installed acceptance. */
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import config from "../../../tests/fixtures/web_wire/config.json" with { type: "json" };
import { SOURCE_FIXTURE_ORIGIN, sourceFixture } from "./source-fixture";

for (const buffer of ["repository", "settings", "json"] as const) {
    test(`built dirty reload keeps ${buffer} raw values until successful same-base replacement`, async ({
        page,
    }, testInfo) => {
        const fixture = await sourceFixture(page);
        const phases: { phase: string; configGets: number; posts: number }[] =
            [];
        const checkpoint = (phase: string) => {
            phases.push({
                phase,
                configGets: fixture.configGets(),
                posts: fixture.requests.filter(
                    (request) => request.method === "POST",
                ).length,
            });
        };
        try {
            await page.goto(SOURCE_FIXTURE_ORIGIN + "/ui/administration");
            const editor = page.getByRole("region", {
                name: "Configuration and tags",
            });
            const reload = editor.getByRole("button", {
                name: "Reload installed configuration",
            });
            await editor
                .getByRole("button", { name: "Read installed configuration" })
                .click();
            await expect(reload).toBeEnabled();
            expect(fixture.configGets()).toBe(1);
            checkpoint("initial read");
            await editor
                .getByRole("button", {
                    name: "Edit model organization/model-name",
                })
                .click();
            await editor
                .getByLabel("Tags (one per line)")
                .fill("prepared-intent");
            await editor
                .getByRole("button", { name: "Update draft repository" })
                .click();
            await expect(
                editor.getByText("Current draft tags: prepared-intent"),
            ).toBeVisible();
            let raw;
            let text;
            switch (buffer) {
                case "repository":
                    await editor
                        .getByRole("button", {
                            name: "Edit model organization/model-name",
                        })
                        .click();
                    raw = editor.getByLabel("Tags (one per line)");
                    text = "  Raw unsaved TAG\nunfinished:";
                    break;
                case "settings":
                    await editor
                        .getByRole("button", { name: "Edit global settings" })
                        .click();
                    raw = editor.getByLabel("Maximum sync workers");
                    text = "007";
                    break;
                case "json":
                    await editor
                        .getByRole("button", { name: "Supported JSON view" })
                        .click();
                    raw = editor.getByLabel("Editable configuration JSON");
                    text = '{\n  "unfinished": ';
                    break;
            }
            await raw.fill(text);
            await reload.click();
            const dialog = page.getByRole("dialog", {
                name: "Replace unsaved configuration?",
            });
            const keep = dialog.getByRole("button", { name: "Keep editing" });
            const replace = dialog.getByRole("button", {
                name: "Reload and replace draft",
            });
            await expect(keep).toBeFocused();
            await page.keyboard.press("Shift+Tab");
            await expect(replace).toBeFocused();
            await page.keyboard.press("Tab");
            await expect(keep).toBeFocused();
            await page.keyboard.press("Escape");
            await expect(dialog).toHaveCount(0);
            await expect(reload).toBeFocused();
            await expect(raw).toHaveValue(text);
            expect(fixture.configGets()).toBe(1);
            checkpoint("Escape cancellation");
            await reload.click();
            await keep.click();
            await expect(reload).toBeFocused();
            expect(fixture.configGets()).toBe(1);
            checkpoint("Keep editing cancellation");

            const releaseFailure = fixture.deferRead("api");
            await reload.click();
            await replace.click();
            await expect.poll(fixture.configGets).toBe(2);
            await expect(raw).toHaveValue(text);
            await expect(raw).toBeDisabled();
            await expect(
                editor.getByText(config.read.base_revision),
            ).toBeVisible();
            await expect(
                editor.getByText("Current draft tags: prepared-intent"),
            ).toBeVisible();
            await expect(
                editor.getByRole("button", { name: "Validate draft" }),
            ).toBeDisabled();
            await page
                .getByRole("link", { name: "Library", exact: true })
                .click();
            const departure = page.getByRole("dialog", {
                name: "Unsaved configuration changes",
            });
            await expect(
                departure.getByRole("button", { name: "Stay" }),
            ).toBeFocused();
            await departure.getByRole("button", { name: "Stay" }).click();
            await expect(departure).toHaveCount(0);
            await expect(raw).toHaveValue(text);
            expect(fixture.configGets()).toBe(2);
            checkpoint("pending failed replacement");
            releaseFailure();
            await expect(
                editor.getByText(/Configuration reload failed\./u),
            ).toBeVisible();
            await expect(raw).toHaveValue(text);
            await expect(raw).toBeEnabled();
            await expect(
                editor.getByText(config.read.base_revision),
            ).toBeVisible();
            await expect(
                editor.getByText("Current draft tags: prepared-intent"),
            ).toBeVisible();
            checkpoint("failed replacement retains exact intent and buffer");
            await page.screenshot({
                path: testInfo.outputPath(`${buffer}-failed-reload.png`),
                fullPage: true,
            });

            const releaseSuccess = fixture.deferRead("success");
            await reload.click();
            await replace.click();
            await expect.poll(fixture.configGets).toBe(3);
            await expect(raw).toHaveValue(text);
            await expect(raw).toBeDisabled();
            releaseSuccess();
            await expect(raw).toHaveCount(0);
            await expect(
                editor.getByText("Current draft tags: coding"),
            ).toBeVisible();
            await expect(
                editor.getByText("Current draft tags: prepared-intent"),
            ).toHaveCount(0);
            await expect(
                editor.getByText(
                    /The editable draft matches its installed base/u,
                ),
            ).toBeVisible();
            await expect(
                editor.getByText(config.read.base_revision),
            ).toBeVisible();
            checkpoint("successful same-base atomic replacement");
            expect(
                fixture.requests.every((request) => request.method === "GET"),
            ).toBe(true);
            expect(fixture.unexpected).toEqual([]);
            expect(fixture.cspViolations).toEqual([]);
            expect(fixture.pageErrors).toEqual([]);
            const accessibility = await new AxeBuilder({ page }).analyze();
            expect(
                accessibility.violations.filter(
                    (item) =>
                        item.impact === "serious" || item.impact === "critical",
                ),
            ).toEqual([]);
        } finally {
            fixture.releasePendingReads();
            await testInfo.attach("owned-source-draft-reload-evidence", {
                contentType: "application/json",
                body: JSON.stringify(
                    {
                        scope: "built source Chromium; routed synthetic HTTPS/API fixtures; no installed/native/rootless/production acceptance",
                        buffer,
                        viewport: page.viewportSize(),
                        manifest: fixture.manifest,
                        phases,
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
}
