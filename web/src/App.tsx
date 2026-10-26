import { useEffect, useRef, useState } from "react";
import type { MouseEvent } from "react";
import { Notice, Panel } from "./primitives";
import {
    resolveRoute,
    isPlainNavigation,
    validateBasePath,
    WORKSPACES,
    workspaceLabel,
    workspacePath,
} from "./navigation";
import type { Workspace } from "./navigation";
import type { UiAdminPermission, UiBootstrap } from "./wire/generated";
import {
    HostAdministration,
    SessionHostAdministration,
} from "./components/HostStatusPanel";
import { OperationRecovery } from "./components/OperationRecovery";
import type {
    SessionController,
    SessionSnapshot,
} from "./state/session-controller";

const permissionLabels: Readonly<
    Record<UiAdminPermission["capability"], string>
> = {
    "config-read": "View configuration",
    "config-write": "Edit configuration",
    "host-read": "View host status",
    "observer-stop": "Stop observation",
    "schedule-write": "Change schedules",
};

function WorkspaceContent({
    workspace,
    authenticated,
    host,
    controller,
    session,
}: {
    workspace: Workspace;
    authenticated: boolean;
    host: UiBootstrap | null;
    controller?: SessionController;
    session?: SessionSnapshot;
}) {
    switch (workspace) {
        case "library":
            return (
                <div className="workspace-grid">
                    <Panel title="Your repository library">
                        <div className="empty-state">
                            <span className="empty-mark" aria-hidden="true">
                                ▦
                            </span>
                            <h3>
                                {authenticated
                                    ? "Library data has not been loaded"
                                    : "Connect an archive to explore your library"}
                            </h3>
                            <p>
                                Published models and datasets will appear here
                                with their exact revision and publication
                                identity.
                            </p>
                            <div className="content-types">
                                <span>Models</span>
                                <span>Datasets</span>
                            </div>
                        </div>
                    </Panel>
                    <div className="supporting-panels">
                        <Panel title="Operator tags">
                            <p>
                                Your labels organize repositories. Tags come
                                from the installed configuration and never grant
                                access.
                            </p>
                        </Panel>
                        <Panel title="Know your evidence">
                            <p>
                                Availability, technical metadata coverage and
                                verification confidence describe different
                                facts.
                            </p>
                        </Panel>
                    </div>
                </div>
            );
        case "operations":
            if (controller !== undefined && session !== undefined)
                return (
                    <OperationRecovery
                        controller={controller}
                        session={session}
                    />
                );
            return (
                <Panel title="Operation observation">
                    <div className="empty-state">
                        <span className="empty-mark" aria-hidden="true">
                            ⌁
                        </span>
                        <h3>No operation history has been loaded</h3>
                        <p>
                            Connection loss does not cancel accepted work.
                            Original operation handles remain the way to observe
                            its outcome.
                        </p>
                    </div>
                </Panel>
            );
        case "maintenance":
            return (
                <Panel title="Archive care">
                    <div className="empty-state">
                        <span className="empty-mark" aria-hidden="true">
                            ◇
                        </span>
                        <h3>Maintenance requires current archive evidence</h3>
                        <p>
                            Verification, retention and recovery use guarded
                            server workflows. No maintenance action is available
                            yet.
                        </p>
                    </div>
                </Panel>
            );
        case "administration":
            if (host !== null && controller !== undefined)
                return <SessionHostAdministration controller={controller} />;
            if (host !== null) return <HostAdministration bootstrap={host} />;
            return (
                <Panel title="Configuration and host permissions">
                    <div className="empty-state">
                        <span className="empty-mark" aria-hidden="true">
                            ☷
                        </span>
                        <h3>Deployment authority has not been observed</h3>
                        <p>
                            Configuration changes require exact installed
                            content and protected host permission. Host controls
                            are not available in this interface yet.
                        </p>
                    </div>
                </Panel>
            );
    }
}

