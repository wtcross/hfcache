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
import { Library } from "./components/Library";
import type { RepositoryNavigation } from "./components/Library";
import type { LibraryStore } from "./library/library-state";
import { RepositoryDetail } from "./components/RepositoryDetail";
import { ConfigurationEditor } from "./components/ConfigurationEditor";
import type {
    ConfigurationStore,
    ConfigurationIntent,
} from "./configuration/configuration-state";
import type { RepositoryStore } from "./repository/repository-state";
import { repositoryFragment, repositoryPath } from "./repository/routes";
import type { RepositoryTarget } from "./repository/routes";
import { OperationsWorkspace } from "./components/OperationsWorkspace";
import { MaintenanceWorkspace } from "./components/MaintenanceWorkspace";
import type {
    MaintenanceStore,
    RepairFindingIntent,
} from "./operations/maintenance-state";
import type { JobsStore } from "./operations/jobs-state";
import type { HistoryStore } from "./operations/history-state";
import type { AdministrationReadStore } from "./administration/administration-read-state";
import type { HostControlsStore } from "./administration/host-controls-state";
import { AdministrationWorkspace } from "./components/AdministrationWorkspace";
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
    library,
    repository,
    repositoryTarget,
    basePath,
    onOpenRepository,
    configuration,
    onEditConfiguration,
    jobs,
    history,
    onReadReport,
    onOpenConfiguration,
    maintenance,
    onRepairFinding,
    administrationRead,
    hostControls,
    onAdministrationNavigate,
}: {
    workspace: Workspace;
    authenticated: boolean;
    host: UiBootstrap | null;
    controller?: SessionController;
    session?: SessionSnapshot;
    library?: LibraryStore;
    repository?: RepositoryStore;
    repositoryTarget?: RepositoryTarget;
    basePath: string;
    onOpenRepository: RepositoryNavigation;
    configuration?: ConfigurationStore;
    onEditConfiguration?: (intent: ConfigurationIntent) => void;
    jobs?: JobsStore;
    history?: HistoryStore;
    onReadReport?: (runId: string) => void;
    onOpenConfiguration?: () => void;
    maintenance?: MaintenanceStore;
    onRepairFinding?: (intent: RepairFindingIntent) => void;
    administrationRead?: AdministrationReadStore;
    hostControls?: HostControlsStore;
    onAdministrationNavigate: (
        destination: "configuration" | "maintenance" | "operations",
    ) => void;
}) {
    switch (workspace) {
        case "library":
            if (repositoryTarget !== undefined) {
                return repository === undefined ? (
                    <Panel title="Repository details unavailable">
                        <p>
                            Connect the authenticated archive to inspect this
                            repository.
                        </p>
                    </Panel>
                ) : (
                    <RepositoryDetail
                        store={repository}
                        target={repositoryTarget}
                        basePath={basePath}
                        {...(onReadReport === undefined
                            ? {}
                            : { onReadReport })}
                        {...(onEditConfiguration === undefined
                            ? {}
                            : { onEditConfiguration })}
                    />
                );
            }
            if (library !== undefined)
                return (
                    <Library
                        store={library}
                        basePath={basePath}
                        onOpenRepository={onOpenRepository}
                        {...(onEditConfiguration === undefined
                            ? {}
                            : { onEditConfiguration })}
                    />
                );
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
            if (
                controller !== undefined &&
                session !== undefined &&
                jobs !== undefined &&
                history !== undefined
            )
                return (
                    <OperationsWorkspace
                        controller={controller}
                        session={session}
                        jobs={jobs}
                        history={history}
                        {...(onRepairFinding === undefined
                            ? {}
                            : { onRepairFinding })}
                        {...(configuration === undefined
                            ? {}
                            : { configuration })}
                        {...(onOpenConfiguration === undefined
                            ? {}
                            : { onOpenConfiguration })}
                    />
                );
            if (controller !== undefined && session !== undefined)
                return (
                    <OperationRecovery
                        controller={controller}
                        session={session}
                        {...(configuration === undefined
                            ? {}
                            : { configuration })}
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
            if (
                maintenance !== undefined &&
                controller !== undefined &&
                session !== undefined
            )
                return (
                    <MaintenanceWorkspace
                        store={maintenance}
                        controller={controller}
                        session={session}
                        {...(onReadReport === undefined
                            ? {}
                            : { onReadReport })}
                    />
                );
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
            if (
                controller !== undefined &&
                session !== undefined &&
                administrationRead !== undefined &&
                hostControls !== undefined
            )
                return (
                    <AdministrationWorkspace
                        controller={controller}
                        session={session}
                        read={administrationRead}
                        hostControls={hostControls}
                        onNavigate={onAdministrationNavigate}
                        {...(configuration === undefined
                            ? {}
                            : { configuration })}
                        {...(jobs === undefined ? {} : { jobs })}
                        {...(onReadReport === undefined
                            ? {}
                            : { onReadReport })}
                    />
                );
            if (configuration !== undefined)
                return (
                    <>
                        <ConfigurationEditor store={configuration} />
                        {host !== null && controller !== undefined && (
                            <SessionHostAdministration
                                controller={controller}
                            />
                        )}
                    </>
                );
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
    library,
    libraryBookmark,
    repository,
    configuration,
    jobs,
    history,
    maintenance,
    administrationRead,
    hostControls,
}: {
    basePath: string;
    bootstrap?: UiBootstrap;
    onCheckRelease?: () => Promise<boolean>;
    controller?: SessionController;
    session?: SessionSnapshot;
    library?: LibraryStore;
    libraryBookmark?: string;
    repository?: RepositoryStore;
    configuration?: ConfigurationStore;
    jobs?: JobsStore;
    history?: HistoryStore;
    maintenance?: MaintenanceStore;
    administrationRead?: AdministrationReadStore;
    hostControls?: HostControlsStore;
}) {
    const base = validateBasePath(basePath);
    const [pathname, setPathname] = useState(window.location.pathname);
    const [navigationOpen, setNavigationOpen] = useState(false);
    const main = useRef<HTMLElement>(null);
    const initial = useRef(true);
    const acceptedLocation = useRef(
        window.location.pathname + window.location.hash,
    );
    const [pendingNavigation, setPendingNavigation] = useState<{
        path: string | null;
        intent: ConfigurationIntent | null;
    } | null>(null);
    const stayButton = useRef<HTMLButtonElement>(null);
    const leaveButton = useRef<HTMLButtonElement>(null);
    const previousFocus = useRef<HTMLElement | null>(null);
    const documentReadsSuspended = useRef(false);
    const [updateRequired, setUpdateRequired] = useState(false);
    const [versionCheck, setVersionCheck] = useState<
        "idle" | "checking" | "unavailable"
    >("idle");
    const route = resolveRoute(pathname, base);
    const workspace =
        route.kind === "workspace"
            ? route.workspace
            : route.kind === "repository"
              ? "library"
              : null;
    const host =
        bootstrap !== undefined &&
        bootstrap.user.admin_permissions.some(
            (permission) =>
                permission.capability === "host-read" && permission.effective,
        )
            ? bootstrap
            : null;
    const title =
        route.kind === "repository"
            ? route.target.repositoryType === "model"
                ? "Model details"
                : "Dataset details"
            : workspace === null
              ? "Page unavailable"
              : workspaceLabel(workspace);

    useEffect(() => {
        const suspendDocumentReads = () => {
            if (documentReadsSuspended.current) return;
            documentReadsSuspended.current = true;
            // INV-021: retire the parent batches before cancelled reads settle
            // and try to start their next bounded read during document leave.
            library?.setPageActive(false);
            repository?.setPageActive(false);
            administrationRead?.setPageActive(false);
        };
        const resumeDocumentReads = () => {
            if (!documentReadsSuspended.current) return;
            documentReadsSuspended.current = false;
            const current = resolveRoute(window.location.pathname, base);
            if (current.kind === "repository") repository?.setPageActive(true);
            else if (current.kind === "workspace") {
                if (current.workspace === "library")
                    library?.setPageActive(true);
                else if (current.workspace === "administration")
                    administrationRead?.setPageActive(true);
            }
        };
        const observeLocation = () => {
            const target = window.location.pathname + window.location.hash;
            if (target !== acceptedLocation.current) maintenance?.pause();
            if (
                (configuration?.snapshot().dirty === true ||
                    hostControls?.snapshot().dirty === true) &&
                target !== acceptedLocation.current
            ) {
                window.history.replaceState(null, "", acceptedLocation.current);
                previousFocus.current =
                    document.activeElement instanceof HTMLElement
                        ? document.activeElement
                        : null;
                setPendingNavigation({
                    path: target,
                    intent: null,
                });
                return;
            }
            acceptedLocation.current = target;
            setPathname(window.location.pathname);
            setNavigationOpen(false);
        };
        window.addEventListener("popstate", observeLocation);
        window.addEventListener("hashchange", observeLocation);
        const beforeUnload = (event: BeforeUnloadEvent) => {
            if (
                configuration?.snapshot().dirty === true ||
                hostControls?.snapshot().dirty === true
            ) {
                event.preventDefault();
                // Native Stay must leave this document's draft and reads usable.
                return;
            }
            if (!event.defaultPrevented) suspendDocumentReads();
        };
        window.addEventListener("beforeunload", beforeUnload);
        window.addEventListener("pagehide", suspendDocumentReads);
        // React effects may remain frozen in BFCache. Reactivate before each
        // mounted route's pageshow listener parses its current address.
        window.addEventListener("pageshow", resumeDocumentReads, true);
        return () => {
            window.removeEventListener("popstate", observeLocation);
            window.removeEventListener("hashchange", observeLocation);
            window.removeEventListener("beforeunload", beforeUnload);
            window.removeEventListener("pagehide", suspendDocumentReads);
            window.removeEventListener("pageshow", resumeDocumentReads, true);
        };
    }, [
        base,
        configuration,
        hostControls,
        maintenance,
        library,
        repository,
        administrationRead,
    ]);
    useEffect(() => {
        if (pendingNavigation !== null) stayButton.current?.focus();
    }, [pendingNavigation]);
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

    function performNavigation(
        path: string | null,
        intent: ConfigurationIntent | null = null,
    ) {
        maintenance?.pause();
        if (path === null) {
            window.location.reload();
            return;
        }
        if (intent !== null) configuration?.setIntent(intent);
        window.history.pushState(null, "", path);
        acceptedLocation.current =
            window.location.pathname + window.location.hash;
        setPathname(window.location.pathname);
        setNavigationOpen(false);
    }
    function requestNavigation(
        path: string | null,
        intent: ConfigurationIntent | null = null,
    ) {
        maintenance?.pause();
        if (
            configuration?.snapshot().dirty === true ||
            hostControls?.snapshot().dirty === true
        ) {
            previousFocus.current =
                document.activeElement instanceof HTMLElement
                    ? document.activeElement
                    : null;
            setPendingNavigation({ path, intent });
        } else performNavigation(path, intent);
    }
    function navigate(event: MouseEvent<HTMLAnchorElement>, target: Workspace) {
        if (!isPlainNavigation(event)) return;
        event.preventDefault();
        const path =
            workspacePath(target, base) +
            (target === "library" ? (libraryBookmark ?? "") : "");
        requestNavigation(path);
    }
    const navigateRepository: RepositoryNavigation = (event, target, view) => {
        if (!isPlainNavigation(event)) return;
        event.preventDefault();
        const path = repositoryPath(target, base);
        requestNavigation(path + repositoryFragment(view));
    };
    const canEditConfiguration =
        configuration !== undefined &&
        bootstrap !== undefined &&
        ["config-read", "config-write"].every((capability) =>
            bootstrap.user.admin_permissions.some(
                (permission) =>
                    permission.capability === capability &&
                    permission.effective,
            ),
        );
    function editConfiguration(intent: ConfigurationIntent) {
        requestNavigation(workspacePath("administration", base), intent);
    }
    function administrationNavigate(
        destination: "configuration" | "maintenance" | "operations",
    ) {
        if (destination === "configuration") {
            const section = document.getElementById(
                "administration-configuration",
            );
            section?.scrollIntoView({ block: "start" });
            section?.focus();
        } else requestNavigation(workspacePath(destination, base));
    }
    function readReport(runId: string) {
        if (history === undefined) return;
        void history.selectRun(runId);
        requestNavigation(workspacePath("operations", base));
    }
    function reviewRepairFinding(intent: RepairFindingIntent) {
        // Only the charged maintenance owner retains finding data, including
        // while an unsaved-configuration navigation dialog is open.
        maintenance?.setRepairFinding(intent);
        requestNavigation(workspacePath("maintenance", base));
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
            {pendingNavigation !== null && (
                <div className="draft-navigation-overlay">
                    <div
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="unsaved-draft-title"
                        className="draft-navigation-dialog"
                        onKeyDown={(event) => {
                            if (event.key === "Escape") {
                                event.preventDefault();
                                setPendingNavigation(null);
                                previousFocus.current?.focus();
                            } else if (event.key === "Tab") {
                                event.preventDefault();
                                if (
                                    document.activeElement ===
                                    stayButton.current
                                )
                                    leaveButton.current?.focus();
                                else stayButton.current?.focus();
                            }
                        }}
                    >
                        <h2 id="unsaved-draft-title">
                            {hostControls?.snapshot().dirty === true
                                ? configuration?.snapshot().dirty === true
                                    ? "Unsaved administration changes"
                                    : "Unsaved schedule changes"
                                : "Unsaved configuration changes"}
                        </h2>
                        <p>
                            {hostControls?.snapshot().dirty === true
                                ? "Leaving discards private administration drafts and schedule review."
                                : "Leaving discards the private configuration draft."}{" "}
                            Original operation handles remain available in
                            Operations and Administration.
                        </p>
                        <button
                            ref={stayButton}
                            type="button"
                            onClick={() => {
                                setPendingNavigation(null);
                                previousFocus.current?.focus();
                            }}
                        >
                            Stay
                        </button>
                        <button
                            ref={leaveButton}
                            type="button"
                            onClick={() => {
                                const next = pendingNavigation;
                                configuration?.discard();
                                hostControls?.discard();
                                setPendingNavigation(null);
                                performNavigation(next.path, next.intent);
                            }}
                        >
                            Discard draft and leave
                        </button>
                    </div>
                </div>
            )}
            <a
                className="skip-link"
                href="#main-content"
                onClick={(event) => {
                    if (!isPlainNavigation(event)) return;
                    event.preventDefault();
                    main.current?.focus();
                }}
            >
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
                            href={
                                workspacePath(item.id, base) +
                                (item.id === "library"
                                    ? (libraryBookmark ?? "")
                                    : "")
                            }
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
                            {route.kind === "repository"
                                ? "Inspect one exact publication, its attributed metadata and independent integrity evidence."
                                : (WORKSPACES.find(
                                      (item) => item.id === workspace,
                                  )?.description ??
                                  "This address does not identify an available workspace.")}
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
                              : "Original operation handles are preserved separately from private observations. Open Operations or Administration for recovery."}
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
                                    requestNavigation(null);
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
                            {...(library === undefined ? {} : { library })}
                            {...(repository === undefined
                                ? {}
                                : { repository })}
                            {...(route.kind === "repository"
                                ? { repositoryTarget: route.target }
                                : {})}
                            basePath={base}
                            onOpenRepository={navigateRepository}
                            onAdministrationNavigate={administrationNavigate}
                            {...(administrationRead === undefined
                                ? {}
                                : { administrationRead })}
                            {...(hostControls === undefined
                                ? {}
                                : { hostControls })}
                            {...(configuration === undefined
                                ? {}
                                : { configuration })}
                            {...(jobs === undefined ? {} : { jobs })}
                            {...(history === undefined
                                ? {}
                                : { history, onReadReport: readReport })}
                            {...(maintenance === undefined
                                ? {}
                                : {
                                      maintenance,
                                      onRepairFinding: reviewRepairFinding,
                                  })}
                            {...(!canEditConfiguration
                                ? {}
                                : {
                                      onEditConfiguration: editConfiguration,
                                      onOpenConfiguration: () => {
                                          requestNavigation(
                                              workspacePath(
                                                  "administration",
                                                  base,
                                              ),
                                          );
                                      },
                                  })}
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
