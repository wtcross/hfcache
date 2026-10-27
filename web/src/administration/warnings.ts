/** Guidance from operations.md/discovery.md; warnings never execute an action. */
export type AdministrationDestination =
    "configuration" | "maintenance" | "operations";
export interface WarningGuidance {
    readonly meaning: string;
    readonly response: string;
    readonly destination: AdministrationDestination | null;
    readonly actionLabel: string | null;
}
export const WARNING_GUIDANCE: Readonly<Record<string, WarningGuidance>> = {
    HFDEP001: {
        meaning: "Undeclared dependency detected in repository metadata",
        response:
            "Add it to declared dependencies, or configure the dependency as its own repository. Dependencies are never downloaded implicitly.",
        destination: "configuration",
        actionLabel: "Review configured dependencies",
    },
    HFWRN001: {
        meaning:
            "Temporary over-retention: retained revisions exceed the configured limit",
        response:
            "Preview recovery, then review a prune preview before applying any changes.",
        destination: "maintenance",
        actionLabel: "Review recovery and prune",
    },
    HFWRN002: {
        meaning: "Logical prune committed, trash removal outstanding",
        response:
            "The revision is already gone logically. Preview recovery to review the remaining physical cleanup.",
        destination: "maintenance",
        actionLabel: "Review recovery",
    },
    HFWRN003: {
        meaning: "Unknown files in an application-owned area",
        response:
            "These files are preserved, never deleted automatically. Identify them before removing anything by hand.",
        destination: null,
        actionLabel: null,
    },
    HFWRN004: {
        meaning: "Stale staging directory",
        response:
            "A run stopped part way and aged past the configured stale staging age. Preview recovery before changing it.",
        destination: "maintenance",
        actionLabel: "Review recovery",
    },
    HFWRN005: {
        meaning: "Free space approaching the configured reserve",
        response:
            "Review storage capacity. ZFS snapshots can retain blocks after an application prune; pruning does not guarantee reclaimed space.",
        destination: null,
        actionLabel: null,
    },
    HFWRN006: {
        meaning: "Upstream repository unreachable",
        response:
            "Every local revision is preserved. Upstream unavailability never triggers a prune.",
        destination: null,
        actionLabel: null,
    },
    HFWRN007: {
        meaning: "Archived repository is not in configuration",
        response:
            "Its revisions are kept. If removal is intentional, review a purge preview before applying any changes.",
        destination: "maintenance",
        actionLabel: "Review unmanaged repositories",
    },
    HFWRN008: {
        meaning: "Retired repair instance past its grace period",
        response:
            "Preview recovery to review quarantining the retired instance. Grace expiry alone does not delete it.",
        destination: "maintenance",
        actionLabel: "Review recovery",
    },
    HFWRN009: {
        meaning: "Local Xet transfer cache exceeded its advisory ceiling",
        response:
            "Check the writer-local cache at /var/cache/hfcache/xet. This is writer-local disk, separate from the archive.",
        destination: null,
        actionLabel: null,
    },
    HFWRN010: {
        meaning: "Verification may overlap storage maintenance",
        response:
            "Review verification and storage maintenance timing; reschedule one of the overlapping activities. Verification scheduling is read-only here.",
        destination: null,
        actionLabel: null,
    },
    HFWRN011: {
        meaning: "Supplemental metadata or README capture is incomplete",
        response:
            "Missing or failed supplemental fields remain unknown. This warning does not invalidate a valid archive publication or establish an integrity failure. Review the original result and, when appropriate, explicitly request metadata refresh in Operations; reading this warning never refreshes metadata.",
        destination: "operations",
        actionLabel: "Review metadata refresh",
    },
};
const UNKNOWN: WarningGuidance = Object.freeze({
    meaning: "Unrecognized warning",
    response:
        "Preserve the diagnostic code and review the original operation details and operator documentation. No action is inferred from this warning.",
    destination: "operations",
    actionLabel: "Review operation details",
});
export function warningGuidance(code: string): WarningGuidance {
    return Object.hasOwn(WARNING_GUIDANCE, code)
        ? (WARNING_GUIDANCE[code] ?? UNKNOWN)
        : UNKNOWN;
}
