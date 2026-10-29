/** Renderer/component boundary fixtures; actual capture/API/network acceptance is recorded separately. */
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { ReadmeCard } from "../src/readme/ReadmeCard";
import { readmeAdmission, readmeIdPrefix } from "../src/readme/policy";
import type { ExactPublication } from "../src/api/identity";
import type { RepositoryCardRead } from "../src/wire/generated";

const nativeCrypto: unknown = await vi.importActual("node:crypto");
function digest(source: string): string {
    if (
        typeof nativeCrypto !== "object" ||
        nativeCrypto === null ||
        !("createHash" in nativeCrypto) ||
        typeof nativeCrypto.createHash !== "function"
    )
        throw new Error("Native fixture hash unavailable");
    const hash: unknown = Reflect.apply(nativeCrypto.createHash, nativeCrypto, [
        "sha256",
    ]);
    if (
        typeof hash !== "object" ||
        hash === null ||
        !("update" in hash) ||
        typeof hash.update !== "function" ||
        !("digest" in hash) ||
        typeof hash.digest !== "function"
    )
        throw new Error("Native fixture hash unavailable");
    Reflect.apply(hash.update, hash, [source]);
    const value: unknown = Reflect.apply(hash.digest, hash, ["hex"]);
    if (typeof value !== "string" || !/^[a-f0-9]{64}$/u.test(value))
        throw new Error("Native fixture hash unavailable");
    return value;
}

const identity: ExactPublication = {
    repositoryType: "model",
    repositoryId: "owner/model",
    commitSha: "a".repeat(40),
    publicationId: "b".repeat(32),
};
function card(
    markdown: string | null,
    state: RepositoryCardRead["state"] = "present",
    selected = identity,
): RepositoryCardRead {
    return {
        schema_version: 1,
        kind: "repository_card",
        archive_id: "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90",
        repository_type: selected.repositoryType,
        repository_id: selected.repositoryId,
        commit_sha: selected.commitSha,
        publication_id: selected.publicationId,
        publication_generation: 1,
        manifest_path: `published/manifests/${selected.repositoryType}s/${selected.repositoryId}/${selected.commitSha}/${selected.publicationId}.json`,
        manifest_digest: "c".repeat(64),
        source_path: state === "absent" ? null : "README.md",
        expected_source_sha256: state === "absent" ? null : "d".repeat(64),
        captured_at:
            state === "not_captured" ? null : "2026-10-26T12:00:00.000000Z",
        presentation_version: state === "not_captured" ? null : "markdown-1",
        state,
        markdown,
        presentation_sha256: markdown === null ? null : digest(markdown),
        diagnostics: [],
    };
}
function mount(source: string, selected = identity) {
    const evidence = card(source, "present", selected);
    return {
        evidence,
        ...render(
            <>
                <ReadmeCard
                    card={evidence}
                    identity={selected}
                    publicationGeneration={1}
                />
                <button type="button">Observe original operation</button>
            </>,
        ),
    };
}
async function body() {
    const region = screen.getByRole("region", { name: "Archived README" });
    await within(region).findByRole("button", { name: "Sanitized source" });
    return region;
}
afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
});

test("renders useful inert formatting and deterministic publication-prefixed headings without stripping leading horizontal rules", async () => {
    mount(
        "---\n\n# Overview\n\nA **strong**, *emphasized* and ~~old~~ claim.\n\n> A quote\n\n- One\n- Two\n\n```text\n<script>inert example</script>\n```\n",
    );
    const region = await body();
    const heading = await within(region).findByRole(
        "heading",
        {
            name: "Overview",
            level: 1,
        },
        { timeout: 5000 },
    );
    expect(heading.id).toBe(readmeIdPrefix(identity) + "1");
    expect(region.querySelector("hr")).not.toBeNull();
    expect(region.querySelector("strong")?.textContent).toBe("present");
    expect(region.querySelector(".readme-markdown strong")?.textContent).toBe(
        "strong",
    );
    expect(region.querySelector("blockquote")?.textContent).toContain(
        "A quote",
    );
    expect(region.querySelector("pre code")?.textContent).toContain(
        "<script>inert example</script>",
    );
    expect(region.querySelector("script")).toBeNull();
    expect(region).toHaveTextContent("derivative content");
    expect(region).toHaveTextContent("Expected README source SHA256");
    expect(region).toHaveTextContent("Sanitized presentation SHA256");
});

