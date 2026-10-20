# Independent browser wire fixtures

`goldens.json` is hand-authored from the existing public client/domain contracts.
It is not generated from `wire/contracts.json` or from the TypeScript decoder.
Its fictional version strings identify test data only; they never establish an
API feature or appear as connected archive facts.

The cases distinguish explicit null identities, false capabilities, zero counts,
a disabled configured repository, a known zero-byte complete variant and an exact
publication reference. Python original-model validation and TypeScript validation
must independently agree. Adversarial tests mutate these literals and preserve
raw numeric/Unicode token fixtures before parsing; regeneration must not rewrite
the expected fixtures to fit its output.
