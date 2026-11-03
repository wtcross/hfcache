/** WEB029: own full Chromium and actual tab zoom; synthetic source fixture only. */
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { isAbsolute, join } from "node:path";
import type { BrowserContext } from "@playwright/test";
import {
    SOURCE_FIXTURE_ORIGIN,
    sourceFixture,
} from "../test/browser/source-fixture.ts";

declare const chrome: {
    tabs: {
        query(query: { url: string }): Promise<{ id?: number }[]>;
        getZoom(tabId: number): Promise<number>;
        setZoom(tabId: number, zoom: number): Promise<void>;
        setZoomSettings(
            tabId: number,
            settings: { mode: string; scope: string },
        ): Promise<void>;
        getZoomSettings(tabId: number): Promise<unknown>;
    };
};

const root = fileURLToPath(new URL("../", import.meta.url));
const cache =
    process.env.PLAYWRIGHT_BROWSERS_PATH ?? join(root, ".cache/ms-playwright");
if (!isAbsolute(cache))
    throw new Error("An absolute owned browser cache is required.");
process.env.PLAYWRIGHT_BROWSERS_PATH = cache;
const { chromium, expect } = await import("@playwright/test");
const { default: AxeBuilder } = await import("@axe-core/playwright");
const executable = chromium.executablePath();
if (!existsSync(executable))
    throw new Error(
        "Provision the pinned full Chromium separately; no download or skipped zoom acceptance.",
    );
if (process.argv.length !== 2)
    throw new Error("Run test:library-zoom without arguments.");
