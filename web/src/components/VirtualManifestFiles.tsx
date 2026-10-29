import { useId, useLayoutEffect, useRef, useState } from "react";
import type { KeyboardEvent, ReactNode } from "react";
import type { FileEntry } from "../wire/generated";

const ROW_HEIGHT = 72;
const HEADER_HEIGHT = 40;
const OVERSCAN = 3;
const MAX_VISIBLE = 16;

interface Props {
    readonly identity: string;
    readonly files: readonly FileEntry[];
    readonly renderDetails: (file: FileEntry) => ReactNode;
}

/** INV-021: only a bounded window of the already validated exact manifest. */
export function VirtualManifestFiles(props: Props) {
    return <ManifestWindow key={props.identity} {...props} />;
}

function ManifestWindow({ files, renderDetails }: Props) {
    const viewport = useRef<HTMLDivElement>(null);
    const detailsHeading = useRef<HTMLHeadingElement>(null);
    const pendingFocus = useRef<number | null>(null);
    const focusDetails = useRef(false);
    const instructions = useId();
    const detailsId = useId();
    const [top, setTop] = useState(0);
    const [height, setHeight] = useState(384);
    const [focused, setFocused] = useState<number | null>(null);
    const [selected, setSelected] = useState<number | null>(null);
    const [fileNumber, setFileNumber] = useState("");
    const [error, setError] = useState(false);
    const last = Math.max(0, files.length - 1);
    const firstVisible = Math.min(last, Math.floor(top / ROW_HEIGHT));
    const visibleCount = Math.max(
        1,
        Math.min(MAX_VISIBLE, Math.ceil((height - HEADER_HEIGHT) / ROW_HEIGHT)),
    );
    const start = Math.max(0, firstVisible - OVERSCAN);
    const end = Math.min(
        files.length,
        firstVisible + visibleCount + OVERSCAN + 1,
    );
    const indices = Array.from(
        { length: end - start },
        (_, index) => start + index,
    );
    // Scrolling must not remove the focused control from the accessibility tree.
    if (
        focused !== null &&
        focused < files.length &&
        !indices.includes(focused)
    )
        indices.push(focused);
    indices.sort((left, right) => left - right);
    const selectedFile = selected === null ? undefined : files[selected];

    useLayoutEffect(() => {
        const element = viewport.current;
        if (element === null) return;
        const measure = () => {
            if (element.clientHeight > 0)
                setHeight(
                    Math.min(
                        element.clientHeight,
                        HEADER_HEIGHT + MAX_VISIBLE * ROW_HEIGHT,
                    ),
                );
        };
        measure();
        const observer =
            typeof ResizeObserver === "undefined"
                ? null
                : new ResizeObserver(measure);
        observer?.observe(element);
        const window = element.ownerDocument.defaultView;
        window?.addEventListener("resize", measure);
        return () => {
            observer?.disconnect();
            window?.removeEventListener("resize", measure);
        };
    }, []);

    useLayoutEffect(() => {
        if (focusDetails.current && detailsHeading.current !== null) {
            focusDetails.current = false;
            detailsHeading.current.focus();
        }
        if (pendingFocus.current !== null) {
            const button = viewport.current?.querySelector<HTMLButtonElement>(
                `[data-file-index="${String(pendingFocus.current)}"] button`,
            );
            if (button !== null && button !== undefined) {
                pendingFocus.current = null;
                button.focus({ preventScroll: true });
            }
        }
    });

    const show = (index: number, moveFocus: boolean) => {
        const position = Math.max(0, Math.min(last, index));
        const offset = position * ROW_HEIGHT;
        if (moveFocus) {
            pendingFocus.current = position;
            setFocused(position);
        }
        if (viewport.current !== null) viewport.current.scrollTop = offset;
        setTop(offset);
        if (moveFocus) {
            const button = viewport.current?.querySelector<HTMLButtonElement>(
                `[data-file-index="${String(position)}"] button`,
            );
            if (button !== null && button !== undefined) {
                pendingFocus.current = null;
                button.focus({ preventScroll: true });
            }
        }
    };
    const navigate = (event: KeyboardEvent<HTMLDivElement>) => {
        if (
            event.altKey ||
            event.ctrlKey ||
            event.metaKey ||
            files.length === 0
        )
            return;
        const current = focused ?? firstVisible;
        const positions: Readonly<Record<string, number>> = {
            ArrowDown: current + 1,
            ArrowUp: current - 1,
            PageDown: current + visibleCount,
            PageUp: current - visibleCount,
            Home: 0,
            End: last,
        };
        const next = positions[event.key];
        if (next === undefined) return;
        event.preventDefault();
        show(next, true);
    };
    const rows: ReactNode[] = [];
    let cursor = 0;
    const spacer = (from: number, until: number) => {
        if (until <= from) return;
        rows.push(
            <tr
                key={`gap-${String(from)}`}
                aria-hidden="true"
                role="presentation"
                className="virtual-manifest-spacer"
                style={{ height: (until - from) * ROW_HEIGHT }}
            >
                <td colSpan={3} />
            </tr>,
        );
    };
    for (const index of indices) {
        const file = files[index];
        if (file === undefined) continue;
        spacer(cursor, index);
        rows.push(
            <tr
                key={index}
                className="virtual-manifest-row"
                data-file-index={index}
                aria-rowindex={index + 2}
            >
                <th scope="row">
                    <code title={file.path}>{file.path}</code>
                </th>
                <td>{file.size.toLocaleString("en-US")}</td>
                <td>
                    <button
                        type="button"
                        aria-label={`Inspect metadata for file ${String(index + 1)}`}
                        aria-controls={detailsId}
                        aria-pressed={selected === index}
                        onFocus={() => {
                            setFocused(index);
                        }}
                        onClick={() => {
                            if (
                                selected === index &&
                                detailsHeading.current !== null
                            ) {
                                detailsHeading.current.focus();
                                return;
                            }
                            focusDetails.current = true;
                            setSelected(index);
                        }}
                    >
                        Inspect metadata
                    </button>
                </td>
            </tr>,
        );
        cursor = index + 1;
    }
    spacer(cursor, files.length);

    return (
        <section aria-label="Virtualized manifest files">
            <p id={instructions}>
                Large manifest: the table mounts a finite window of file
                metadata. Scroll, or use Arrow Up/Down, Page Up/Down, Home and
                End while the table has focus. Inspect one file for its full
                path, hashes and provenance. No file payload is fetched.
            </p>
            <p role="status">
                {files.length === 0
                    ? "No files in this loaded manifest."
                    : `File window ${String(firstVisible + 1)}–${String(Math.min(firstVisible + visibleCount, files.length))} of ${files.length.toLocaleString("en-US")} files in this loaded manifest.`}
            </p>
            <div
                className="repository-table-scroll virtual-manifest-scroll"
                ref={viewport}
                role="region"
                aria-label="Virtualized manifest file table"
                aria-describedby={instructions}
                tabIndex={0}
                onKeyDown={navigate}
                onBlur={(event) => {
                    if (!event.currentTarget.contains(event.relatedTarget))
                        setFocused(null);
                }}
                onScroll={(event) => {
                    setTop(Math.max(0, event.currentTarget.scrollTop));
                }}
            >
                <table
                    aria-label="Manifest files"
                    aria-rowcount={files.length + 1}
                >
                    <thead>
                        <tr aria-rowindex={1}>
                            <th scope="col">Path</th>
                            <th scope="col">Logical bytes</th>
                            <th scope="col">Evidence</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
            <div className="repository-local-pages">
                <button
                    type="button"
                    disabled={firstVisible === 0}
                    onClick={() => {
                        show(firstVisible - 25, false);
                    }}
                >
                    Previous files
                </button>
                <button
                    type="button"
                    disabled={firstVisible + visibleCount >= files.length}
                    onClick={() => {
                        show(firstVisible + 25, false);
                    }}
                >
                    Next files
                </button>
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        const value = Number(fileNumber);
                        if (
                            !/^[1-9][0-9]*$/u.test(fileNumber) ||
                            !Number.isSafeInteger(value) ||
                            value > files.length
                        ) {
                            setError(true);
                            return;
                        }
                        setError(false);
                        show(value - 1, true);
                    }}
                >
                    <label>
                        File number
                        <input
                            inputMode="numeric"
                            maxLength={Math.max(1, String(files.length).length)}
                            value={fileNumber}
                            onChange={(event) => {
                                setFileNumber(event.currentTarget.value);
                            }}
                        />
                    </label>
                    <button type="submit" disabled={files.length === 0}>
                        Go to file
                    </button>
                    {error && (
                        <p role="alert">
                            Enter a whole file number from 1 to {files.length}.
                        </p>
                    )}
                </form>
            </div>
            <section
                id={detailsId}
                aria-label="Selected manifest file metadata"
            >
                {selectedFile === undefined ? (
                    <p>Choose Inspect metadata for one file.</p>
                ) : (
                    <>
                        <h4 ref={detailsHeading} tabIndex={-1}>
                            File {String((selected ?? 0) + 1)} metadata
                        </h4>
                        <p className="virtual-manifest-selected-path">
                            <code>{selectedFile.path}</code>
                        </p>
                        <p>
                            {selectedFile.size.toLocaleString("en-US")} logical
                            bytes.
                        </p>
                        {renderDetails(selectedFile)}
                        <button
                            type="button"
                            onClick={() => {
                                show(selected ?? 0, true);
                            }}
                        >
                            Return to selected file
                        </button>
                    </>
                )}
            </section>
        </section>
    );
}
