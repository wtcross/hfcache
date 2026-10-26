/** ADR155: independent work-boundary and upstream-navigation adversaries. */
import { performance } from "node:perf_hooks";
import { describe, expect, test, vi } from "vitest";
import type { ExactPublication } from "../src/api/identity";
import {
    readmeAdmission,
    readmeIdPrefix,
    readmeLink,
} from "../src/readme/policy";

const model: ExactPublication = {
    repositoryType: "model",
    repositoryId: "owner/name",
    commitSha: "a".repeat(40),
    publicationId: "b".repeat(32),
};
const dataset: ExactPublication = { ...model, repositoryType: "dataset" };
const modelRoot =
    "https://huggingface.co/owner/name/blob/" + model.commitSha + "/";
const datasetRoot =
    "https://huggingface.co/datasets/owner/name/blob/" + model.commitSha + "/";

describe("finite README admission before the synchronous parser", () => {
    test("ordinary prose, a leading horizontal rule, fenced literals and Unicode are admitted without changing bytes", () => {
        const source =
            "---\n# Owned card\n\nこんにちは 🙂\n\n- A\n- B\n\n```html\n<script>literal()</script>\n```\n";
        expect(readmeAdmission(source)).toEqual({ allowed: true });
        expect(source.startsWith("---\n")).toBe(true);
        expect(readmeAdmission("")).toEqual({ allowed: true });
    });
    test("64KiB measures UTF8 rather than JavaScript string units", () => {
        const exact = ("🙂".repeat(1023) + "\n").repeat(16) + "x".repeat(48);
        expect(new TextEncoder().encode(exact)).toHaveLength(65536);
        expect(readmeAdmission(exact)).toEqual({ allowed: true });
        expect(readmeAdmission(exact + "🙂")).toEqual({
            allowed: false,
            reason: "input_bytes",
        });
        expect(readmeAdmission("x".repeat(65537))).toEqual({
            allowed: false,
            reason: "input_bytes",
        });
    });
    test("invalid UTF16 is refused before replacement encoding can claim verified content", () => {
        for (const source of ["\ud800", "text\udfff", "\ud800x\udc00"])
            expect(readmeAdmission(source)).toEqual({
                allowed: false,
                reason: "invalid_source",
            });
    });
    test("2048 lines include the final empty line and CRLF is one boundary", () => {
        expect(readmeAdmission("\n".repeat(2047))).toEqual({ allowed: true });
        expect(readmeAdmission("\r\n".repeat(2047))).toEqual({ allowed: true });
        expect(readmeAdmission("\r".repeat(2048))).toEqual({
            allowed: false,
            reason: "lines",
        });
    });
    test("a line has at most4096 Unicode characters, independent of byte length", () => {
        expect(readmeAdmission("🙂".repeat(4096))).toEqual({ allowed: true });
        expect(readmeAdmission("🙂".repeat(4097))).toEqual({
            allowed: false,
            reason: "line_length",
        });
    });
    test("nested quotes, minimal list indentation and bracket work stop at8", () => {
        for (const source of [
            "> ".repeat(8) + "text",
            " ".repeat(14) + "- item",
            "[".repeat(8) + "text" + "]".repeat(8),
        ])
            expect(readmeAdmission(source)).toEqual({ allowed: true });
        for (const source of [
            "> ".repeat(9) + "text",
            " ".repeat(16) + "- item",
            "[".repeat(9) + "text",
        ])
            expect(readmeAdmission(source)).toEqual({
                allowed: false,
                reason: "nesting",
            });
    });
    test("4096 structural delimiters are bounded globally across individually short lines", () => {
        const exact = ".".repeat(2048) + "\n" + ".".repeat(2048);
        expect(readmeAdmission(exact)).toEqual({ allowed: true });
        expect(readmeAdmission(exact + ".")).toEqual({
            allowed: false,
            reason: "delimiters",
        });
    });
    test("headings and fence blocks share a finite128-block admission budget", () => {
        expect(readmeAdmission("# Heading\n".repeat(128))).toEqual({
            allowed: true,
        });
        expect(readmeAdmission("# Heading\n".repeat(129))).toEqual({
            allowed: false,
            reason: "blocks",
        });
        expect(readmeAdmission("```\n```\n".repeat(128))).toEqual({
            allowed: true,
        });
        expect(readmeAdmission("```\n```\n".repeat(128) + "# Heading")).toEqual(
            { allowed: false, reason: "blocks" },
        );
    });
    test("16KiB code blocks do not inherit the larger overall input allowance", () => {
        const exact = ("x".repeat(4095) + "\n").repeat(4);
        expect(readmeAdmission("```text\n" + exact + "```")).toEqual({
            allowed: true,
        });
        const crlf = ("x".repeat(4094) + "\r\n").repeat(4);
        expect(readmeAdmission("```text\r\n" + crlf + "```")).toEqual({
            allowed: true,
        });
        expect(
            readmeAdmission("~~~\n" + exact.slice(0, -1) + "x\n~~~"),
        ).toEqual({ allowed: false, reason: "code_block" });
        const indented = ("    " + "x".repeat(4091) + "\n").repeat(4);
        expect(readmeAdmission(indented)).toEqual({ allowed: true });
        expect(readmeAdmission(indented.slice(0, -1) + "x\n")).toEqual({
            allowed: false,
            reason: "code_block",
        });
    });
    test("adjacent indented fence-looking chunks are charged as one code block before parsing", () => {
        const chunk =
            "    ```\n" +
            ("    " + "x".repeat(4091) + "\n").repeat(3) +
            "    ```\n";
        expect(new TextEncoder().encode(chunk).length).toBeLessThan(16384);
        expect(new TextEncoder().encode(chunk + chunk).length).toBeLessThan(
            65536,
        );
        expect(readmeAdmission(chunk)).toEqual({ allowed: true });
        expect(readmeAdmission(chunk + chunk)).toEqual({
            allowed: false,
            reason: "code_block",
        });
        const tabbed =
            "\t```\r\n" +
            ("\t" + "x".repeat(4091) + "\r\n").repeat(3) +
            "\t```\r\n";
        expect(readmeAdmission(tabbed + tabbed)).toEqual({
            allowed: false,
            reason: "code_block",
        });
    });
    test("four-space and tabbed fence-looking closers remain counted content of an actual fence", () => {
        const body = ("x".repeat(4095) + "\n").repeat(3);
        for (const falseCloser of ["    ```\n", "\t```\r\n"])
            expect(
                readmeAdmission(
                    "```\n" + body + falseCloser + "x".repeat(4095) + "\n```\n",
                ),
            ).toEqual({ allowed: false, reason: "code_block" });
        expect(readmeAdmission("   ```\n" + body + "   ```")).toEqual({
            allowed: true,
        });
    });
    test("a genuine nonindented fence separates bounded indented code blocks", () => {
        const indented = ("    " + "x".repeat(4091) + "\n").repeat(3);
        expect(
            readmeAdmission(indented + "```\nliteral\n```\n" + indented),
        ).toEqual({ allowed: true });
    });
    test("256 potential table cells count header and padded missing columns before parsing", () => {
        const exact = "a|b\n-|-\n" + "x|y\n".repeat(127);
        expect(readmeAdmission(exact)).toEqual({ allowed: true });
        expect(readmeAdmission(exact + "z")).toEqual({
            allowed: false,
            reason: "table_cells",
        });
        const padded = "a|b\n-|-\n" + "x\n".repeat(127);
        expect(readmeAdmission(padded)).toEqual({ allowed: true });
        expect(readmeAdmission(padded + "x")).toEqual({
            allowed: false,
            reason: "table_cells",
        });
    });
    test("adversarial admission remains measured and finite without a promise timeout", () => {
        const fixtures = [
            ("x".repeat(4095) + "\n").repeat(16),
            "[".repeat(4096) + "\n" + "]".repeat(4096),
            "a|b\n-|-\n" + "x|y\n".repeat(1500),
            ("> ".repeat(9) + "text\n").repeat(1000),
        ];
        let maximum = 0;
        for (const fixture of fixtures) {
            for (let attempt = 0; attempt < 5; attempt++) {
                const start = performance.now();
                readmeAdmission(fixture);
                maximum = Math.max(maximum, performance.now() - start);
            }
        }
        // Generous scheduling headroom; this guards accidental nonlinear work,
        // rather than treating Promise.race as cancellation of a sync parser.
        expect(maximum).toBeLessThan(1000);
        console.info(
            "README admission maximum milliseconds:",
            maximum.toFixed(3),
        );
    });
});

