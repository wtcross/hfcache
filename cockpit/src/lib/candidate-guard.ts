/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Exact candidate/base bytes stay under one privileged config lock (ADR122).
 * Browser content is bounded stdin data; only the CLI adapter supplies argv.
 */

export interface CandidateGuard {
    candidateContent: string;
    installedContent: string;
}

export interface ConfigurationPaths {
    installed: string;
    candidate: string;
    backup: string;
    lock: string;
}

export const CONFIGURATION_PATHS: Readonly<ConfigurationPaths> = Object.freeze({
    installed: '/etc/hfcache/config.toml',
    candidate: '/etc/hfcache/.candidate.toml',
    backup: '/etc/hfcache/config.toml.bak',
    lock: '/etc/hfcache/.configuration.lock',
});

/* Only hermetic tests supply this override. Product callers use fixed paths and
 * root:hfcache; none of these settings is accepted from a page/config request. */
export interface ConfigurationFixture {
    paths: ConfigurationPaths;
    ownerUid: number;
    group: string;
}

export interface GuardedInvocation {
    argv: string[];
    input: string;
}

export const MAX_CANDIDATE_BYTES = 1024 * 1024;

export function validateCandidateText(value: string, allowEmpty = false): void {
    if (typeof value !== 'string' || (!allowEmpty && value === '') || value.includes('\0'))
        throw new Error('Configuration must be bounded UTF-8 text without NUL');
    for (let index = 0; index < value.length; index += 1) {
        const character = value.charCodeAt(index);
        if (character >= 0xd800 && character <= 0xdbff) {
            const next = value.charCodeAt(index + 1);
            if (!(next >= 0xdc00 && next <= 0xdfff))
                throw new Error('Configuration must contain complete Unicode characters');
            index += 1;
        } else if (character >= 0xdc00 && character <= 0xdfff) {
            throw new Error('Configuration must contain complete Unicode characters');
        }
    }
    if (new TextEncoder().encode(value).length > MAX_CANDIDATE_BYTES)
        throw new Error('Configuration text is limited to 1 MiB');
}

/* All participating page calls use this cooperative root-only lock. External
 * sysadmin edits remain the trusted boundary. Never unlink the lock inode. */
