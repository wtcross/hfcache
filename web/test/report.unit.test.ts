import { expect, test } from "vitest";
import {
    requirePassingBrowserReport,
    requirePassingReport,
    requirePassingTap,
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

const tap =
    "TAP version 13\nok 1 - actual test\n1..1\n# tests 1\n# pass 1\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n";
test("required Node execution rejects empty, failed, skipped, todo and contradictory TAP", () => {
    expect(requirePassingTap(tap)).toBe(1);
    for (const text of [
        "",
        tap.replace("# tests 1", "# tests 0"),
        tap.replace("# pass 1", "# pass 0"),
        tap.replace("# fail 0", "# fail 1"),
        tap.replace("# cancelled 0", "# cancelled 1"),
        tap.replace("# skipped 0", "# skipped 1"),
        tap.replace("# todo 0", "# todo 1"),
        tap.replace("ok 1", "not ok 1"),
        tap + "# skipped 0\n",
        tap.replace("actual test", "actual test # SKIP"),
        tap.replace("# todo 0\n", ""),
    ])
        expect(() => requirePassingTap(text)).toThrow();
});

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
