/** ADR155: the lazy parser has no raw HTML, source attributes or resource-fetching components. */
import ReactMarkdown from "react-markdown";
import type { Components, ExtraProps } from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import type { Options as SanitizeOptions } from "rehype-sanitize";
import type { ExactPublication } from "../api/identity";
import { readmeAdmission, readmeIdPrefix, readmeLink } from "./policy";

const TAGS = [
    "a",
    "p",
    "br",
    "hr",
    "blockquote",
    "ul",
    "ol",
    "li",
    "strong",
    "em",
    "del",
    "code",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "sup",
];
const SCHEMA: SanitizeOptions = {
    tagNames: TAGS,
    attributes: { a: ["href"] },
    protocols: { href: ["http", "https"] },
    clobber: ["id", "name"],
    clobberPrefix: "readme-stripped-",
    strip: [
        "script",
        "style",
        "iframe",
        "form",
        "input",
        "textarea",
        "select",
        "button",
        "svg",
        "math",
        "object",
        "embed",
        "img",
        "picture",
        "video",
        "audio",
        "source",
        "canvas",
    ],
};
function record(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}
const MAX_CODE_BYTES = 16 * 1024;
const utf8 = new TextEncoder();
function codeBytes(value: unknown, remaining = MAX_CODE_BYTES): number {
    // Bound the allocation before encoding, independently of lexical admission.
    if (typeof value !== "string" || value.length > remaining)
        throw new Error("readme-code-bounds");
    const bytes = utf8.encode(value).length;
    if (bytes > remaining) throw new Error("readme-code-bounds");
    return bytes;
}
/** Iterative before/after sanitizer walks bound both parser output and generated GFM structure. */
function walk(tree: unknown, visit?: (node: Record<string, unknown>) => void) {
    const stack: {
        node: unknown;
        depth: number;
        codeBlock: { bytes: number } | null;
    }[] = [{ node: tree, depth: 0, codeBlock: null }];
    let nodes = 0,
        headings = 0,
        cells = 0;
    while (stack.length > 0) {
        const item = stack.pop();
        if (
            item === undefined ||
            !record(item.node) ||
            typeof item.node.type !== "string"
        )
            throw new Error("readme-tree");
        const { node, depth } = item;
        if (++nodes > 4096 || depth > 24) throw new Error("readme-tree-bounds");
        if (node.type === "code") codeBytes(node.value);
        // HAST can split block-code text across descendants. Charge it once
        // during this same bounded walk, including the parser's trailing LF.
        const codeBlock =
            item.codeBlock ??
            (node.type === "element" && node.tagName === "pre"
                ? { bytes: 0 }
                : null);
        if (codeBlock !== null && node.type === "text")
            codeBlock.bytes += codeBytes(
                node.value,
                MAX_CODE_BYTES - codeBlock.bytes,
            );
        const heading =
            node.type === "heading" ||
            (node.type === "element" &&
                typeof node.tagName === "string" &&
                /^h[1-6]$/u.test(node.tagName));
        if (heading && ++headings > 128)
            throw new Error("readme-heading-bounds");
        if (
            (node.type === "tableCell" ||
                (node.type === "element" &&
                    (node.tagName === "th" || node.tagName === "td"))) &&
            ++cells > 256
        )
            throw new Error("readme-table-bounds");
        visit?.(node);
        const children = node.children;
        if (children !== undefined) {
            if (
                !Array.isArray(children) ||
                nodes + stack.length + children.length > 4096
            )
                throw new Error("readme-tree-bounds");
            for (let index = children.length - 1; index >= 0; index--)
                stack.push({
                    node: children[index],
                    depth: depth + 1,
                    codeBlock,
                });
        }
    }
}
function boundMarkdown() {
    return (tree: unknown) => {
        walk(tree);
    };
}
function inertElements() {
    return (tree: unknown) => {
        walk(tree, (node) => {
            if (
                node.type !== "element" ||
                (node.tagName !== "img" && node.tagName !== "input")
            )
                return;
            const value =
                node.tagName === "img"
                    ? "[Image omitted]"
                    : "[Task checkbox omitted]";
            for (const key of Object.keys(node))
                Reflect.deleteProperty(node, key);
            node.type = "text";
            node.value = value;
        });
    };
}

