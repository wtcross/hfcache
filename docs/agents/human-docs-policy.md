# Human-document boundary

Human documentation is every documentation file outside `docs/agents/`, except
the explicit agent entrypoints `AGENTS.md` and its `CLAUDE.md` symlink.
Public CLI help is also human-facing. Write current behavior, examples,
prerequisites, supported profiles, security boundaries and compatibility limits.
Never introduce work-package IDs, task/implementation-plan/progress links,
agent workflow instructions, phase chronology or task-owned availability claims.
Technical error codes, architectural/storage invariant IDs, operation states,
schema versions and domain planning commands remain valid product concepts.

Keep execution authorization, active selection, work-package evidence, process
ADRs and historical transcripts here. Agents may cite human contracts; human
guides must not depend on implementation tracking for technical authority.

DOC-011 inventories the exact pre-existing tracking matches in
`documentation-inventory.json`. Each row names a file, matched token and maximum
count; no file-wide exemption is allowed. This is a shrinking transitional
baseline, not a permanent policy exception. Subsequent packages remove matches
within their scope. DOC-019 requires zero remaining matches and no exemptions.
The inventory also records every original tracked document, executable/example
surface and historical-authority citation. The migration manifest records old
paths and original SHA-256 hashes at the reviewed git baseline. Mechanical
reference repairs are distinct from the substantive extractions listed in the
coverage map and task evidence.
