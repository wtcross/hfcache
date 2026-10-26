/** Controlled DOM boundary tests; installed CSP/browser conformance is separate. */
import { useState } from "react";
import {
    act,
    cleanup,
    fireEvent,
    render,
    screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { ChoiceControl } from "../src/components/ChoiceControl";
import type { ChoiceOption } from "../src/components/ChoiceControl";

const choices = [
    { value: "a", label: "Alpha" },
    { value: "b", label: "Bravo" },
    { value: "c", label: "Charlie" },
] as const;
type Value = (typeof choices)[number]["value"];
function Controlled({ changed }: { changed: (value: Value) => void }) {
    const [value, setValue] = useState<Value>("b");
    return (
        <ChoiceControl
            label="Mode"
            value={value}
            options={choices}
            onChange={(next) => {
                changed(next);
                setValue(next);
            }}
        />
    );
}
function activeLabel(): string | null | undefined {
    const list = screen.getByRole("listbox");
    const id = list.getAttribute("aria-activedescendant");
    return id === null ? null : document.getElementById(id)?.textContent;
}
afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
});

test("arrows and Home/End explore locally, then Enter commits one actual typed option and restores focus", async () => {
    const changed = vi.fn<(value: Value) => void>();
    render(<Controlled changed={changed} />);
    const user = userEvent.setup();
    const trigger = screen.getByRole("button", { name: "Mode: Bravo" });
    trigger.focus();
    await user.keyboard("{ArrowDown}");
    expect(screen.getByRole("listbox", { name: "Mode" })).toHaveFocus();
    expect(activeLabel()).toBe("Bravo");
    const scrolling = vi.fn();
    Object.defineProperty(
        screen.getByRole("option", { name: "Charlie" }),
        "scrollIntoView",
        { value: scrolling },
    );
    await user.keyboard("{ArrowDown}{Home}{End}");
    expect(activeLabel()).toBe("Charlie");
    expect(scrolling).toHaveBeenCalledWith({ block: "nearest" });
    expect(screen.getByRole("option", { name: "Bravo" })).toHaveAttribute(
        "aria-selected",
        "true",
    );
    expect(changed).not.toHaveBeenCalled();
    await user.keyboard("{Enter}");
    expect(changed).toHaveBeenCalledExactlyOnceWith("c");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mode: Charlie" })).toHaveFocus();
});

test("Space opens and commits while reselecting the controlled value has no callback", async () => {
    const changed = vi.fn<(value: Value) => void>();
    render(<Controlled changed={changed} />);
    const user = userEvent.setup();
    screen.getByRole("button").focus();
    await user.keyboard(" ");
    expect(activeLabel()).toBe("Bravo");
    await user.keyboard(" ");
    expect(changed).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button"));
    await user.keyboard("{ArrowUp} ");
    expect(changed).toHaveBeenCalledExactlyOnceWith("a");
});

