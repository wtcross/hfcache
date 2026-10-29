import {
    act,
    cleanup,
    fireEvent,
    render,
    screen,
    within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { VirtualManifestFiles } from "../src/components/VirtualManifestFiles";
import type { FileEntry } from "../src/wire/generated";

afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
});

function file(index: number): FileEntry {
    return {
        path: `file-${String(index).padStart(5, "0")}.txt`,
        size: index === 9999 ? Number.MAX_SAFE_INTEGER : 0,
        sha256: "e".repeat(64),
        provenance: {
            cache_root: "canonical",
            hash_reused_from: null,
            hashed: true,
            source: "hub_download",
        },
        upstream: { git_oid: null, lfs_sha256: null, xet_hash: null },
    };
}
function fixture(count = 10000) {
    const files = Array.from({ length: count }, (_, index) => file(index));
    const details = vi.fn((value: FileEntry) => (
        <p>
            Expected digest <code>{value.sha256}</code>
        </p>
    ));
    const view = render(
        <VirtualManifestFiles
            identity="sha:publication:first"
            files={files}
            renderDetails={details}
        />,
    );
    const viewport = screen.getByRole("region", {
        name: "Virtualized manifest file table",
    });
    const table = screen.getByRole("table", { name: "Manifest files" });
    return { files, details, view, viewport, table };
}
function inspect(index: number) {
    return screen.getByRole("button", {
        name: `Inspect metadata for file ${String(index + 1)}`,
    });
}
function fileRows(table: HTMLElement) {
    return table.querySelectorAll("tr[data-file-index]");
}

test("ten thousand accepted files keep bounded DOM, real table headers and actual row positions", () => {
    const f = fixture();
    expect(f.table).toHaveAttribute("aria-rowcount", "10001");
    expect(
        within(f.table)
            .getAllByRole("columnheader")
            .map((node) => node.textContent),
    ).toEqual(["Path", "Logical bytes", "Evidence"]);
    expect(fileRows(f.table).length).toBeLessThanOrEqual(24);
    expect(fileRows(f.table)[0]).toHaveAttribute("aria-rowindex", "2");
    expect(inspect(0)).toHaveTextContent("Inspect metadata");
    expect(f.details).not.toHaveBeenCalled();
    fireEvent.scroll(f.viewport, { target: { scrollTop: 5000 * 72 } });
    expect(
        screen.getByRole("rowheader", { name: file(5000).path }),
    ).toBeInTheDocument();
    expect(
        screen.queryByRole("rowheader", { name: file(0).path }),
    ).not.toBeInTheDocument();
    expect(fileRows(f.table).length).toBeLessThanOrEqual(24);
    expect(screen.getByRole("status")).toHaveTextContent("File window 5001");
    expect(f.details).not.toHaveBeenCalled();
});

test("keyboard End Home arrows and page keys reach unmounted rows and preserve exact large sizes", () => {
    const f = fixture();
    fireEvent.keyDown(f.viewport, { key: "End" });
    expect(inspect(9999)).toHaveFocus();
    expect(inspect(9999).closest("tr")).toHaveAttribute(
        "aria-rowindex",
        "10001",
    );
    const lastRow = inspect(9999).closest("tr");
    if (lastRow === null)
        throw new Error("The last file must have a table row.");
    expect(
        within(lastRow).getByRole("cell", {
            name: "9,007,199,254,740,991",
        }),
    ).toBeInTheDocument();
    fireEvent.keyDown(inspect(9999), { key: "ArrowDown" });
    expect(inspect(9999)).toHaveFocus();
    fireEvent.keyDown(inspect(9999), { key: "Home" });
    expect(inspect(0)).toHaveFocus();
    fireEvent.keyDown(inspect(0), { key: "ArrowUp" });
    expect(inspect(0)).toHaveFocus();
    fireEvent.keyDown(inspect(0), { key: "ArrowDown" });
    expect(inspect(1)).toHaveFocus();
    fireEvent.keyDown(inspect(1), { key: "PageDown" });
    expect(inspect(6)).toHaveFocus();
    fireEvent.keyDown(inspect(6), { key: "PageUp" });
    expect(inspect(1)).toHaveFocus();
    fireEvent.keyDown(inspect(1), { key: "End", ctrlKey: true });
    expect(inspect(1)).toHaveFocus();
    fireEvent.keyDown(inspect(1), { key: "Escape" });
    expect(inspect(1)).toHaveFocus();
    expect(fileRows(f.table).length).toBeLessThanOrEqual(24);
});

test("wheel scrolling retains the actual focused row until focus deliberately leaves", async () => {
    const f = fixture();
    const original = inspect(0);
    act(() => {
        original.focus();
    });
    fireEvent.scroll(f.viewport, { target: { scrollTop: 5000 * 72 } });
    expect(original).toHaveFocus();
    expect(original).toBeInTheDocument();
    expect(inspect(5000)).toBeInTheDocument();
    expect(fileRows(f.table).length).toBeLessThanOrEqual(24);
    await userEvent.click(screen.getByLabelText("File number"));
    expect(
        screen.queryByRole("rowheader", { name: file(0).path }),
    ).not.toBeInTheDocument();
});

