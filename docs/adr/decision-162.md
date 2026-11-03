# Bind a preserved rootless service-account home to the protected index

- Decision identity: 162.
- Status: Accepted for source implementation; installed proof remains pending.
- Date: 2026-11-01.
- Introducing change: this commit.

## Context and decision

The actual preserved writer deployment's `hfcache` account is UID/GID981 with
home `/var/lib/hfcache/container-home`. Its running rootless store belongs under
that home. The new helper instead fixes `/var/lib/hfcache`, refusing the real
account; merely changing HOME could select an unrelated engine store. A failed
diagnostic's independently retained default-home store supplies no migration or
cleanup authority. Source fixtures accepted under the old home do not prove the
production home works.

Permit only `/var/lib/hfcache` and `/var/lib/hfcache/container-home` for rootless
helper observation. The independent protected deployment index optionally binds
the exact string as `profile_evidence.account_home`. Omission retains the first
value; native remains fixed to the first value and rejects the extra field.
The read-only preparer obtains the value from the measured fixed passwd account,
checks its UID/GID against the selected immutable runtime, and emits the extra
field only for the alternate home. Recapture the account before returning.

Every helper/launcher consumer checks the closed value and measured passwd
UID/GID/home against the protected principal and indexed runtime. Pin the home in
the internal engine preparation, compare it across original observer/child/final
revalidation, and derive the clean HOME, two user override paths and two image/
layer lock paths solely from it. Never run Podman under an unselected home or
search another store after a refusal. Preserve the exact existing lock/SHM
metadata, SELinux types, namespace/peer/process proofs, finite budgets and narrow
engine capability state from decisions150/151/159.

The helper unit masks both fixed possible secret-store paths and lists only the
two exact optional engine coordination roots as writable. Independently label
existing selected secret/lock objects under the unchanged fifteen-role receipt;
this adds no helper payload rights, broad HOME bind, permission/category grant,
new module or runtime dependency. Do not move the account or store, mutate an
unselected store, release the NAS guard or change schedules to pass acceptance.

## Rationale and alternatives

Changing passwd/home or moving the existing Podman store risks real persistent
state and is unnecessary. Reading arbitrary homes or trusting ambient HOME would
widen path authority. Deriving a finite choice from passwd alone would fail to
pin it across requests. A protected finite index choice preserves the real store
while binding its identity independently of the online application and mutable
process environment. Existing immutable runtime/container-release schema1 and
UID/GID/image bindings remain unchanged.

## Compatibility and required evidence

This is an additive protected host-index field, not an archive, operation,
application-outcome or SELinux-receipt format change. Previous strict helpers
refuse the extended rootless index. Preserve predecessor bootstrap/index/policy
receipts for rollback and require an account/home compatible with that exact
target; removing the field cannot make an alternate account satisfy an older
fixed-home helper. Never auto-rewrite an index or account to force startup.

Require meaningful closed-enum, mismatch/drift, no-fallback, both-home owned
override/lock and exact launcher/bootstrap tests; keep existing mode/context,
namespace/capability and native tests. Run the full strict web/build gate after
implementation. Actual confined installed preparation, separate rootless engine
read, helper/API/browser configuration and expected-denial acceptance remain
required under the preserved read-only NAS barrier. Source tests alone prove
none of those installed outcomes.

Amends decisions150/151/159 only for closed home binding; no capability, label
policy, archive authority or native execution rule is relaxed.

## Original-intent and writer amendment (2026-11-03)

Accepted design in [decision 165](decision-165.md); implementation and installed conformance remain
pending. Closed rootless account-home selection and existing mapped identities remain unchanged. The independent writer archive-mode binding is additional protected authority, not a new home, engine selector or permission to migrate an account/store.
See the [executable recovery contract](../job-recovery.md). Original rationale
and unrelated requirements above remain in force.