test("Escape discards the active option, returns focus and preserves the committed label", async () => {
    const changed = vi.fn<(value: Value) => void>();
    render(<Controlled changed={changed} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button"));
    await user.keyboard("{ArrowUp}{Escape}");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mode: Bravo" })).toHaveFocus();
    expect(changed).not.toHaveBeenCalled();
});

test("Tab leaves naturally and outside pointer/focus never commit or steal focus", async () => {
    const changed = vi.fn<(value: Value) => void>();
    render(
        <>
            <Controlled changed={changed} />
            <button type="button">Next field</button>
        </>,
    );
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Mode: Bravo" }));
    await user.keyboard("{ArrowDown}");
    await user.tab();
    const next = screen.getByRole("button", { name: "Next field" });
    expect(next).toHaveFocus();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Mode: Bravo" }));
    await user.click(next);
    expect(next).toHaveFocus();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Mode: Bravo" }));
    act(() => {
        next.focus();
    });
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(changed).not.toHaveBeenCalled();
});

test("clicks pass numeric values without string coercion or implicit form submission", async () => {
    const changed = vi.fn<(value: number) => void>();
    const submitted = vi.fn();
    render(
        <form onSubmit={submitted}>
            <ChoiceControl
                label="Page size"
                value={7}
                options={[
                    { value: 7, label: "7" },
                    { value: 25, label: "25" },
                ]}
                onChange={changed}
            />
        </form>,
    );
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Page size: 7" }));
    await user.click(screen.getByRole("option", { name: "25" }));
    expect(changed).toHaveBeenCalledExactlyOnceWith(25);
    expect(screen.getByRole("button", { name: "Page size: 7" })).toHaveFocus();
    expect(submitted).not.toHaveBeenCalled();
});

test("controlled replacements discard pending local state, including when old props return", async () => {
    const changed = vi.fn<(value: string) => void>();
    const view = render(
        <ChoiceControl
            label="Mode"
            value="b"
            options={choices}
            onChange={changed}
        />,
    );
    const user = userEvent.setup();
    await user.click(screen.getByRole("button"));
    await user.keyboard("{End}");
    view.rerender(
        <ChoiceControl
            label="Mode"
            value="a"
            options={choices}
            onChange={changed}
        />,
    );
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(screen.getByRole("button")).toHaveAccessibleName("Mode: Alpha");
    view.rerender(
        <ChoiceControl
            label="Mode"
            value="b"
            options={choices}
            onChange={changed}
        />,
    );
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button"));
    expect(activeLabel()).toBe("Bravo");
    view.rerender(
        <ChoiceControl
            label="Mode"
            value="a"
            options={choices.slice(0, 1)}
            onChange={changed}
        />,
    );
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(changed).not.toHaveBeenCalled();
});

test("disabled transitions close without reviving a pending choice after re-enable", async () => {
    const changed = vi.fn<(value: string) => void>();
    const view = render(
        <ChoiceControl
            label="Mode"
            value="a"
            options={choices}
            onChange={changed}
        />,
    );
    const user = userEvent.setup();
    await user.click(screen.getByRole("button"));
    view.rerender(
        <ChoiceControl
            label="Mode"
            value="a"
            options={choices}
            onChange={changed}
            disabled
        />,
    );
    expect(screen.getByRole("button")).toBeDisabled();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button"));
    view.rerender(
        <ChoiceControl
            label="Mode"
            value="a"
            options={choices}
            onChange={changed}
        />,
    );
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(changed).not.toHaveBeenCalled();
});

test("multiple instances have unique trusted IDs and opening one closes the other", async () => {
    render(
        <>
            <Controlled changed={() => {}} />
            <Controlled changed={() => {}} />
        </>,
    );
    const user = userEvent.setup();
    const triggers = screen.getAllByRole("button");
    const first = triggers[0],
        second = triggers[1];
    if (first === undefined || second === undefined)
        throw new Error("Missing fixture choices.");
    await user.click(first);
    const firstId = screen.getByRole("listbox").id;
    await user.click(second);
    const list = screen.getByRole("listbox");
    expect(list.id).not.toBe(firstId);
    expect(first).toHaveAttribute("aria-expanded", "false");
    expect(second).toHaveAttribute("aria-controls", list.id);
    const ids = [...document.querySelectorAll("[id]")].map(
        (element) => element.id,
    );
    expect(new Set(ids).size).toBe(ids.length);
});

test.each(
    (
        [
            [],
            Array.from({ length: 33 }, (_, index) => ({
                value: String(index),
                label: String(index),
            })),
            [
                { value: "a", label: "Alpha" },
                { value: "a", label: "Duplicate" },
            ],
            [{ value: "a", label: "x".repeat(129) }],
            [{ value: "missing", label: "Other" }],
        ] satisfies readonly (readonly ChoiceOption<string>[])[]
    ).map((options) => ({ options })),
)(
    "incoherent or unbounded options refuse without inventing a committed value (%#)",
    ({ options }) => {
        const changed = vi.fn();
        render(
            <ChoiceControl
                label="Mode"
                value="a"
                options={options}
                onChange={changed}
            />,
        );
        expect(screen.getByRole("button")).toBeDisabled();
        expect(screen.getByRole("alert")).toHaveTextContent(
            "Choices are unavailable.",
        );
        expect(changed).not.toHaveBeenCalled();
    },
);

test("labels remain inert and no native select, inline style or hidden input is created", async () => {
    const label = '<img src="/api/v1/status" onerror="alert(1)">';
    const view = render(
        <ChoiceControl
            label="Mode"
            value="a"
            options={[{ value: "a", label }]}
            onChange={() => {}}
        />,
    );
    await userEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("option")).toHaveTextContent(label);
    expect(
        view.container.querySelector("select,input,img,script,[style]"),
    ).toBeNull();
    view.unmount();
    const outside = render(<button type="button">Other route</button>);
    fireEvent.pointerDown(screen.getByRole("button"));
    screen.getByRole("button").focus();
    expect(screen.getByRole("button")).toHaveFocus();
    outside.unmount();
});
