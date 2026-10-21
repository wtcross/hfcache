import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { App } from "../src/App";
import { mountApplication } from "../src/mount";
import { inertUiDocument, uiBootstrapFixture } from "./ui-fixtures";

test("unconnected Library reports unavailable facts without fictional measurements or API requests", () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<App basePath="/ui/" />);
    expect(
        screen.getByRole("heading", { level: 1, name: "Library" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Archive not connected")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
        "Archive information is unavailable.",
    );
    expect(screen.getByText("Models")).toBeInTheDocument();
    expect(screen.getByText("Datasets")).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
});

test("keyboard navigation selects all four workspaces and focuses their content", async () => {
    const user = userEvent.setup();
    render(<App basePath="/ui/" />);
    await user.tab();
    expect(screen.getByRole("link", { name: "Skip to content" })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole("link", { name: "Library" })).toHaveFocus();
    for (const label of [
        "Operations",
        "Maintenance",
        "Administration",
        "Library",
    ]) {
        const link = screen.getByRole("link", { name: label });
        link.focus();
        await user.keyboard("{Enter}");
        expect(
            screen.getByRole("heading", { level: 1, name: label }),
        ).toBeInTheDocument();
        expect(link).toHaveAttribute("aria-current", "page");
        expect(screen.getByRole("main")).toHaveFocus();
        expect(document.title).toBe(`hfcache · ${label}`);
    }
});

test("unknown paths retain an explicit unavailable screen and a safe Library destination", async () => {
    window.history.replaceState(null, "", "/ui/not-a-workspace");
    render(<App basePath="/ui/" />);
    expect(
        screen.getByRole("heading", { level: 1, name: "Page unavailable" }),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: "Open Library" }));
    expect(
        screen.getByRole("heading", { level: 1, name: "Library" }),
    ).toBeInTheDocument();
});

test("mobile navigation is explicitly labelled and closes on navigation or history changes", async () => {
    render(<App basePath="/ui/" />);
    await userEvent.click(
        screen.getByRole("button", { name: "Open navigation" }),
    );
    expect(
        screen.getByRole("button", { name: "Close navigation" }),
    ).toHaveAttribute("aria-expanded", "true");
    await userEvent.click(screen.getByRole("link", { name: "Operations" }));
    expect(
        screen.getByRole("button", { name: "Open navigation" }),
    ).toHaveAttribute("aria-expanded", "false");
    act(() => {
        window.history.replaceState(null, "", "/ui/maintenance");
        window.dispatchEvent(new PopStateEvent("popstate"));
    });
    expect(
        screen.getByRole("heading", { level: 1, name: "Maintenance" }),
    ).toBeInTheDocument();
});

test("the mount boundary validates deployment metadata and supports owned cleanup", async () => {
    const bootstrap = uiBootstrapFixture();
    expect(() => mountApplication(document, bootstrap)).toThrow("container");
    const container = document.createElement("div");
    container.id = "root";
    document.body.append(container);
    expect(() => mountApplication(document, bootstrap)).toThrow();
    container.remove();
    inertUiDocument(document);
    let unmount = () => {};
    act(() => {
        unmount = mountApplication(document, bootstrap);
    });
    await waitFor(() => {
        expect(
            screen.getByRole("heading", { level: 1, name: "Library" }),
        ).toBeInTheDocument();
    });
    act(unmount);
    expect(document.getElementById("root")).toBeEmptyDOMElement();
});