test("inspect exposes one complete escaped path and digest, then returns to its original row", async () => {
    const files = Array.from({ length: 300 }, (_, index) => file(index));
    const hostile =
        "nested/" +
        Array.from({ length: 5 }, () => "long-".repeat(30)).join("/") +
        "/<img src=x onerror=alert(1)>.txt";
    files[299] = { ...file(299), path: hostile };
    const details = vi.fn((value: FileEntry) => <p>Digest {value.sha256}</p>);
    render(
        <VirtualManifestFiles
            identity="exact-pair"
            files={files}
            renderDetails={details}
        />,
    );
    const viewport = screen.getByRole("region", {
        name: "Virtualized manifest file table",
    });
    fireEvent.keyDown(viewport, { key: "End" });
    const button = screen.getByRole("button", {
        name: "Inspect metadata for file 300",
    });
    await userEvent.click(button);
    const heading = screen.getByRole("heading", { name: "File 300 metadata" });
    expect(heading).toHaveFocus();
    const selected = screen.getByRole("region", {
        name: "Selected manifest file metadata",
    });
    expect(within(selected).getByText(hostile)).toBeInTheDocument();
    expect(
        within(selected).getByText("Digest " + "e".repeat(64)),
    ).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
    expect(details).toHaveBeenLastCalledWith(files[299]);
    await userEvent.click(
        screen.getByRole("button", { name: "Return to selected file" }),
    );
    expect(button).toHaveFocus();
    await userEvent.click(button);
    expect(heading).toHaveFocus();
});

test("explicit file-number jumps reject fractional exponential zero and out-of-range values", async () => {
    fixture(200);
    const input = screen.getByLabelText("File number");
    for (const value of [
        "",
        "0",
        "1.5",
        "1e2",
        "201",
        "-1",
        "9007199254740993",
    ]) {
        fireEvent.change(input, { target: { value } });
        const form = input.closest("form");
        if (form === null) throw new Error("File navigation must have a form.");
        fireEvent.submit(form);
        expect(screen.getByRole("alert")).toHaveTextContent(
            "Enter a whole file number from 1 to 200.",
        );
        expect(inspect(0)).toBeInTheDocument();
    }
    fireEvent.change(input, { target: { value: "200" } });
    await userEvent.click(screen.getByRole("button", { name: "Go to file" }));
    expect(inspect(199)).toHaveFocus();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next files" })).toBeDisabled();
    await userEvent.click(
        screen.getByRole("button", { name: "Previous files" }),
    );
    expect(screen.getByRole("status")).toHaveTextContent("File window 175");
    expect(
        screen.getByRole("button", { name: "Previous files" }),
    ).toHaveFocus();
});

test("changing exact publication resets scroll focus selection and file-number intent before rendering", async () => {
    const f = fixture(200);
    fireEvent.keyDown(f.viewport, { key: "End" });
    await userEvent.click(inspect(199));
    fireEvent.change(screen.getByLabelText("File number"), {
        target: { value: "180" },
    });
    const replacement = [
        { ...file(0), path: "replacement.txt", sha256: "d".repeat(64) },
    ];
    f.view.rerender(
        <VirtualManifestFiles
            identity="sha:publication:replacement"
            files={replacement}
            renderDetails={f.details}
        />,
    );
    expect(
        screen.queryByRole("heading", { name: "File 200 metadata" }),
    ).not.toBeInTheDocument();
    expect(screen.getByLabelText("File number")).toHaveValue("");
    expect(screen.getByRole("status")).toHaveTextContent(
        "File window 1–1 of 1",
    );
    expect(
        screen.getByRole("rowheader", { name: "replacement.txt" }),
    ).toBeInTheDocument();
    expect(screen.queryByText(file(199).path)).not.toBeInTheDocument();
    expect(
        screen.getByRole("region", { name: "Virtualized manifest file table" })
            .scrollTop,
    ).toBe(0);
});

test("viewport resize still caps mounted rows and releases observer and resize ownership on unmount", () => {
    let callback: ResizeObserverCallback | undefined;
    const disconnect = vi.fn();
    const resizeObserver: ResizeObserver = {
        observe() {},
        unobserve() {},
        disconnect,
    };
    vi.stubGlobal(
        "ResizeObserver",
        class implements ResizeObserver {
            constructor(value: ResizeObserverCallback) {
                callback = value;
            }
            observe() {}
            unobserve() {}
            disconnect = disconnect;
        },
    );
    const f = fixture();
    Object.defineProperty(f.viewport, "clientHeight", {
        configurable: true,
        value: 100000,
    });
    act(() => {
        callback?.([], resizeObserver);
    });
    expect(fileRows(f.table).length).toBeLessThanOrEqual(24);
    act(() => {
        inspect(0).focus();
    });
    fireEvent.scroll(f.viewport, { target: { scrollTop: 9000 * 72 } });
    expect(fileRows(f.table).length).toBeLessThanOrEqual(24);
    const removed = vi.spyOn(window, "removeEventListener");
    f.view.unmount();
    expect(disconnect).toHaveBeenCalledOnce();
    expect(removed).toHaveBeenCalledWith("resize", expect.any(Function));
});

test("empty accepted manifest is explicitly empty with no inspection or navigation", () => {
    const f = fixture(0);
    expect(screen.getByRole("status")).toHaveTextContent(
        "No files in this loaded manifest.",
    );
    expect(f.table).toHaveAttribute("aria-rowcount", "1");
    expect(screen.getByRole("button", { name: "Go to file" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next files" })).toBeDisabled();
    fireEvent.keyDown(f.viewport, { key: "End" });
    expect(f.details).not.toHaveBeenCalled();
    expect(fileRows(f.table)).toHaveLength(0);
});
