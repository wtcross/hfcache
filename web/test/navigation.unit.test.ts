import { describe, expect, test } from "vitest";
import {
    isWorkspace,
    isPlainNavigation,
    resolveRoute,
    validateBasePath,
    WORKSPACES,
    workspaceLabel,
    workspacePath,
} from "../src/navigation";

describe("presentation routes", () => {
    test("known workspaces preserve names, prefix and exact route identity", () => {
        for (const workspace of WORKSPACES) {
            expect(isWorkspace(workspace.id)).toBe(true);
            expect(workspaceLabel(workspace.id)).toBe(workspace.label);
            expect(workspacePath(workspace.id, "/management/ui/")).toBe(
                `/management/ui/${workspace.id}`,
            );
            expect(
                resolveRoute(
                    `/management/ui/${workspace.id}`,
                    "/management/ui/",
                ),
            ).toEqual({ kind: "workspace", workspace: workspace.id });
        }
        expect(resolveRoute("/ui/", "/ui/")).toEqual({
            kind: "workspace",
            workspace: "library",
        });
    });

    test.each([
        "/ui/missing",
        "/api/v1/status",
        "/mcp/",
        "/ui/library/extra",
        "/ui/library/",
        "/other/ui/library",
        "/ui/%6cibrary",
    ])("unknown path %s never supplies another route", (path) => {
        expect(resolveRoute(path, "/ui/")).toEqual({ kind: "not-found" });
    });

    test.each([
        null,
        undefined,
        1,
        {},
        [],
        "",
        "ui/",
        "/ui",
        "/ui//",
        "/./ui/",
        "/../ui/",
        "/u%69/",
        "/ui/?",
        "/ui/#",
        "/ui/\\/",
        "/ui/\n/",
        "/ui/ /",
        "/".repeat(1025),
    ])("malformed deployment base is refused", (value) => {
        expect(() => validateBasePath(value)).toThrow("deployment base path");
    });

    test("valid normalized deployment paths remain exact", () => {
        expect(validateBasePath("/ui/")).toBe("/ui/");
        expect(validateBasePath("/management/ui/")).toBe("/management/ui/");
        expect(isWorkspace("Library")).toBe(false);
    });
});

test("native modified navigation remains distinct from a plain primary click", () => {
    const plain = {
        button: 0,
        metaKey: false,
        ctrlKey: false,
        shiftKey: false,
        altKey: false,
    };
    expect(isPlainNavigation(plain)).toBe(true);
    for (const gesture of [
        { button: 1 },
        { metaKey: true },
        { ctrlKey: true },
        { shiftKey: true },
        { altKey: true },
    ]) {
        expect(isPlainNavigation({ ...plain, ...gesture })).toBe(false);
    }
});