export function App({
    basePath,
    bootstrap,
    onCheckRelease,
    controller,
    session,
}: {
    basePath: string;
    bootstrap?: UiBootstrap;
    onCheckRelease?: () => Promise<boolean>;
    controller?: SessionController;
    session?: SessionSnapshot;
}) {
    const base = validateBasePath(basePath);
    const [pathname, setPathname] = useState(window.location.pathname);
    const [navigationOpen, setNavigationOpen] = useState(false);
    const main = useRef<HTMLElement>(null);
    const initial = useRef(true);
    const [updateRequired, setUpdateRequired] = useState(false);
    const [versionCheck, setVersionCheck] = useState<
        "idle" | "checking" | "unavailable"
    >("idle");
    const route = resolveRoute(pathname, base);
    const workspace = route.kind === "workspace" ? route.workspace : null;
    const host =
        bootstrap !== undefined &&
        bootstrap.user.admin_permissions.some(
            (permission) =>
                permission.capability === "host-read" && permission.effective,
        )
            ? bootstrap
            : null;
    const title =
        workspace === null ? "Page unavailable" : workspaceLabel(workspace);

    useEffect(() => {
        const observeLocation = () => {
            setPathname(window.location.pathname);
            setNavigationOpen(false);
        };
        window.addEventListener("popstate", observeLocation);
        return () => {
            window.removeEventListener("popstate", observeLocation);
        };
    }, []);
    useEffect(() => {
        const refuseChunk = (event: Event) => {
            event.preventDefault();
            setUpdateRequired(true);
        };
        window.addEventListener("vite:preloadError", refuseChunk);
        return () => {
            window.removeEventListener("vite:preloadError", refuseChunk);
        };
    }, []);

    useEffect(() => {
        document.title = `hfcache · ${title}`;
        if (initial.current) initial.current = false;
        else main.current?.focus();
    }, [pathname, title]);

    function navigate(event: MouseEvent<HTMLAnchorElement>, target: Workspace) {
        if (!isPlainNavigation(event)) return;
        event.preventDefault();
        const path = workspacePath(target, base);
        window.history.pushState(null, "", path);
        setPathname(path);
        setNavigationOpen(false);
    }
    async function checkInterfaceVersion(): Promise<void> {
        if (onCheckRelease === undefined) return;
        setVersionCheck("checking");
        try {
            if (await onCheckRelease()) setUpdateRequired(true);
            setVersionCheck("idle");
        } catch {
            setVersionCheck("unavailable");
        }
    }

    return (
        <div className="application">
            <a className="skip-link" href="#main-content">
                Skip to content
            </a>
            <aside className={`sidebar${navigationOpen ? " is-open" : ""}`}>
                <div className="brand">
                    <span className="brand-mark" aria-hidden="true">
                        ▱
                    </span>
                    hfcache
                </div>
                <div className="archive-context">
                    <span className="context-mark" aria-hidden="true">
                        ▤
                    </span>
                    <div>
                        <strong>
                            {bootstrap === undefined
                                ? "Archive not connected"
                                : "Configured archive"}
                        </strong>
                        <span>
                            {bootstrap?.configured_archive_id ??
                                "Awaiting trusted archive identity"}
                        </span>
                    </div>
                </div>
                <p className="nav-label">Workspace</p>
                <nav aria-label="Main navigation" id="workspace-navigation">
                    {WORKSPACES.map((item) => (
                        <a
                            key={item.id}
                            href={workspacePath(item.id, base)}
                            aria-current={
                                workspace === item.id ? "page" : undefined
                            }
                            onClick={(event) => {
                                navigate(event, item.id);
                            }}
                        >
                            <span className="nav-symbol" aria-hidden="true">
                                {item.symbol}
                            </span>
                            {item.label}
                        </a>
                    ))}
                </nav>
                <div className="sidebar-bottom">
                    <p>
                        Complete revisions.
                        <br />
                        Exact publication identity.
                        <br />
                        Guarded archive operations.
                    </p>
                    <span>hfcache management</span>
                </div>
            </aside>
            <div className="main-column">
                <div className="preview-banner">
                    <strong>
                        {bootstrap === undefined
                            ? "Development preview"
                            : "Administrator session"}
                    </strong>
                    <span>
                        {bootstrap === undefined
                            ? "Archive data and authenticated actions are not connected."
                            : `Signed in as ${bootstrap.user.display_name}. Archive health has not been loaded.`}
                    </span>
                </div>
                <header className="topbar">
                    <div className="breadcrumb">
                        <button
                            className="navigation-toggle"
                            type="button"
                            aria-controls="workspace-navigation"
                            aria-expanded={navigationOpen}
                            onClick={() => {
                                setNavigationOpen(!navigationOpen);
                            }}
                        >
                            {navigationOpen
                                ? "Close navigation"
                                : "Open navigation"}
                        </button>
                        <span>Workspace</span>
                        <span aria-hidden="true">›</span>
                        <strong>{title}</strong>
                    </div>
                    <span className="connection-state">
                        <span aria-hidden="true" />
                        {bootstrap === undefined
                            ? "Not connected"
                            : session === undefined
                              ? "Authenticated"
                              : session.connection === "connected"
                                ? "Authenticated"
                                : session.connection.replaceAll("_", " ")}
                    </span>
                </header>
                <main id="main-content" ref={main} tabIndex={-1}>
                    {controller !== undefined && session !== undefined && (
                        <div className="session-recovery">
                            <button
                                type="button"
                                disabled={
                                    session.connection === "reconnecting" ||
                                    session.connection === "update_required"
                                }
                                onClick={() => {
                                    void controller.reconnect();
                                }}
                            >
                                Reconnect
                            </button>
                            {session.notice !== null && (
                                <Notice>{session.notice}</Notice>
                            )}
                            {session.connection === "update_required" && (
                                <p role="status">
                                    Copy original recovery handles, then reload
                                    the interface.
                                </p>
                            )}
                        </div>
                    )}
                    {bootstrap !== undefined &&
                        onCheckRelease !== undefined && (
                            <div>
                                <button
                                    type="button"
                                    disabled={versionCheck === "checking"}
                                    onClick={() => {
                                        void checkInterfaceVersion();
                                    }}
                                >
                                    Check interface version
                                </button>
                                {versionCheck === "unavailable" && (
                                    <p role="status">
                                        The interface version could not be
                                        checked. Existing operation handles are
                                        preserved.
                                    </p>
                                )}
                            </div>
                        )}
                    <div className="page-heading">
                        <span className="eyebrow">Your archive workspace</span>
                        <h1>{title}</h1>
                        <p>
                            {WORKSPACES.find((item) => item.id === workspace)
                                ?.description ??
                                "This address does not identify an available workspace."}
                        </p>
                    </div>
                    <Notice>
                        <strong>
                            {bootstrap === undefined
                                ? "Archive information is unavailable."
                                : "Configured identity loaded."}
                        </strong>{" "}
                        {bootstrap === undefined
                            ? "This source preview makes no API requests and submits no operations."
                            : controller === undefined
                              ? "Archive health and repository data have not been requested. No operation has been submitted."
                              : "Original operation handles are preserved separately from private observations. Open Operations for recovery."}
                    </Notice>
                    {(updateRequired ||
                        session?.connection === "update_required") && (
                        <Notice>
                            <strong>Interface update required.</strong> Reload
                            when ready. Original operation handles and unsaved
                            work must be preserved.
                            <button
                                type="button"
                                onClick={() => {
                                    window.location.reload();
                                }}
                            >
                                Reload interface
                            </button>
                        </Notice>
                    )}
                    {workspace === "administration" &&
                        bootstrap !== undefined && (
                            <Panel title="Administrator permissions">
                                <ul>
                                    {bootstrap.user.admin_permissions.map(
                                        (permission) => (
                                            <li key={permission.capability}>
                                                <span>
                                                    {
                                                        permissionLabels[
                                                            permission
                                                                .capability
                                                        ]
                                                    }
                                                </span>{" "}
                                                {permission.reason ===
                                                "feature_unavailable"
                                                    ? "This feature is not available in this deployment."
                                                    : permission.reason ===
                                                        "not_granted"
                                                      ? "Permission is not granted."
                                                      : "Available."}
                                            </li>
                                        ),
                                    )}
                                </ul>
                            </Panel>
                        )}
                    {workspace === null ? (
                        <Panel title="Choose a workspace">
                            <p>
                                Use the main navigation to return to a known
                                workspace.
                            </p>
                            <a
                                href={workspacePath("library", base)}
                                onClick={(event) => {
                                    navigate(event, "library");
                                }}
                            >
                                Open Library
                            </a>
                        </Panel>
                    ) : (
                        <WorkspaceContent
                            workspace={workspace}
                            authenticated={bootstrap !== undefined}
                            host={host}
                            {...(controller === undefined
                                ? {}
                                : { controller })}
                            {...(session === undefined ? {} : { session })}
                        />
                    )}
                    <footer className="page-footer">
                        Published content remains separate from management
                        actions. Repository information is shown only after it
                        is loaded and validated.
                    </footer>
                </main>
            </div>
        </div>
    );
}
