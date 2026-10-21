import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const prefix = process.env.HFCACHE_READ_FIXTURE_PREFIX;
if (prefix !== "" && prefix !== "/management")
    throw new Error("Use the explicitly owned fixture prefix profiles.");
const entry = prefix + "/ui/";
const api = prefix + "/api/v1/";

test.beforeEach(async ({ page, baseURL }) => {
    if (baseURL === undefined) throw new Error("Owned origin missing.");
    await page.route("**/*", async (route) => {
        const url = new URL(route.request().url());
        if (url.origin !== baseURL) {
            await route.abort();
            throw new Error("A fixture attempted an external request.");
        }
        await route.continue();
    });
});

test("actual status preserves unavailable archive and zero loaded rows without inventing capacity", async ({
    page,
}) => {
    const response = page.waitForResponse(
        (reply) => new URL(reply.url()).pathname === api + "status",
    );
    await page.goto(entry);
    expect((await response).status()).toBe(200);
    await expect(
        page.getByRole("heading", { name: "Server status" }),
    ).toBeVisible();
    await expect(page.getByRole("status")).toHaveText(
        /0 loaded repositories\. Archive unavailable\./u,
    );
    await expect(page.getByTestId("read-request-id")).toHaveText(
        /^[a-f0-9]{32}$/u,
    );
    const first = await page.getByTestId("read-request-id").textContent();
    await page.getByRole("button", { name: "Refresh read" }).click();
    await expect(page.getByTestId("read-request-id")).not.toHaveText(
        first ?? "",
    );
    const axe = await new AxeBuilder({ page }).analyze();
    expect(
        axe.violations.filter(
            (item) => item.impact === "serious" || item.impact === "critical",
        ),
    ).toEqual([]);
});

test("actual version and capabilities are rendered through generated typed reads", async ({
    page,
}) => {
    await page.goto(entry + "?source=version");
    await expect(
        page.getByRole("heading", { name: "Server version" }),
    ).toBeVisible();
    await expect(page.getByRole("status")).toContainText("Application ");
    await page.goto(entry + "?source=capabilities");
    await expect(
        page.getByRole("heading", { name: "Server capabilities" }),
    ).toBeVisible();
    await expect(page.getByRole("status")).toContainText(
        "Maintenance disabled.",
    );
});

test("original Python-serialized models roundtrip and independent incorrect wires reject", async ({
    page,
}) => {
    await page.goto(entry + "?source=roundtrip");
    await expect(
        page.getByRole("heading", { name: "Original model roundtrip" }),
    ).toBeVisible();
    await expect(page.getByRole("status")).toHaveText(
        "Original Python models validated: 297. Independent incorrect wires refused: 4.",
    );
});

test("genuine failed HTTP200 inspection retains domain error codes", async ({
    page,
}) => {
    const response = page.waitForResponse(
        (reply) => new URL(reply.url()).pathname === api + "archive/inspection",
    );
    await page.goto(entry + "?source=inspection");
    expect((await response).status()).toBe(200);
    await expect(
        page.getByRole("heading", { name: "Read failed" }),
    ).toBeVisible();
    await expect(
        page.getByRole("list", { name: "Original diagnostic codes" }),
    ).toContainText("HFMNT");
});

test("genuine invalid installed fixture policy produces a classified503 unavailable view", async ({
    page,
    request,
}) => {
    const changed = await request.post(prefix + "/__fixture__/policy-invalid", {
        headers: { "X-Hfcache-Fixture": "1" },
    });
    expect(changed.status()).toBe(200);
    try {
        const response = page.waitForResponse(
            (reply) => new URL(reply.url()).pathname === api + "status",
        );
        await page.goto(entry);
        expect((await response).status()).toBe(503);
        await expect(
            page.getByRole("heading", { name: "API unavailable" }),
        ).toBeVisible();
        await expect(
            page.getByRole("list", { name: "Original diagnostic codes" }),
        ).toContainText("HFCFG002");
    } finally {
        expect(
            (
                await request.post(prefix + "/__fixture__/policy-restore", {
                    headers: { "X-Hfcache-Fixture": "1" },
                })
            ).status(),
        ).toBe(200);
    }
});

test("labelled post-service schema corruption displays unsupported rather than server facts", async ({
    page,
}) => {
    // Actual auth + version service execute; only its completed wire is corrupted.
    await page.setExtraHTTPHeaders({
        "X-Hfcache-Fixture-Fault": "schema-version",
    });
    await page.goto(entry + "?source=version");
    await expect(
        page.getByRole("heading", { name: "Unsupported response" }),
    ).toBeVisible();
    await expect(page.getByRole("alert")).toContainText(
        "No server facts have been inferred.",
    );
});

test("actual API authentication refuses a context without the generated bearer", async ({
    browser,
    baseURL,
}) => {
    if (baseURL === undefined) throw new Error("Owned origin missing.");
    const context = await browser.newContext({ baseURL, extraHTTPHeaders: {} });
    try {
        const page = await context.newPage();
        await page.route("**/*", async (route) => {
            if (new URL(route.request().url()).origin !== baseURL)
                await route.abort();
            else {
                expect(route.request().headers()).not.toHaveProperty(
                    "authorization",
                );
                await route.continue();
            }
        });
        const response = page.waitForResponse(
            (reply) => new URL(reply.url()).pathname === api + "status",
        );
        await page.goto(entry);
        expect((await response).status()).toBe(401);
        await expect(
            page.getByRole("heading", { name: "Access refused" }),
        ).toBeVisible();
    } finally {
        await context.close();
    }
});
