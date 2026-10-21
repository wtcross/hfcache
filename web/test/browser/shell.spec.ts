import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("built main refuses unavailable bootstrap and preserves a keyboard reload", async ({
    page,
    baseURL,
}) => {
    if (baseURL === undefined)
        throw new Error("The owned loopback refusal fixture is required.");
    const external: string[] = [],
        bootstraps: string[] = [];
    page.on("request", (request) => {
        if (!request.url().startsWith(baseURL + "/"))
            external.push(request.url());
        if (request.url().endsWith("/bootstrap.json"))
            bootstraps.push(request.url());
    });
    await page.goto("/ui/");
    await expect(
        page.getByRole("heading", { level: 1, name: "Starting hfcache" }),
    ).toBeVisible();
    await expect(
        page.getByText(
            "The interface could not start. Reload the interface or contact your operator.",
            { exact: true },
        ),
    ).toBeVisible();
    await expect(
        page.getByText("Administrator session", { exact: true }),
    ).toHaveCount(0);
    await expect(page.getByRole("navigation")).toHaveCount(0);
    await page.keyboard.press("Tab");
    const reload = page.getByRole("link", { name: "Reload interface" });
    await expect(reload).toBeFocused();
    await expect(reload).toHaveAttribute("href", "./");
    expect(bootstraps).toEqual([baseURL + "/ui/bootstrap.json"]);
    expect(external).toEqual([]);
    const accessibility = await new AxeBuilder({ page }).analyze();
    expect(
        accessibility.violations.filter(
            (item) => item.impact === "serious" || item.impact === "critical",
        ),
    ).toEqual([]);
});

test("missing built main chunk preserves inert fallback on a narrow viewport", async ({
    page,
    baseURL,
}) => {
    if (baseURL === undefined)
        throw new Error("The owned loopback refusal fixture is required.");
    const missing: string[] = [],
        bootstraps: string[] = [];
    page.on("response", (response) => {
        if (response.url().endsWith(".js") && response.status() === 404)
            missing.push(response.url());
    });
    page.on("request", (request) => {
        if (request.url().endsWith("/bootstrap.json"))
            bootstraps.push(request.url());
    });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/missing-script/ui/");
    await expect(
        page.getByRole("heading", { level: 1, name: "Starting hfcache" }),
    ).toBeVisible();
    await expect(
        page.getByText(/The interface has not started\./),
    ).toBeVisible();
    await expect(
        page.getByRole("link", { name: "Reload interface" }),
    ).toBeVisible();
    await expect(page.getByRole("navigation")).toHaveCount(0);
    expect(missing).toHaveLength(1);
    expect(bootstraps).toEqual([]);
    expect(
        await page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
    ).toBe(true);
    const accessibility = await new AxeBuilder({ page }).analyze();
    expect(
        accessibility.violations.filter(
            (item) => item.impact === "serious" || item.impact === "critical",
        ),
    ).toEqual([]);
});