test.each(["model", "dataset"] as const)(
    "%s relative, fragment and HTTP links navigate only with closed external attributes",
    async (repositoryType) => {
        mount(
            "# Links\n\n[relative](docs/guide.md) [root](/LICENSE) [fragment](#part) [external](https://example.test/reference)\n",
            { ...identity, repositoryType },
        );
        const region = await body();
        const relative = await within(region).findByRole("link", {
            name: "relative",
        });
        const upstream = `https://huggingface.co/${repositoryType === "dataset" ? "datasets/" : ""}owner/model/blob/${identity.commitSha}/`;
        expect(relative).toHaveAttribute("href", upstream + "docs/guide.md");
        expect(
            within(region).getByRole("link", { name: "root" }),
        ).toHaveAttribute("href", upstream + "LICENSE");
        expect(
            within(region).getByRole("link", { name: "fragment" }),
        ).toHaveAttribute("href", upstream + "README.md#part");
        for (const anchor of region.querySelectorAll("a")) {
            expect(anchor).toHaveAttribute("target", "_blank");
            expect(anchor).toHaveAttribute("rel", "noopener noreferrer");
            expect(anchor).toHaveAttribute("referrerpolicy", "no-referrer");
            expect(new URL(anchor.href).origin).not.toBe(
                window.location.origin,
            );
        }
    },
);

test("HTML, MDX, SVG, forms and attribute injections cannot construct active elements or navigation IDs", async () => {
    const fetcher = vi.spyOn(globalThis, "fetch");
    mount(
        '<script>globalThis.readmeAttack=true</script>\n\n<svg onload="alert(1)"><foreignObject><form action="/api/v1/syncs"><input name="password"></form></foreignObject></svg>\n\n<iframe src="https://evil.test/frame"></iframe>\n\n# Safe\n\n<Component secret={1}/>\n\n[Label](https://example.test/ "onmouseover=alert(1)")\n',
    );
    const region = await body();
    await within(region).findByRole("heading", { name: "Safe" });
    expect(
        region.querySelector(
            "script,style,svg,form,input,button[form],iframe,object,embed,math,video,audio,img",
        ),
    ).toBeNull();
    for (const element of region.querySelectorAll(".readme-markdown *"))
        for (const attribute of element.attributes)
            expect(attribute.name).not.toMatch(
                /^on|^style$|^name$|^src|^data-/u,
            );
    expect(fetcher).not.toHaveBeenCalled();
    expect(region.querySelector("#root,#main-content,#operations")).toBeNull();
});

test("absolute management API and UI links are withheld while external navigation remains explicit", async () => {
    const fetcher = vi.spyOn(globalThis, "fetch");
    const before = window.location.href;
    mount(
        `# Origin\n\n[api](${document.location.origin}/api/v1/status) [ui](${document.location.origin}/ui/operations) [external](https://example.test/reference)\n`,
    );
    const region = await body();
    await within(region).findByRole("heading", { name: "Origin" });
    expect(
        within(region).queryByRole("link", { name: "api" }),
    ).not.toBeInTheDocument();
    expect(
        within(region).queryByRole("link", { name: "ui" }),
    ).not.toBeInTheDocument();
    await userEvent.click(within(region).getByText("api (link unavailable)"));
    expect(
        within(region).getByRole("link", { name: "external" }),
    ).toHaveAttribute("href", "https://example.test/reference");
    expect(fetcher).not.toHaveBeenCalled();
    expect(window.location.href).toBe(before);
});

