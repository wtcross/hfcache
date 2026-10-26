import { Component, lazy, Suspense, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { publicationIdentity } from "../api/identity";
import type { ExactPublication } from "../api/identity";
import { applyCardSemantic } from "../wire/card-semantics";
import type { RepositoryCardRead } from "../wire/generated";
import { readmeAdmission } from "./policy";

const MarkdownBody = lazy(() => import("./MarkdownBody"));
class RenderBoundary extends Component<
    { children: ReactNode },
    { failed: boolean }
> {
    override state = { failed: false };
    static getDerivedStateFromError() {
        return { failed: true };
    }
    override render() {
        return this.state.failed ? (
            <p role="alert">
                README formatting is unavailable. The sanitized source and the
                rest of the interface remain available.
            </p>
        ) : (
            this.props.children
        );
    }
}
const reasons: Readonly<Record<string, string>> = {
    invalid_source: "The source cannot be admitted for formatting.",
    input_bytes: "The formatting input limit is 64KiB.",
    lines: "The source exceeds the formatting line limit.",
    line_length: "A line exceeds the formatting limit.",
    nesting: "The source is too deeply nested for formatting.",
    delimiters: "The source exceeds the formatting delimiter limit.",
    blocks: "The source exceeds the heading or fence limit.",
    code_block: "A code block exceeds the formatting limit.",
    table_cells: "A table exceeds the formatting cell limit.",
};
function captureMessage(state: string): string {
    switch (state) {
        case "present":
            return "A sanitized derivative of the archived README is available.";
        case "absent":
            return "This publication's manifest has no root README.md.";
        case "unsupported":
            return "README capture does not support this content. Its body is withheld.";
        case "oversize":
            return "README content exceeds the capture or presentation limit. Its body is withheld.";
        case "unsafe":
            return "README content was withheld by capture safety checks.";
        case "failed":
            return "README capture failed. No presentation body is available.";
        case "not_captured":
            return "No README capture exists for this exact publication.";
        default:
            return "This README capture state is unsupported. No body is available.";
    }
}
function admittedCard(
    card: RepositoryCardRead,
    identity: ExactPublication,
    generation: number,
): string | null {
    try {
        const key = publicationIdentity(identity);
        applyCardSemantic(
            "hfcache.card_models.RepositoryCardRead.strict_version",
            card.schema_version,
        );
        applyCardSemantic(
            "hfcache.card_models.RepositoryCardRead.coherent",
            card,
        );
        if (
            card.repository_type !== identity.repositoryType ||
            card.repository_id !== identity.repositoryId ||
            card.commit_sha !== identity.commitSha ||
            card.publication_id !== identity.publicationId ||
            card.publication_generation !== generation
        )
            return null;
        return (
            key +
            ":" +
            String(generation) +
            ":" +
            (card.presentation_sha256 ?? card.state)
        );
    } catch {
        return null;
    }
}

export function ReadmeCard({
    card,
    identity,
    publicationGeneration,
}: {
    card: RepositoryCardRead;
    identity: ExactPublication;
    publicationGeneration: number;
}) {
    const key = useMemo(
        () => admittedCard(card, identity, publicationGeneration),
        [card, identity, publicationGeneration],
    );
    const [selection, setSelection] = useState({
        key,
        mode: "rendered" as "rendered" | "source",
    });
    const mode = selection.key === key ? selection.mode : "rendered";
    if (key === null)
        return (
            <section className="panel readme-card" aria-label="Archived README">
                <h2>Archived README</h2>
                <p role="alert">
                    README evidence is invalid, unsupported or does not match
                    the selected publication. No body is shown.
                </p>
            </section>
        );
    const source = card.markdown;
    const admission = source === null ? null : readmeAdmission(source);
    return (
        <section className="panel readme-card" aria-label="Archived README">
            <header className="panel-heading">
                <h2>Archived README</h2>
            </header>
            <div className="panel-body">
                <p>
                    Capture state: <strong>{card.state}</strong>.{" "}
                    {captureMessage(card.state)}
                </p>
                <p>
                    Upstream README claims are derivative content, separate from
                    archive integrity. This view does not fetch media, contact
                    the Hub or recapture content.
                </p>
                <dl className="readme-provenance">
                    <div>
                        <dt>Publication</dt>
                        <dd>
                            <code>{card.commit_sha}</code> ·{" "}
                            <code>{card.publication_id}</code> · generation{" "}
                            {card.publication_generation}
                        </dd>
                    </div>
                    <div>
                        <dt>Capture time</dt>
                        <dd>{card.captured_at ?? "Not captured"}</dd>
                    </div>
                    <div>
                        <dt>Presentation version</dt>
                        <dd>{card.presentation_version ?? "Not captured"}</dd>
                    </div>
                    <div>
                        <dt>Expected README source SHA256</dt>
                        <dd>
                            <code>
                                {card.expected_source_sha256 ??
                                    "No source recorded"}
                            </code>
                        </dd>
                    </div>
                    <div>
                        <dt>Sanitized presentation SHA256</dt>
                        <dd>
                            <code>
                                {card.presentation_sha256 ??
                                    "No presentation recorded"}
                            </code>
                        </dd>
                    </div>
                </dl>
                {card.diagnostics.length > 0 && (
                    <p>Capture diagnostics: {card.diagnostics.join(", ")}</p>
                )}
                {source === null ? (
                    <p>
                        Sanitized source is unavailable for this capture state.
                        Capture changes require a separate explicit operation.
                    </p>
                ) : (
                    <>
                        <div
                            className="readme-toolbar"
                            role="group"
                            aria-label="README view"
                        >
                            <button
                                type="button"
                                aria-pressed={mode === "rendered"}
                                onClick={() => {
                                    setSelection({ key, mode: "rendered" });
                                }}
                            >
                                Rendered README
                            </button>
                            <button
                                type="button"
                                aria-pressed={mode === "source"}
                                onClick={() => {
                                    setSelection({ key, mode: "source" });
                                }}
                            >
                                Sanitized source
                            </button>
                        </div>
                        <p>
                            Only the exact verified sanitized presentation is
                            shown. Raw HTML and embedded resources are not
                            enabled; omitted content is not restored.
                        </p>
                        {mode === "source" ? (
                            <pre
                                className="readme-source"
                                tabIndex={0}
                                aria-label="Sanitized README source"
                            >
                                <code>{source}</code>
                            </pre>
                        ) : admission !== null && !admission.allowed ? (
                            <p role="alert">
                                Formatting was refused.{" "}
                                {reasons[admission.reason] ??
                                    "This content cannot be safely formatted."}{" "}
                                Sanitized source remains available.
                            </p>
                        ) : (
                            <RenderBoundary key={key}>
                                <Suspense
                                    fallback={
                                        <p role="status">
                                            Loading README formatting.
                                        </p>
                                    }
                                >
                                    <MarkdownBody
                                        source={source}
                                        identity={identity}
                                    />
                                </Suspense>
                            </RenderBoundary>
                        )}
                    </>
                )}
            </div>
        </section>
    );
}
