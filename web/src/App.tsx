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

function WorkspaceContent({ workspace }: { workspace: Workspace }) {
    switch (workspace) {
        case "library":
            return (
                <div className="workspace-grid">
                    <Panel title="Your repository library">
                        <div className="empty-state">
                            <span className="empty-mark" aria-hidden="true">
                                ▦
                            </span>
                            <h3>Connect an archive to explore your library</h3>
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
                            in this preview.
                        </p>
                    </div>
                </Panel>
            );
        case "administration":
            return (
                <Panel title="Configuration and host permissions">
                    <div className="empty-state">
                        <span className="empty-mark" aria-hidden="true">
                            ☷
                        </span>
                        <h3>Deployment authority has not been observed</h3>
                        <p>
                            Configuration changes require exact installed
                            content and protected host permission. This preview
                            has no authentication or host connection.
                        </p>
                    </div>
                </Panel>
            );
    }
}

export function App({ basePath }: { basePath: string }) {
    const base = validateBasePath(basePath);
    const [pathname, setPathname] = useState(window.location.pathname);
    const [navigationOpen, setNavigationOpen] = useState(false);
    const main = useRef<HTMLElement>(null);
    const initial = useRef(true);
    const route = resolveRoute(pathname, base);
    const workspace = route.kind === "workspace" ? route.workspace : null;
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
                        <strong>Archive not connected</strong>
                        <span>Awaiting trusted archive identity</span>
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
                    <strong>Development preview</strong>
                    <span>
                        Archive data and authenticated actions are not
                        connected.
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
                        Not connected
                    </span>
                </header>
                <main id="main-content" ref={main} tabIndex={-1}>
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
                        <strong>Archive information is unavailable.</strong>{" "}
                        This source preview makes no API requests and submits no
                        operations.
                    </Notice>
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
                        <WorkspaceContent workspace={workspace} />
                    )}
                    <footer className="page-footer">
                        Published content remains separate from management
                        actions. No repository facts are inferred from an
                        unconnected view.
                    </footer>
                </main>
            </div>
        </div>
    );
}