test("media are placeholders and GFM task checkboxes are inert content", async () => {
    mount(
        "# Items\n\n![private alt](https://evil.test/pixel.png)\n\n- [x] Completed claim\n- [ ] Pending claim\n",
    );
    const region = await body();
    await within(region).findByRole("heading", { name: "Items" });
    expect(region).toHaveTextContent("[Image omitted]");
    expect(region).toHaveTextContent("[Task checkbox omitted]");
    expect(
        region.querySelector("img,input,video,audio,source,picture"),
    ).toBeNull();
    expect(within(region).queryByRole("checkbox")).not.toBeInTheDocument();
});

test("generated footnotes never bind the management fragment or accept source-controlled identifiers", async () => {
    const original = window.location.hash;
    mount(
        "# Footnotes\n\nA claim[^operations].\n\n[^operations]: An inert note.\n",
    );
    const region = await body();
    await within(region).findByRole("heading", { name: "Footnotes", level: 1 });
    for (const anchor of region.querySelectorAll("a")) {
        expect(anchor.href).toMatch(
            /^https:\/\/huggingface.co\/owner\/model\/blob\//u,
        );
        expect(anchor.getAttribute("href")).not.toMatch(/^#/u);
    }
    for (const element of region.querySelectorAll(".readme-markdown [id]"))
        expect(element.id.startsWith(readmeIdPrefix(identity))).toBe(true);
    expect(window.location.hash).toBe(original);
    expect(region.querySelector('[id="operations"],[name]')).toBeNull();
});

test.each([
    "javascript:alert(1)",
    "JaVaScRiPt:alert(1)",
    "data:text/html,evil",
    "blob:https://example.test/id",
    "//evil.test/x",
    "javascript%3Aalert(1)",
    "jav&#x61;script:alert(1)",
])(
    "unsafe target %s cannot become an application or executable link",
    async (destination) => {
        mount(`# Safe link\n\n[bad](${destination})\n`);
        const region = await body();
        await within(region).findByRole("heading", { name: "Safe link" });
        expect(
            within(region).queryByRole("link", { name: "bad" }),
        ).not.toBeInTheDocument();
        expect(region.querySelector("img,iframe,form,script")).toBeNull();
    },
);

test("sanitized source is exact escaped presentation text, including leading separators and omitted-image escaping", async () => {
    const source =
        "---\n\n# Source\n\n\\[image omitted\\]\n\n`<svg onload=evil>` & exact whitespace  \n";
    mount(source);
    const region = await body();
    await userEvent.click(
        within(region).getByRole("button", { name: "Sanitized source" }),
    );
    const sourceGroup = within(region).getByRole("group", {
        name: "Sanitized README source",
    });
    expect(sourceGroup.textContent).toBe(source);
    sourceGroup.focus();
    expect(sourceGroup).toHaveFocus();
    expect(region.querySelector("svg,img,script")).toBeNull();
    expect(
        within(region).getByRole("button", { name: "Sanitized source" }),
    ).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(
        within(region).getByRole("button", { name: "Rendered README" }),
    );
    await within(region).findByRole("heading", { name: "Source" });
});

test.each([
    "absent",
    "unsupported",
    "oversize",
    "unsafe",
    "failed",
    "not_captured",
] as const)(
    "capture state %s remains explicit with no fictional source or parser action",
    (state) => {
        render(
            <ReadmeCard
                card={card(null, state)}
                identity={identity}
                publicationGeneration={1}
            />,
        );
        const region = screen.getByRole("region", { name: "Archived README" });
        expect(region).toHaveTextContent("Capture state: " + state);
        expect(
            within(region).queryByRole("button", { name: "Sanitized source" }),
        ).not.toBeInTheDocument();
        expect(region).toHaveTextContent("source is unavailable");
        expect(region.querySelector(".readme-markdown")).toBeNull();
    },
);

test("format admission refuses a large valid presentation without truncating sanitized source or blocking recovery", async () => {
    const source = "x".repeat(65537);
    mount(source);
    const region = await body();
    expect(await within(region).findByRole("alert")).toHaveTextContent(
        "Formatting was refused",
    );
    await userEvent.click(
        within(region).getByRole("button", { name: "Sanitized source" }),
    );
    expect(
        within(region).getByLabelText("Sanitized README source").textContent,
    ).toBe(source);
    expect(
        screen.getByRole("button", { name: "Observe original operation" }),
    ).toBeEnabled();
});

test("post-parse node exhaustion stays within the local boundary and sanitized source controls still work", async () => {
    const source = ("a *b* ".repeat(100) + "\n\n").repeat(15);
    expect(readmeAdmission(source)).toEqual({ allowed: true });
    vi.spyOn(console, "error").mockImplementation(() => {});
    mount(source);
    const region = await body();
    expect(await within(region).findByRole("alert")).toHaveTextContent(
        "formatting is unavailable",
    );
    await userEvent.click(
        within(region).getByRole("button", { name: "Sanitized source" }),
    );
    expect(
        within(region).getByLabelText("Sanitized README source").textContent,
    ).toBe(source);
    expect(
        screen.getByRole("button", { name: "Observe original operation" }),
    ).toBeEnabled();
});

test("post-parse deep inline structure is refused without disabling the source control", async () => {
    let source = "leaf";
    for (let index = 0; index < 30; index++) {
        const marker = index % 2 === 0 ? "**" : "_";
        source = marker + "layer " + source + marker;
    }
    expect(readmeAdmission(source)).toEqual({ allowed: true });
    vi.spyOn(console, "error").mockImplementation(() => {});
    mount(source);
    const region = await body();
    expect(await within(region).findByRole("alert")).toHaveTextContent(
        "formatting is unavailable",
    );
    await userEvent.click(
        within(region).getByRole("button", { name: "Sanitized source" }),
    );
    expect(
        within(region).getByLabelText("Sanitized README source").textContent,
    ).toBe(source);
});

function adjacentIndentedFences(): string {
    const chunk =
        "    ```\n" +
        ("    " + "x".repeat(2000) + "\n").repeat(8) +
        "    ```\n";
    return chunk + chunk;
}

test("adjacent indented fence-looking chunks cannot reset the code-block limit or hide sanitized source", async () => {
    const source = adjacentIndentedFences();
    expect(readmeAdmission(source)).toEqual({
        allowed: false,
        reason: "code_block",
    });
    mount(source);
    const region = await body();
    expect(await within(region).findByRole("alert")).toHaveTextContent(
        "Formatting was refused",
    );
    await userEvent.click(
        within(region).getByRole("button", { name: "Sanitized source" }),
    );
    expect(
        within(region).getByLabelText("Sanitized README source").textContent,
    ).toBe(source);
    expect(
        screen.getByRole("button", { name: "Observe original operation" }),
    ).toBeEnabled();
});

test("the actual parsed code node independently enforces the byte bound if lexical admission misses it", async () => {
    const source = adjacentIndentedFences();
    // Bypass only pre-admission to exercise the independent real parser limit.
    vi.spyOn(
        await import("../src/readme/policy"),
        "readmeAdmission",
    ).mockReturnValue({ allowed: true });
    vi.spyOn(console, "error").mockImplementation(() => {});
    mount(source);
    const region = await body();
    expect(await within(region).findByRole("alert")).toHaveTextContent(
        "formatting is unavailable",
    );
    await userEvent.click(
        within(region).getByRole("button", { name: "Sanitized source" }),
    );
    expect(
        within(region).getByLabelText("Sanitized README source").textContent,
    ).toBe(source);
});

test("a code block at the exact UTF-8 boundary renders without truncation", async () => {
    const code = ("x".repeat(4095) + "\n").repeat(4);
    expect(new TextEncoder().encode(code)).toHaveLength(16 * 1024);
    const source = "```text\n" + code + "```\n";
    expect(readmeAdmission(source)).toEqual({ allowed: true });
    mount(source);
    const region = await body();
    const rendered = await within(region).findByText(
        (_, element) => element?.matches(".readme-markdown pre code") === true,
    );
    expect(rendered.textContent).toBe(code);
    expect(within(region).queryByRole("alert")).not.toBeInTheDocument();
});

test("table formatting stays bounded and available with accessible overflow", async () => {
    mount("# Table\n\n| A | B |\n| - | - |\n| 1 | 2 |\n");
    const region = await body();
    await within(region).findByRole("table");
    expect(
        within(region).getByRole("region", {
            name: "README table, scroll horizontally",
        }),
    ).toHaveAttribute("tabindex", "0");
    expect(region.querySelector("table")?.textContent).toContain("12");
});

test("every supported heading uses its trusted ordinal rather than source text or attributes", async () => {
    mount(
        "# One\n\n## Two\n\n### Three\n\n#### Four\n\n##### Five\n\n###### Six\n",
    );
    const region = await body();
    await within(region).findByRole("heading", { name: "Six", level: 6 });
    for (const [index, heading] of [
        ...region.querySelectorAll(
            ".readme-markdown h1,.readme-markdown h2,.readme-markdown h3,.readme-markdown h4,.readme-markdown h5,.readme-markdown h6",
        ),
    ].entries())
        expect(heading.id).toBe(readmeIdPrefix(identity) + String(index + 1));
});

test("a presentation exactly at the JSON string byte boundary stays available as untruncated escaped source", async () => {
    const source = "x".repeat(1024 * 1024 - 2);
    mount(source);
    const region = await body();
    expect(await within(region).findByRole("alert")).toHaveTextContent(
        "Formatting was refused",
    );
    await userEvent.click(
        within(region).getByRole("button", { name: "Sanitized source" }),
    );
    expect(
        within(region).getByLabelText("Sanitized README source").textContent,
    ).toBe(source);
});

test("identity, generation, unknown versions/states and over-boundary source refuse the entire card body", () => {
    for (const [field, value] of [
        ["publication_id", "e".repeat(32)],
        ["publication_generation", 2],
        ["schema_version", 2],
        ["state", "future"],
        ["presentation_version", "markdown-2"],
        ["markdown", "x".repeat(1024 * 1024 + 1)],
        ["markdown", "\ud800"],
        ["markdown", "\n".repeat(1024 * 512)],
    ] as const) {
        const evidence = card("# Hidden");
        Object.defineProperty(evidence, field, { value });
        const result = render(
            <ReadmeCard
                card={evidence}
                identity={identity}
                publicationGeneration={1}
            />,
        );
        expect(screen.getByRole("alert")).toHaveTextContent("No body is shown");
        expect(
            screen.queryByRole("button", { name: "Sanitized source" }),
        ).not.toBeInTheDocument();
        result.unmount();
    }
});

test("selection changes reset local presentation state and never retain another publication's source", async () => {
    const first = card("# First");
    const view = render(
        <ReadmeCard
            card={first}
            identity={identity}
            publicationGeneration={1}
        />,
    );
    const region = await body();
    await userEvent.click(
        within(region).getByRole("button", { name: "Sanitized source" }),
    );
    const nextIdentity = { ...identity, publicationId: "e".repeat(32) };
    view.rerender(
        <ReadmeCard
            card={card("# Second", "present", nextIdentity)}
            identity={nextIdentity}
            publicationGeneration={1}
        />,
    );
    await screen.findByRole("heading", { name: "Second", level: 1 });
    expect(
        screen.queryByLabelText("Sanitized README source"),
    ).not.toBeInTheDocument();
    expect(
        screen.queryByRole("heading", { name: "First" }),
    ).not.toBeInTheDocument();
});
