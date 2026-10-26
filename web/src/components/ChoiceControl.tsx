import { useEffect, useId, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

export type ChoiceOption<T extends string | number> = Readonly<{
    value: T;
    label: string;
}>;
export type ChoiceControlProps<T extends string | number> = {
    label: string;
    value: T;
    options: readonly ChoiceOption<T>[];
    onChange: (value: T) => void;
    disabled?: boolean;
};

/** A controlled, bounded choice with no native select or source-derived DOM IDs. */
export function ChoiceControl<T extends string | number>({
    label,
    value,
    options,
    onChange,
    disabled = false,
}: ChoiceControlProps<T>) {
    const id = useId();
    const root = useRef<HTMLDivElement>(null);
    const trigger = useRef<HTMLButtonElement>(null);
    const listbox = useRef<HTMLUListElement>(null);
    const coherent =
        label.length > 0 &&
        label.length <= 128 &&
        options.length > 0 &&
        options.length <= 32 &&
        new Set(options.map((option) => option.value)).size ===
            options.length &&
        options.every(
            (option) =>
                option.label.length > 0 &&
                option.label.length <= 128 &&
                (typeof option.value === "number"
                    ? Number.isFinite(option.value)
                    : option.value.length > 0 && option.value.length <= 128),
        );
    const selectedIndex = coherent
        ? options.findIndex((option) => Object.is(option.value, value))
        : -1;
    const selected = options[selectedIndex];
    const key =
        coherent && selected !== undefined
            ? JSON.stringify([
                  disabled,
                  value,
                  options.map((option) => [option.value, option.label]),
              ])
            : "unavailable";
    const [selection, setSelection] = useState({
        key,
        open: false,
        active: selectedIndex,
    });
    if (selection.key !== key)
        setSelection({ key, open: false, active: selectedIndex });
    // A new controlled value/list closes the old pending local choice immediately.
    const open =
        !disabled &&
        coherent &&
        selected !== undefined &&
        selection.key === key &&
        selection.open;
    const active = selection.key === key ? selection.active : selectedIndex;
    const labelId = id + "-label";
    const listId = id + "-list";
    const optionId = (index: number) => id + "-option-" + String(index);

    useEffect(() => {
        if (!open) return;
        listbox.current?.focus();
        function outside(event: Event) {
            if (
                !(event.target instanceof Node) ||
                !root.current?.contains(event.target)
            )
                setSelection((previous) => ({ ...previous, open: false }));
        }
        document.addEventListener("pointerdown", outside, true);
        document.addEventListener("focusin", outside, true);
        return () => {
            document.removeEventListener("pointerdown", outside, true);
            document.removeEventListener("focusin", outside, true);
        };
    }, [open]);
    useEffect(() => {
        if (!open) return;
        const option = listbox.current?.children.item(active);
        if (
            option instanceof HTMLElement &&
            typeof option.scrollIntoView === "function"
        )
            option.scrollIntoView({ block: "nearest" });
    }, [open, active]);

    function close(restoreFocus: boolean) {
        setSelection({ key, open: false, active: selectedIndex });
        if (restoreFocus) trigger.current?.focus();
    }
    function show() {
        if (!disabled && selected !== undefined && coherent)
            setSelection({ key, open: true, active: selectedIndex });
    }
    function commit(index: number) {
        const option = options[index];
        if (disabled || !coherent || !open || option === undefined) return;
        // Focus the still-mounted owner before the caller can change route/value.
        close(true);
        if (!Object.is(option.value, value)) onChange(option.value);
    }
    function navigate(event: KeyboardEvent<HTMLUListElement>) {
        let next: number;
        switch (event.key) {
            case "ArrowDown":
                next = (active + 1) % options.length;
                break;
            case "ArrowUp":
                next = (active + options.length - 1) % options.length;
                break;
            case "Home":
                next = 0;
                break;
            case "End":
                next = options.length - 1;
                break;
            case "Enter":
            case " ":
                event.preventDefault();
                commit(active);
                return;
            case "Escape":
                event.preventDefault();
                event.stopPropagation();
                close(true);
                return;
            default:
                // Tab keeps native navigation; the blur handler closes afterward.
                return;
        }
        event.preventDefault();
        setSelection({ key, open: true, active: next });
    }
    return (
        <div
            className="choice-control"
            ref={root}
            onBlur={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget))
                    close(false);
            }}
        >
            <span className="choice-control-label" id={labelId}>
                {label.length <= 128 ? label : "Choice"}
            </span>
            <button
                type="button"
                className="choice-control-trigger"
                ref={trigger}
                disabled={disabled || !coherent || selected === undefined}
                aria-label={
                    coherent && selected !== undefined
                        ? label + ": " + selected.label
                        : "Choice unavailable"
                }
                aria-haspopup="listbox"
                aria-expanded={open}
                aria-controls={open ? listId : undefined}
                onClick={() => {
                    if (open) close(false);
                    else show();
                }}
                onKeyDown={(event) => {
                    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
                        event.preventDefault();
                        show();
                    }
                }}
            >
                {coherent && selected !== undefined
                    ? selected.label
                    : "Unavailable"}
                <span aria-hidden="true"> ▾</span>
            </button>
            {!coherent || selected === undefined ? (
                <span role="alert">Choices are unavailable.</span>
            ) : null}
            {open && (
                <ul
                    className="choice-control-listbox"
                    id={listId}
                    role="listbox"
                    tabIndex={0}
                    aria-labelledby={labelId}
                    aria-activedescendant={optionId(active)}
                    ref={listbox}
                    onKeyDown={navigate}
                >
                    {options.map((option, index) => (
                        <li
                            key={index}
                            id={optionId(index)}
                            role="option"
                            aria-selected={Object.is(option.value, value)}
                            className={
                                "choice-control-option" +
                                (index === active ? " is-active" : "") +
                                (Object.is(option.value, value)
                                    ? " is-selected"
                                    : "")
                            }
                            onPointerEnter={() => {
                                setSelection({
                                    key,
                                    open: true,
                                    active: index,
                                });
                            }}
                            onClick={() => {
                                commit(index);
                            }}
                        >
                            {option.label}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
