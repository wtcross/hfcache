import { readFileSync } from "node:fs";
import { expect, test } from "vitest";
import {
    WARNING_GUIDANCE,
    warningGuidance,
} from "../src/administration/warnings";

test("every warning in the operator runbook has explicit browser guidance", () => {
    const document = readFileSync(
        new URL("../../docs/operations.md", import.meta.url),
        "utf8",
    );
    const codes = [
        ...document.matchAll(/^\| `(HFDEP001|HFWRN\d{3})` \|/gm),
    ].map((match) => {
        const code = match[1];
        if (code === undefined) throw new Error("Missing runbook warning code");
        return code;
    });
    expect(codes).toHaveLength(11);
    const discovery = readFileSync(
        new URL("../../docs/discovery.md", import.meta.url),
        "utf8",
    );
    expect(discovery).toContain("`HFWRN011`");
    expect(Object.keys(WARNING_GUIDANCE).sort()).toEqual(
        [...codes, "HFWRN011"].sort(),
    );
    for (const code of codes) {
        expect(warningGuidance(code).meaning.length).toBeGreaterThan(10);
        expect(warningGuidance(code).response.length).toBeGreaterThan(20);
    }
});
test("supplemental capture warnings preserve publication integrity and require explicit refresh", () => {
    const guidance = warningGuidance("HFWRN011");
    expect(guidance.meaning).toContain("Supplemental metadata");
    expect(guidance.response).toContain("remain unknown");
    expect(guidance.response).toContain(
        "does not invalidate a valid archive publication",
    );
    expect(guidance.response).toContain(
        "reading this warning never refreshes metadata",
    );
    expect(guidance.destination).toBe("operations");
});
test("unknown and prototype-named warning codes use a fixed nonexecuting fallback", () => {
    for (const code of [
        "HFNEW999",
        "__proto__",
        "constructor",
        "<script>run()</script>",
    ]) {
        expect(warningGuidance(code).meaning).toBe("Unrecognized warning");
        expect(warningGuidance(code).response).toContain(
            "No action is inferred",
        );
        expect(warningGuidance(code).destination).toBe("operations");
        expect(warningGuidance(code).actionLabel).toBe(
            "Review operation details",
        );
    }
});
test("runbook preservation and scope consequences remain explicit", () => {
    expect(warningGuidance("HFWRN003").response).toContain(
        "preserved, never deleted automatically",
    );
    expect(warningGuidance("HFWRN006").response).toContain(
        "never triggers a prune",
    );
    expect(warningGuidance("HFWRN007").response).toContain("purge preview");
    expect(warningGuidance("HFWRN008").response).toContain("does not delete");
    expect(warningGuidance("HFWRN009").response).toContain("writer-local disk");
});
