import { useId } from "react";
import type { ReactNode } from "react";

export function Notice({ children }: { children: ReactNode }) {
    return (
        <div className="notice" role="status">
            <span aria-hidden="true">i</span>
            <div>{children}</div>
        </div>
    );
}

export function Panel({
    title,
    children,
}: {
    title: string;
    children: ReactNode;
}) {
    const heading = useId();
    return (
        <section className="panel" aria-labelledby={heading}>
            <header className="panel-heading">
                <h2 id={heading}>{title}</h2>
            </header>
            <div className="panel-body">{children}</div>
        </section>
    );
}
