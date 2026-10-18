# Historical plan: current technical authority

DOC-011 reviewed every section before moving the original plan. The historical
text remains evidence, never sole current technical authority. Original identity,
results and rationale are retained in git and the migration manifest.

| Historical section | Living authority and disposition |
| --- | --- |
| 1–5 | Architecture mission, context and decisions |
| 6 | Architecture layout/invariants/transactions; schemas; consumers; CLI initialization |
| 7 | Architecture framework; development; agent guides own process |
| 8 | Development quality gate and dependency rules; deployment Python/install |
| 9 | Configuration contract |
| 10 | Schemas contract |
| 11 | CLI contract |
| 12 | Security Hub adapter boundary; AD-08/09/15; configuration credentials |
| 13 | CLI sync; AD-19; architecture publication/run transactions |
| 14 | AD-11/18, FS-13–15; architecture copy mechanics; CLI doctor |
| 15 | AD-04/05/20; architecture prune; operations retention; storage capacity |
| 16 | CLI verify; schemas verification/report; recovery; operations verification triggers |
| 17 | AD-07; security T-01; schemas dependencies; configuration |
| 18 | Architecture recovery/quarantine; recovery runbook |
| 19 | CLI doctor; configuration storage; AD-19 |
| 20 | Storage requirements, TrueNAS settings and data protection |
| 21–23 | Deployment, server, containers and security hardening |
| 24 | CLI output/event vocabulary; operations logs; deployment journald/failure hook |
| 25 | Security contract |
| 26 | Development complete test tiers/failure matrix; executable failure-matrix tests |
| 27 | Storage capacity/performance checklist; operations measurements |
| 28–29, 33 | Historical implementation acceptance; current rollout in deployment and consumers |
| 30 | Deployment upgrade/rollback; schemas compatibility |
| 31 | Recovery runbook |
| 32 | Security/storage and technical ADR rationale |
| 34–35 | Historical site facts; effective writability in storage/architecture/CLI doctor |
| 36 | Historical agent protocol; current agent guides retain process/restrictions |
| 37 | Bibliography; no independent behavioral authority |
| Later amendments | API/server/security/container contracts; authorization history stays agent-only |

Substantive extractions: explicit Hub adapter arguments/completeness/typed
boundary; bounded hashing; copy temporary-file/rename/digest procedure and logical
allocation explanation; manifest-schema full-verification trigger; exact native
timer defaults; closed current logging vocabulary; TrueNAS dataset/export/
data-protection requirements; performance/capacity checklist; full offline/live/
NFS/installed-host/failure test matrix. Existing requirements take precedence over
obsolete historical public-only and five-revision defaults; current authenticated
scope and configured three-revision default are preserved. The two-dataset
alternative needs separate design approval consistent with FS-04.

Source/test comments now cite living contracts, including formerly unqualified
`plan §…` references. Mechanical path/link repairs retain historical factual prose.
Original hashes are validated against git, rather than claimed to equal the
reference-repaired or substantively amended destination bytes.
