/** Required suites cannot turn an empty or skipped execution into acceptance. */
function record(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function requirePassingReport(value: unknown): number {
    if (
        !record(value) ||
        value.success !== true ||
        !Array.isArray(value.testResults)
    ) {
        throw new Error("The required test report is missing or malformed.");
    }
    let count = 0;
    for (const suite of value.testResults) {
        if (!record(suite) || !Array.isArray(suite.assertionResults)) {
            throw new Error("The required suite report is malformed.");
        }
        for (const assertion of suite.assertionResults) {
            if (!record(assertion) || assertion.status !== "passed") {
                throw new Error(
                    "Required tests cannot be skipped, pending, failed or todo.",
                );
            }
            count += 1;
        }
    }
    if (
        count === 0 ||
        value.numTotalTests !== count ||
        value.numPassedTests !== count ||
        value.numFailedTests !== 0 ||
        value.numPendingTests !== 0 ||
        value.numTodoTests !== 0
    ) {
        throw new Error("The required test report is empty or inconsistent.");
    }
    return count;
}

export function requirePassingBrowserReport(value: unknown): number {
    if (
        !record(value) ||
        !record(value.stats) ||
        !Array.isArray(value.suites) ||
        typeof value.stats.expected !== "number" ||
        value.stats.expected < 1 ||
        value.stats.unexpected !== 0 ||
        value.stats.flaky !== 0 ||
        value.stats.skipped !== 0
    ) {
        throw new Error(
            "The required browser report is empty, skipped, flaky or malformed.",
        );
    }
    let passed = 0;
    function inspect(suites: unknown[]) {
        for (const suite of suites) {
            if (!record(suite) || !Array.isArray(suite.specs))
                throw new Error("Malformed browser suite.");
            for (const spec of suite.specs) {
                if (
                    !record(spec) ||
                    spec.ok !== true ||
                    !Array.isArray(spec.tests)
                )
                    throw new Error("Malformed browser specification.");
                for (const result of spec.tests) {
                    if (
                        !record(result) ||
                        result.status !== "expected" ||
                        !Array.isArray(result.results) ||
                        result.results.length !== 1 ||
                        !record(result.results[0]) ||
                        result.results[0].status !== "passed"
                    )
                        throw new Error(
                            "Required browser test did not pass once.",
                        );
                    passed += 1;
                }
            }
            if (suite.suites !== undefined) {
                if (!Array.isArray(suite.suites))
                    throw new Error("Malformed nested browser suite.");
                inspect(suite.suites);
            }
        }
    }
    inspect(value.suites);
    if (passed !== value.stats.expected)
        throw new Error("Inconsistent browser test count.");
    return passed;
}