describe("links leave the application selection and bind the immutable upstream commit", () => {
    test("model/dataset relative and root-relative paths have distinct upstream roots", () => {
        expect(readmeLink("docs/guide.md", model)).toBe(
            modelRoot + "docs/guide.md",
        );
        expect(readmeLink("/docs/guide.md", dataset)).toBe(
            datasetRoot + "docs/guide.md",
        );
        expect(readmeLink("docs/../guide.md", model)).toBe(
            modelRoot + "guide.md",
        );
        expect(readmeLink("docs/./", model)).toBe(modelRoot + "docs/");
        expect(readmeLink("资料/Read me.md", dataset)).toBe(
            datasetRoot + "%E8%B5%84%E6%96%99/Read%20me.md",
        );
    });
    test("fragments and management-looking queries cannot become application links", () => {
        expect(readmeLink("#operations", model)).toBe(
            modelRoot + "README.md#operations",
        );
        expect(readmeLink("?next=/api/v1/plans&value=%26literal", model)).toBe(
            modelRoot + "README.md?next=/api/v1/plans&value=%26literal",
        );
        expect(readmeLink("/api/v1/config#commit_sha=other", dataset)).toBe(
            datasetRoot + "api/v1/config#commit_sha=other",
        );
        expect(readmeLink("", model)).toBe(modelRoot + "README.md");
    });
    test("dot normalization never crosses the selected repository root", () => {
        for (const link of [
            "../README.md",
            "/../README.md",
            "docs/../../api/v1",
            "%2e%2e/README.md",
        ])
            expect(readmeLink(link, model)).toBeNull();
        expect(readmeLink("docs/./nested/../guide.md", model)).toBe(
            modelRoot + "docs/guide.md",
        );
        expect(readmeLink("/", model)).toBe(modelRoot);
    });
    test("explicit HTTP(S) with a host is navigation only, including normalized case", () => {
        expect(readmeLink("HTTPS://EXAMPLE.COM/path?q=one#part", model)).toBe(
            "https://example.com/path?q=one#part",
        );
        expect(readmeLink("http://[::1]:8080/docs", model)).toBe(
            "http://[::1]:8080/docs",
        );
    });
    test("trusted current-page origin refuses management navigation including host and default-port aliases", () => {
        for (const destination of [
            "https://management.test/api/v1/config",
            "HTTPS://MANAGEMENT.TEST:443/ui/library",
            "https://%6danagement.test/api/v1/plans",
        ])
            expect(
                readmeLink(destination, model, "https://management.test"),
            ).toBeNull();
        expect(
            readmeLink(
                "http://management.test:80/api/v1/config",
                model,
                "HTTP://MANAGEMENT.TEST",
            ),
        ).toBeNull();
        expect(
            readmeLink(
                "https://external.test/docs",
                model,
                "https://management.test",
            ),
        ).toBe("https://external.test/docs");
        expect(
            readmeLink("docs/guide.md", model, "https://management.test"),
        ).toBe(modelRoot + "docs/guide.md");
        expect(
            readmeLink("docs/guide.md", model, "https://huggingface.co"),
        ).toBeNull();
    });
    test("an invalid supplied management context fails closed for external and relative links", () => {
        for (const context of [
            "not-an-origin",
            "null",
            "file:///owned",
            "https://user@management.test",
            "https://management.test/extra",
            "https://management.test?q=1",
            "https://management.test#part",
        ])
            for (const destination of [
                "https://external.test/docs",
                "README.md",
            ])
                expect(readmeLink(destination, model, context)).toBeNull();
    });
    test.each([
        [
            "unsupported schemes",
            [
                "JaVaScRiPt:alert(1)",
                "data:text/html,content",
                "blob:https://example.test/id",
                "mailto:operator@example.test",
            ],
        ],
        [
            "encoded scheme/control",
            [
                "%6aavascript:alert(1)",
                "java%0ascript:alert(1)",
                "https%3A//example.test",
                "java\tscript:alert(1)",
            ],
        ],
        [
            "entity schemes",
            [
                "javascript&#58;alert(1)",
                "javascript&colon;alert(1)",
                "java&Tab;script:alert(1)",
            ],
        ],
        [
            "ambiguous authorities",
            [
                "//example.test/path",
                "https:example.test",
                "https:///example.test",
                "https:////example.test",
                "https://user:password@example.test/path",
            ],
        ],
        [
            "backslash/attribute/control",
            [
                "\\\\example.test/path",
                "docs\\file.md",
                'docs/\" onmouseover=\"alert(1)',
                "docs/\u0000file",
                "docs/\u202efile",
            ],
        ],
        [
            "invalid or layered encoding",
            [
                "docs/%",
                "docs/%GG",
                "docs/%ff",
                "docs/%ED%A0%80",
                "%252e%252e/private",
                "docs/%2fprivate",
                "docs/%C2%85file",
            ],
        ],
    ])(
        "%s are refused without returning an active destination",
        (_name, links) => {
            for (const link of links)
                expect(readmeLink(link, model)).toBeNull();
        },
    );
    test("invalid or oversized destinations return null without raw errors", () => {
        expect(readmeLink(" https://example.test", model)).toBeNull();
        expect(readmeLink("https://", model)).toBeNull();
        expect(readmeLink("x".repeat(4097), model)).toBeNull();
        expect(readmeLink("🙂".repeat(1025), model)).toBeNull();
        expect(readmeLink("\ud800", model)).toBeNull();
    });
});

