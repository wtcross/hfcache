/** Private fixture preflight; no browser imports or filesystem writes. */
import { lstatSync, readFileSync } from "node:fs";
import {
    basename,
    dirname,
    isAbsolute,
    join,
    relative,
    resolve,
    sep,
} from "node:path";

export function requireOwnedProfile(
    workspace: string,
    webRoot: string,
    cache: string,
    tokenFile: string,
): void {
    const scratch = resolve(webRoot, "../.scratch");
    const owner = dirname(workspace);
    const child = relative(scratch, owner);
    if (
        !isAbsolute(workspace) ||
        resolve(workspace) !== workspace ||
        child === "" ||
        child.startsWith("..") ||
        isAbsolute(child) ||
        !["root", "prefixed"].includes(basename(workspace)) ||
        cache !== join(webRoot, ".cache/ms-playwright") ||
        tokenFile !== join(workspace, "reader.token")
    )
        throw new Error(
            "Only a generated repository read-fixture profile is allowed.",
        );
    const uid = process.getuid?.();
    if (uid === undefined)
        throw new Error(
            "Owned read-fixture checks require the local Unix host.",
        );
    let current = scratch;
    for (const part of ["", ...relative(scratch, workspace).split(sep)]) {
        if (part !== "") current = join(current, part);
        const facts = lstatSync(current);
        if (
            !facts.isDirectory() ||
            facts.isSymbolicLink() ||
            facts.uid !== uid ||
            (facts.mode & 0o022) !== 0
        )
            throw new Error(
                "Fixture ancestry is not an owned ordinary directory.",
            );
    }
    for (const path of [owner, workspace]) {
        if ((lstatSync(path).mode & 0o777) !== 0o700)
            throw new Error(
                "Fixture owner and profile must be private directories.",
            );
    }
    const marker = join(owner, "fixture.json"),
        facts = lstatSync(marker);
    if (
        !facts.isFile() ||
        facts.isSymbolicLink() ||
        facts.uid !== uid ||
        (facts.mode & 0o777) !== 0o600 ||
        facts.size > 1024
    )
        throw new Error("Fixture ownership marker is unsafe.");
    const value: unknown = JSON.parse(readFileSync(marker, "utf8"));
    if (
        value === null ||
        typeof value !== "object" ||
        !("purpose" in value) ||
        value.purpose !== "WEB-003-owned-read-fixture" ||
        !("id" in value) ||
        typeof value.id !== "string" ||
        !/^[a-f0-9]{32}$/u.test(value.id)
    )
        throw new Error(
            "Fixture ownership marker does not establish this purpose.",
        );
}