mkdirSync(join(root, ".artifacts"), { recursive: true });
const evidence = mkdtempSync(join(root, ".artifacts/library-zoom-"));
const extension = join(evidence, "extension");
mkdirSync(extension);
writeFileSync(
    join(extension, "manifest.json"),
    JSON.stringify({
        manifest_version: 3,
        name: "Owned Library zoom fixture",
        version: "1.0",
        permissions: ["tabs"],
        background: { service_worker: "worker.js" },
    }),
);
writeFileSync(
    join(extension, "worker.js"),
    "chrome.runtime.onInstalled.addListener(() => {});\n",
);
let context: BrowserContext | undefined;
let pid: number | undefined;
let closeObserved = false;
let procAbsent = false;
let force: ReturnType<typeof setTimeout> | undefined;
const lifecycle = { interrupted: false };
function wasInterrupted() {
    return lifecycle.interrupted;
}
let fixture: Awaited<ReturnType<typeof sourceFixture>> | undefined;
const results: Record<string, unknown> = {
    scope: "built source full Chromium; actual extension tabs.setZoom/getZoom; synthetic HTTPS/API fixture; no installed/production acceptance",
    executable,
    mechanism:
        "chrome.tabs.setZoom(tabId,2), with independent chrome.tabs.getZoom(tabId) confirmation; no CSS zoom, pinch zoom or deviceScaleFactor override",
    requestedViewport: { width: 640, height: 1000 },
    sandboxEnabled: true,
};
async function boundedClose(operation: Promise<void>) {
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
        await Promise.race([
            operation,
            new Promise<never>((_resolve, reject) => {
                timer = setTimeout(() => {
                    reject(
                        new Error(
                            "Owned zoom browser closure exceeded five seconds.",
                        ),
                    );
                }, 5000);
            }),
        ]);
    } finally {
        clearTimeout(timer);
    }
}
function stopOwnedBrowser() {
    lifecycle.interrupted = true;
    process.exitCode = 1;
    if (pid !== undefined && existsSync(`/proc/${String(pid)}`)) {
        process.kill(pid, "SIGTERM");
        force ??= setTimeout(() => {
            if (pid !== undefined && existsSync(`/proc/${String(pid)}`))
                process.kill(pid, "SIGKILL");
        }, 5000);
    }
}
process.on("SIGTERM", stopOwnedBrowser);
process.on("SIGINT", stopOwnedBrowser);
const deadline = setTimeout(stopOwnedBrowser, 90000);
try {
    context = await chromium.launchPersistentContext(
        join(evidence, "profile"),
        {
            executablePath: executable,
            channel: "chromium",
            headless: true,
            chromiumSandbox: true,
            viewport: { width: 640, height: 1000 },
            timeout: 15000,
            args: [
                `--disable-extensions-except=${extension}`,
                `--load-extension=${extension}`,
            ],
        },
    );
    const browser = context.browser();
    if (browser === null)
        throw new Error("Owned full Chromium process observation unavailable.");
    const session = await browser.newBrowserCDPSession();
    const processes = await session.send("SystemInfo.getProcessInfo");
    pid = processes.processInfo.find(
        (process) => process.type === "browser",
    )?.id;
    if (pid === undefined)
        throw new Error("Owned zoom browser PID unavailable.");
    if (wasInterrupted()) {
        stopOwnedBrowser();
        throw new Error(
            "Owned actual-zoom check interrupted before admission.",
        );
    }
    console.log(
        `Owned actual-zoom Chromium PID ${String(pid)}; sandbox enabled. Evidence ${evidence}.`,
    );
    const worker =
        context.serviceWorkers()[0] ??
        (await context.waitForEvent("serviceworker", { timeout: 10000 }));
    const page = context.pages()[0] ?? (await context.newPage());
    fixture = await sourceFixture(page, { library: true, jobs: "empty" });
    await page.goto(SOURCE_FIXTURE_ORIGIN + "/ui/library");
    await expect(
        page.getByRole("link", { name: "model-00", exact: true }),
    ).toBeVisible();
    await expect(
        page.getByRole("button", { name: "Refresh library" }),
    ).toBeEnabled();
    const metrics = () =>
        page.evaluate(() => ({
            innerWidth,
            innerHeight,
            outerWidth,
            outerHeight,
            dpr: devicePixelRatio,
            visualScale: visualViewport?.scale,
            visualWidth: visualViewport?.width,
            cssZoom: getComputedStyle(document.documentElement).zoom,
            scrollWidth: document.documentElement.scrollWidth,
        }));
    results.before = await metrics();
    const zoom = await worker.evaluate(async (origin) => {
        const tabs = await chrome.tabs.query({ url: origin + "/ui/library*" });
        const tabId = tabs[0]?.id;
        if (tabs.length !== 1 || tabId === undefined)
            throw new Error("Owned Library tab identity mismatch.");
        const before = await chrome.tabs.getZoom(tabId);
        await chrome.tabs.setZoomSettings(tabId, {
            mode: "automatic",
            scope: "per-tab",
        });
        await chrome.tabs.setZoom(tabId, 2);
        return {
            tabId,
            before,
            after: await chrome.tabs.getZoom(tabId),
            settings: await chrome.tabs.getZoomSettings(tabId),
        };
    }, SOURCE_FIXTURE_ORIGIN);
    results.zoom = zoom;
    await expect.poll(() => page.evaluate(() => innerWidth)).toBe(320);
    const after = await metrics();
    results.after = after;
    expect(zoom.before).toBe(1);
    expect(zoom.after).toBe(2);
    expect(after.innerWidth).toBe(320);
    expect(after.innerHeight).toBe(500);
    expect(after.visualScale).toBe(1);
    expect(after.cssZoom).toBe("1");
    expect(after.scrollWidth).toBe(320);
    await page.screenshot({
        path: join(evidence, "library-actual200percent-320css.png"),
    });
    const summary = page
        .locator("summary")
        .filter({ hasText: "Filters and page size" });
    await summary.focus();
    await page.keyboard.press("Enter");
    await expect(summary.locator("..")).toHaveAttribute("open", "");
    const bits = page.getByLabel("Bits", { exact: true });
    await bits.fill("invalid");
    await summary.click();
    await page
        .getByRole("button", { name: "Apply filters", exact: true })
        .click();
    await expect(bits).toBeFocused();
    await bits.fill("");
    await page
        .getByRole("button", { name: "Clear filters", exact: true })
        .click();
    await expect(
        page.getByRole("button", { name: "Refresh library" }),
    ).toBeEnabled();
    await expect(
        page
            .getByText(
                "Coverage is incomplete. Zero known matches does not prove absence.",
                { exact: true },
            )
            .first(),
    ).toBeVisible();
    const table = page.getByRole("region", {
        name: "Repository table, scroll horizontally on narrow screens",
    });
    await table.focus();
    await page.keyboard.press("ArrowRight");
    await expect
        .poll(() => table.evaluate((element) => element.scrollLeft))
        .toBeGreaterThan(0);
    await page.getByRole("button", { name: "Next page", exact: true }).click();
    await expect(
        page.getByRole("link", { name: "model-25", exact: true }),
    ).toBeVisible();
    await page
        .getByRole("button", { name: "Previous page", exact: true })
        .click();
    await expect(
        page.getByRole("link", { name: "model-00", exact: true }),
    ).toBeVisible();
    fixture.setJobReadiness({ archive: false });
    await page
        .getByRole("button", { name: "Open navigation", exact: true })
        .focus();
    await page.keyboard.press("Enter");
    await page.getByRole("link", { name: "Operations", exact: true }).focus();
    await page.keyboard.press("Enter");
    await page.getByRole("button", { name: /^Job: /u }).click();
    await page.getByRole("option", { name: "Sync", exact: true }).click();
    const submitJob = page.getByRole("button", {
        name: "Submit job",
        exact: true,
    });
    await expect(submitJob).toBeDisabled();
    await expect(submitJob).toHaveAccessibleDescription(
        "Unavailable: archive writes are disabled.",
    );
    const recheckJob = page.getByRole("button", {
        name: "Recheck job readiness",
    });
    await recheckJob.focus();
    await page.keyboard.press("Enter");
    await expect(recheckJob).toBeEnabled();
    expect((await metrics()).scrollWidth).toBe(320);
    results.jobsAt200Percent = await metrics();
    await page.screenshot({
        path: join(evidence, "jobs-actual200percent-320css.png"),
        fullPage: true,
    });
    const accessibility = await new AxeBuilder({ page }).analyze();
    results.violations = accessibility.violations;
    expect(accessibility.violations).toEqual([]);
    expect(fixture.requests.every((request) => request.method === "GET")).toBe(
        true,
    );
    expect(fixture.cspViolations).toEqual([]);
    expect(fixture.pageErrors).toEqual([]);
    expect(fixture.unexpected).toEqual([]);
    if (wasInterrupted())
        throw new Error("Owned actual-zoom check was interrupted.");
    results.passed = true;
    console.log(
        "Actual browser200% Library zoom and320CSS control/keyboard/scroll/pagination checks passed; source fixture only.",
    );
} catch (error) {
    results.passed = false;
    results.failure = error instanceof Error ? error.message : String(error);
    process.exitCode = 1;
    console.error(error);
} finally {
    clearTimeout(deadline);
    try {
        if (context !== undefined) {
            try {
                await boundedClose(context.close());
            } catch (error) {
                results.passed = false;
                results.closureFailure =
                    error instanceof Error ? error.message : String(error);
                stopOwnedBrowser();
                await boundedClose(context.close());
            }
            closeObserved = true;
            procAbsent =
                pid !== undefined && !existsSync(`/proc/${String(pid)}`);
            if (!procAbsent)
                throw new Error(
                    "Owned zoom browser PID remains after closure.",
                );
        }
    } finally {
        clearTimeout(force);
        process.off("SIGTERM", stopOwnedBrowser);
        process.off("SIGINT", stopOwnedBrowser);
        writeFileSync(
            join(evidence, "result.json"),
            JSON.stringify(
                {
                    ...results,
                    pid,
                    closeObserved,
                    procAbsent,
                    manifest: fixture?.manifest,
                    requests: fixture?.requests,
                    unexpected: fixture?.unexpected,
                    cspViolations: fixture?.cspViolations,
                    pageErrors: fixture?.pageErrors,
                },
                null,
                2,
            ) + "\n",
        );
        console.log(
            `Owned actual-zoom Chromium closed ${String(closeObserved)}; PID absent ${String(procAbsent)}.`,
        );
    }
}
