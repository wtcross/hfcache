import { expect, test } from "vitest";
import {
    requirePassingBrowserReport,
    requirePassingReport,
} from "../scripts/test-report";

const report = {
    success: true,
    numTotalTests: 1,
    numPassedTests: 1,
    numFailedTests: 0,
    numPendingTests: 0,
    numTodoTests: 0,
    testResults: [{ assertionResults: [{ status: "passed" }] }],
};

test("a nonempty all-passing suite establishes execution", () => {
    expect(requirePassingReport(report)).toBe(1);
});

test.each(["pending", "skipped", "todo", "failed", "unknown"])(
    "required test state %s refuses acceptance",
    (status) => {
        expect(() =>
            requirePassingReport({
                ...report,
                testResults: [{ assertionResults: [{ status }] }],
            }),
        ).toThrow();
    },
);

test.each([
    null,
    [],
    {},
    { ...report, success: false },
    { ...report, testResults: [null] },
    { ...report, testResults: [{ assertionResults: [null] }] },
    { ...report, numTotalTests: 2 },
    { ...report, numPendingTests: 1 },
    { ...report, numTodoTests: 1 },
    { ...report, testResults: [], numTotalTests: 0, numPassedTests: 0 },
])("malformed, skipped or empty reports refuse acceptance", (value) => {
    expect(() => requirePassingReport(value)).toThrow();
});

const browser = {
    stats: { expected: 1, unexpected: 0, flaky: 0, skipped: 0 },
    suites: [
        {
            specs: [
                {
                    ok: true,
                    tests: [
                        { status: "expected", results: [{ status: "passed" }] },
                    ],
                },
            ],
        },
    ],
};
test("browser evidence requires one execution with no skip, retry or report inconsistency", () => {
    expect(requirePassingBrowserReport(browser)).toBe(1);
    for (const value of [
        null,
        {},
        { ...browser, stats: { ...browser.stats, skipped: 1 } },
        { ...browser, stats: { ...browser.stats, flaky: 1 } },
        { ...browser, suites: [] },
        {
            ...browser,
            suites: [
                {
                    specs: [
                        {
                            ok: true,
                            tests: [
                                {
                                    status: "expected",
                                    results: [{ status: "skipped" }],
                                },
                            ],
                        },
                    ],
                },
            ],
        },
    ]) {
        expect(() => requirePassingBrowserReport(value)).toThrow();
    }
});