describe("heading identifiers and navigation validate the complete publication identity", () => {
    test("prefix contains only validated identity and is collision-safe across type/repository/pair", () => {
        const prefix = readmeIdPrefix(model);
        expect(prefix).toBe(
            "readme-model-5-owner-4-name-" +
                model.commitSha +
                "-" +
                model.publicationId +
                "-",
        );
        const other = [
            dataset,
            { ...model, repositoryId: "owner/other" },
            { ...model, commitSha: "c".repeat(40) },
            { ...model, publicationId: "d".repeat(32) },
        ];
        for (const identity of other)
            expect(readmeIdPrefix(identity)).not.toBe(prefix);
        expect(readmeIdPrefix({ ...model, repositoryId: "a-b/c" })).not.toBe(
            readmeIdPrefix({ ...model, repositoryId: "a/b-c" }),
        );
        expect(readmeIdPrefix(model)).toBe(prefix);
    });
    test("malformed identities and extra authority fields cannot redirect or generate IDs", () => {
        for (const identity of [
            { ...model, commitSha: "A".repeat(40) },
            { ...model, publicationId: "bad" },
            { ...model, repositoryId: "../name" },
            { ...model, origin: "https://management.invalid" },
        ]) {
            expect(readmeLink("README.md", identity)).toBeNull();
            expect(() => readmeIdPrefix(identity)).toThrow();
        }
    });
    test("identity accessors are rejected without consulting attacker code", () => {
        const getter = vi.fn(() => "owner/name");
        const identity = Object.defineProperty({ ...model }, "repositoryId", {
            get: getter,
        });
        expect(readmeLink("README.md", identity)).toBeNull();
        expect(() => readmeIdPrefix(identity)).toThrow();
        expect(getter).not.toHaveBeenCalled();
    });
});
