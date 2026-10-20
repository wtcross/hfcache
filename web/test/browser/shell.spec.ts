import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("built shell supports keyboard workspaces, deep reload and exact not-found routes", async ({
    page,
    baseURL,
}) => {
    if (baseURL === undefined)
        throw new Error("The owned loopback fixture is required.");
    const failures: string[] = [];
    await page.route("**/*", async (route) => {
        if (
            !route
                .request()
                .url()
                .startsWith(baseURL + "/")
        ) {
            failures.push("Forbidden external request.");
            await route.abort();
        } else await route.continue();
    });
    page.on("pageerror", (error) => {
        failures.push(error.message);
    });
    page.on("request", (request) => {
        if (!request.url().startsWith(baseURL + "/"))
            failures.push("Unexpected external request.");
    });
    await page.goto("/ui/");
    await expect(
        page.getByRole("heading", { level: 1, name: "Library" }),
    ).toBeVisible();
    await expect(page.getByText("Archive not connected")).toBeVisible();
    await page.keyboard.press("Tab");
    await expect(
        page.getByRole("link", { name: "Skip to content" }),
    ).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("main")).toBeFocused();
    for (const label of [
        "Operations",
        "Maintenance",
        "Administration",
        "Library",
    ]) {
        const link = page.getByRole("link", { name: label });
        await page.goto("/ui/");
        const tabCount =
            ["Library", "Operations", "Maintenance", "Administration"].indexOf(
                label,
            ) + 2;
        for (let step = 0; step < tabCount; step += 1)
            await page.keyboard.press("Tab");
        await expect(link).toBeVisible();
        await expect(link).toBeFocused();
        await page.keyboard.press("Enter");
        await expect(
            page.getByRole("heading", { level: 1, name: label }),
        ).toBeVisible();
        await expect(page.getByRole("main")).toBeFocused();
        await expect(link).toHaveAttribute("aria-current", "page");
        await page.reload();
        await expect(
            page.getByRole("heading", { level: 1, name: label }),
        ).toBeVisible();
    }
    for (const path of [
        "/ui/assets/missing.js",
        "/api/v1/missing",
        "/mcp/",
        "/ui/assets/../index.html",
    ]) {
        const response = await page.request.get(path);
        expect(response.status()).toBe(404);
    }
    const accessibility = await new AxeBuilder({ page }).analyze();
    expect(
        accessibility.violations.filter(
            (violation) =>
                violation.impact === "serious" ||
                violation.impact === "critical",
        ),
    ).toEqual([]);
    expect(failures).toEqual([]);
});

test("built mobile shell reveals labelled navigation without horizontal overflow", async ({
    page,
    baseURL,
}) => {
    if (baseURL === undefined)
        throw new Error("The owned loopback fixture is required.");
    const external: string[] = [];
    await page.route("**/*", async (route) => {
        if (
            !route
                .request()
                .url()
                .startsWith(baseURL + "/")
        ) {
            external.push("Forbidden external request.");
            await route.abort();
        } else await route.continue();
    });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/ui/");
    await expect(page.getByRole("navigation")).toBeHidden();
    await page.getByRole("button", { name: "Open navigation" }).click();
    await expect(page.getByRole("navigation")).toBeVisible();
    await page.getByRole("link", { name: "Operations" }).click();
    await expect(
        page.getByRole("heading", { level: 1, name: "Operations" }),
    ).toBeVisible();
    await expect(
        page.getByRole("button", { name: "Open navigation" }),
    ).toHaveAttribute("aria-expanded", "false");
    expect(
        await page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
    ).toBe(true);
    const accessibility = await new AxeBuilder({ page }).analyze();
    expect(
        accessibility.violations.filter(
            (violation) =>
                violation.impact === "serious" ||
                violation.impact === "critical",
        ),
    ).toEqual([]);
    expect(external).toEqual([]);
});
