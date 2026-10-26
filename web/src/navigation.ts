/** Presentation routes only; no endpoint, principal or archive authority (INV-019). */
import { canonicalUiPrefix } from "./wire/ui-semantics";
import { uriPath } from "./api/url-paths";
import { parseRepositoryRoute } from "./repository/routes";
import type { RepositoryTarget } from "./repository/routes";
export const WORKSPACES = [
    {
        id: "library",
        label: "Library",
        symbol: "▦",
        description: "Models and datasets, together in your archive.",
    },
    {
        id: "operations",
        label: "Operations",
        symbol: "⌁",
        description:
            "Observe submitted work and preserve original recovery handles.",
    },
    {
        id: "maintenance",
        label: "Maintenance",
        symbol: "◇",
        description: "Review archive integrity and guarded maintenance.",
    },
    {
        id: "administration",
        label: "Administration",
        symbol: "☷",
        description: "Manage configuration and review deployment permissions.",
    },
] as const;

export type Workspace = (typeof WORKSPACES)[number]["id"];
export type Route =
    | { kind: "workspace"; workspace: Workspace }
    | { kind: "repository"; target: RepositoryTarget }
    | { kind: "not-found" };

export function isPlainNavigation(event: {
    button: number;
    metaKey: boolean;
    ctrlKey: boolean;
    shiftKey: boolean;
    altKey: boolean;
}): boolean {
    return (
        event.button === 0 &&
        !event.metaKey &&
        !event.ctrlKey &&
        !event.shiftKey &&
        !event.altKey
    );
}

export function isWorkspace(value: string): value is Workspace {
    return WORKSPACES.some((workspace) => workspace.id === value);
}

export function validateBasePath(value: unknown): string {
    try {
        if (typeof value !== "string" || !value.endsWith("/ui/"))
            throw new Error();
        const prefix = decodeURIComponent(value.slice(0, -4));
        canonicalUiPrefix(prefix);
        if (uriPath(prefix + "/ui/") !== value) throw new Error();
    } catch {
        throw new Error("The deployment base path is unavailable.");
    }
    return value;
}

export function resolveRoute(pathname: string, basePath: string): Route {
    if (!pathname.startsWith(basePath)) return { kind: "not-found" };
    const path = pathname.slice(basePath.length);
    if (path === "") return { kind: "workspace", workspace: "library" };
    if (isWorkspace(path)) return { kind: "workspace", workspace: path };
    const target = parseRepositoryRoute(pathname, basePath);
    return target === null
        ? { kind: "not-found" }
        : { kind: "repository", target };
}

export function workspacePath(workspace: Workspace, basePath: string): string {
    return validateBasePath(basePath) + workspace;
}

export function workspaceLabel(workspace: Workspace): string {
    switch (workspace) {
        case "library":
            return "Library";
        case "operations":
            return "Operations";
        case "maintenance":
            return "Maintenance";
        case "administration":
            return "Administration";
    }
}