export default function MarkdownBody({
    source,
    identity,
}: {
    source: string;
    identity: ExactPublication;
}) {
    // Keep the admission even for a future direct caller of this internal component.
    if (!readmeAdmission(source).allowed) throw new Error("readme-admission");
    const prefix = readmeIdPrefix(identity);
    const ordinals = new WeakMap<object, number>();
    function trustedHeadings() {
        return (tree: unknown) => {
            let ordinal = 0;
            walk(tree, (node) => {
                if (
                    node.type === "element" &&
                    typeof node.tagName === "string" &&
                    /^h[1-6]$/u.test(node.tagName)
                )
                    ordinals.set(node, ++ordinal);
            });
        };
    }
    function headingId(node: ExtraProps["node"]): string {
        const ordinal = node === undefined ? undefined : ordinals.get(node);
        if (ordinal === undefined) throw new Error("readme-heading");
        return prefix + String(ordinal);
    }
    const components = {
        a: ({ children, href }) => {
            const destination =
                href === undefined
                    ? null
                    : readmeLink(
                          href,
                          identity,
                          typeof document === "undefined"
                              ? ""
                              : document.location.origin,
                      );
            return destination === null ? (
                <span>{children} (link unavailable)</span>
            ) : (
                <a
                    href={destination}
                    target="_blank"
                    rel="noopener noreferrer"
                    referrerPolicy="no-referrer"
                >
                    {children}
                </a>
            );
        },
        h1: ({ node, children }) => <h1 id={headingId(node)}>{children}</h1>,
        h2: ({ node, children }) => <h2 id={headingId(node)}>{children}</h2>,
        h3: ({ node, children }) => <h3 id={headingId(node)}>{children}</h3>,
        h4: ({ node, children }) => <h4 id={headingId(node)}>{children}</h4>,
        h5: ({ node, children }) => <h5 id={headingId(node)}>{children}</h5>,
        h6: ({ node, children }) => <h6 id={headingId(node)}>{children}</h6>,
        p: ({ children }) => <p>{children}</p>,
        br: () => <br />,
        hr: () => <hr />,
        blockquote: ({ children }) => <blockquote>{children}</blockquote>,
        ul: ({ children }) => <ul>{children}</ul>,
        ol: ({ children }) => <ol>{children}</ol>,
        li: ({ children }) => <li>{children}</li>,
        strong: ({ children }) => <strong>{children}</strong>,
        em: ({ children }) => <em>{children}</em>,
        del: ({ children }) => <del>{children}</del>,
        code: ({ children }) => <code>{children}</code>,
        pre: ({ children }) => <pre tabIndex={0}>{children}</pre>,
        table: ({ children }) => (
            <div
                className="readme-table-scroll"
                tabIndex={0}
                role="region"
                aria-label="README table, scroll horizontally"
            >
                <table>{children}</table>
            </div>
        ),
        thead: ({ children }) => <thead>{children}</thead>,
        tbody: ({ children }) => <tbody>{children}</tbody>,
        tr: ({ children }) => <tr>{children}</tr>,
        th: ({ children }) => <th>{children}</th>,
        td: ({ children }) => <td>{children}</td>,
        sup: ({ children }) => <sup>{children}</sup>,
    } satisfies Components;
    return (
        <div className="readme-markdown">
            <ReactMarkdown
                skipHtml
                allowedElements={TAGS}
                components={components}
                remarkPlugins={[remarkGfm, boundMarkdown]}
                rehypePlugins={[
                    inertElements,
                    [rehypeSanitize, SCHEMA],
                    trustedHeadings,
                ]}
                remarkRehypeOptions={{ footnoteLabel: "README footnotes" }}
            >
                {source}
            </ReactMarkdown>
        </div>
    );
}
