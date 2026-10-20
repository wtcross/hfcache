/** Presentation routes only; no endpoint, principal or archive authority (INV-019). */
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
    { kind: "workspace"; workspace: Workspace } | { kind: "not-found" };

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
    if (
        typeof value !== "string" ||
        value.length > 1024 ||
        !value.startsWith("/") ||
        !value.endsWith("/") ||
        /[%?#\\\s\u0000-\u001f\u007f]/u.test(value) ||
        value.includes("//") ||
        value.split("/").some((part) => part === "." || part === "..")
    )
        throw new Error("The deployment base path is unavailable.");
    return value;
}

export function resolveRoute(pathname: string, basePath: string): Route {
    if (!pathname.startsWith(basePath)) return { kind: "not-found" };
    const path = pathname.slice(basePath.length);
    if (path === "") return { kind: "workspace", workspace: "library" };
    return isWorkspace(path)
        ? { kind: "workspace", workspace: path }
        : { kind: "not-found" };
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