const SCRIPT = `
set -euo pipefail
umask 077
export LC_ALL=C
action=$1 installed=$2 candidate=$3 backup=$4 lock=$5 owner=$6 group=$7
shift 7
directory=\${installed%/*}
fail() { printf 'Configuration changed or is unsafe; reload and validate again\\n' >&2; exit 1; }
[[ -d "$directory" && ! -L "$directory" ]] || fail
[[ $(stat -c '%u' -- "$directory") == "$owner" ]] || fail
mode=$(stat -c '%a' -- "$directory")
(( (8#$mode & 0022) == 0 )) || fail
regular() {
    [[ -f "$1" && ! -L "$1" ]] || fail
    [[ $(stat -c '%u:%G:%a:%h' -- "$1") == "$owner:$group:640:1" ]] || fail
}
if [[ ! -e "$lock" && ! -L "$lock" ]]; then
    (set -o noclobber; : > "$lock") || fail
fi
[[ -f "$lock" && ! -L "$lock" ]] || fail
[[ $(stat -c '%u:%a:%h' -- "$lock") == "$owner:600:1" ]] || fail
before=$(stat -c '%d:%i' -- "$lock")
exec 9>>"$lock"
flock --exclusive 9
[[ $(stat -Lc '%d:%i' -- /proc/self/fd/9) == "$before" ]] || fail
[[ $(stat -c '%d:%i' -- "$lock") == "$before" ]] || fail
if [[ "$action" == read ]]; then
    regular "$installed"
    size=$(stat -c '%s' -- "$installed")
    (( size <= 1048576 )) || fail
    dd if="$installed" iflag=nofollow,count_bytes count=1048576 status=none
    exit
fi
expected_candidate= expected_base= predecessor=
cleanup() {
    [[ -z "$expected_candidate" ]] || rm -f -- "$expected_candidate"
    [[ -z "$expected_base" ]] || rm -f -- "$expected_base"
    [[ -z "$predecessor" ]] || rm -f -- "$predecessor"
    return 0
}
trap cleanup EXIT
IFS= read -r -d '' -n 1048577 proposed || fail
(( \${#proposed} > 0 && \${#proposed} <= 1048576 )) || fail
IFS= read -r -d '' -n 1048577 original || fail
(( \${#original} <= 1048576 )) || fail
if IFS= read -r -d '' -n 1 extra; then fail; fi
expected_candidate=$(mktemp "$directory/.candidate-input.XXXXXX")
expected_base=$(mktemp "$directory/.installed-input.XXXXXX")
printf '%s' "$proposed" > "$expected_candidate"
printf '%s' "$original" > "$expected_base"
regular "$installed"
cmp -s -- "$installed" "$expected_base" || fail
case "$action" in
write)
    if [[ -e "$candidate" || -L "$candidate" ]]; then regular "$candidate"; fi
    chown "$owner:$group" "$expected_candidate"
    chmod 0640 "$expected_candidate"
    sync "$expected_candidate"
    mv -T -- "$expected_candidate" "$candidate"
    expected_candidate=
    sync "$directory"
    ;;
guard|install|remove)
    regular "$candidate"
    cmp -s -- "$candidate" "$expected_candidate" || fail
    case "$action" in
    guard) "$@" ;;
    install)
        if [[ -e "$backup" || -L "$backup" ]]; then regular "$backup"; fi
        predecessor=$(mktemp "$directory/.predecessor.XXXXXX")
        cp -p -- "$installed" "$predecessor"
        sync "$predecessor"
        mv -T -- "$predecessor" "$backup"
        predecessor=
        sync "$directory"
        sync "$candidate"
        mv -T -- "$candidate" "$installed"
        sync "$directory"
        ;;
    remove) rm -- "$candidate"; sync "$directory" ;;
    esac
    ;;
*) fail ;;
esac
`;

function invocation(
    action: 'read' | 'write' | 'guard' | 'install' | 'remove',
    guard: CandidateGuard | null,
    argv: string[],
    fixture?: ConfigurationFixture,
): GuardedInvocation {
    if (guard !== null) {
        validateCandidateText(guard.candidateContent);
        validateCandidateText(guard.installedContent, true);
    }
    const paths = fixture?.paths ?? CONFIGURATION_PATHS;
    const owner = fixture?.ownerUid ?? 0;
    const group = fixture?.group ?? 'hfcache';
    if (!Number.isSafeInteger(owner) || owner < 0 || !/^[A-Za-z0-9_.-]+$/.test(group))
        throw new Error('Invalid configuration owner');
    const directory = paths.installed.slice(0, paths.installed.lastIndexOf('/'));
    for (const path of Object.values(paths)) {
        if (!path.startsWith('/') || path.includes('\0') || path.split('/').includes('..') ||
            path.slice(0, path.lastIndexOf('/')) !== directory)
            throw new Error('Configuration files must share one trusted directory');
    }
    return {
        argv: ['bash', '-ec', SCRIPT, 'hfcache-configuration', action, paths.installed,
            paths.candidate, paths.backup, paths.lock, String(owner), group, ...argv],
        input: guard === null ? '' : guard.candidateContent + '\0' + guard.installedContent + '\0',
    };
}

export function readInstalledInvocation(fixture?: ConfigurationFixture): GuardedInvocation {
    return invocation('read', null, [], fixture);
}

export function guardCandidateInvocation(
    argv: string[], guard: CandidateGuard, fixture?: ConfigurationFixture,
): GuardedInvocation {
    if (argv[0] !== 'systemd-run')
        throw new Error('Candidate validation requires the installed CLI adapter');
    return invocation('guard', guard, argv, fixture);
}

export function candidateMutationInvocation(
    action: 'write' | 'install' | 'remove', guard: CandidateGuard,
    fixture?: ConfigurationFixture,
): GuardedInvocation {
    return invocation(action, guard, [], fixture);
}
