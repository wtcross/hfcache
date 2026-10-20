/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Exact candidate/base bytes stay under one privileged config lock (ADR122).
 * Browser content is bounded stdin data; only the CLI adapter supplies argv.
 */

export interface CandidateGuard {
    candidateContent: string;
    installedContent: string;
}

export type GuardedFileState = 'matching' | 'absent' | 'changed' | 'unknown';

export interface CandidateInspection {
    candidate: GuardedFileState;
    installedBase: GuardedFileState;
    installedCandidate: GuardedFileState;
    backupBase: GuardedFileState;
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
fail() {
    if [[ "$action" == inspect ]]; then
        printf '{"candidate":"unknown","installedBase":"unknown","installedCandidate":"unknown","backupBase":"unknown"}\\n'
        exit 0
    fi
    printf 'Configuration changed or is unsafe; reload and validate again\\n' >&2
    exit 1
}
if [[ "$action" == inspect ]]; then exec 2>/dev/null; fi
utf8_text() {
    local valid=$'^([\\x01-\\x7f]|[\\xc2-\\xdf][\\x80-\\xbf]|\\xe0[\\xa0-\\xbf][\\x80-\\xbf]|[\\xe1-\\xec][\\x80-\\xbf][\\x80-\\xbf]|\\xed[\\x80-\\x9f][\\x80-\\xbf]|[\\xee-\\xef][\\x80-\\xbf][\\x80-\\xbf]|\\xf0[\\x90-\\xbf][\\x80-\\xbf][\\x80-\\xbf]|[\\xf1-\\xf3][\\x80-\\xbf][\\x80-\\xbf][\\x80-\\xbf]|\\xf4[\\x80-\\x8f][\\x80-\\xbf][\\x80-\\xbf])*$'
    [[ "$1" =~ $valid ]]
}
if [[ "$action" != read ]]; then
    # Cockpit's text channel cannot transport NUL. Decode two canonical bounded
    # ASCII lines entirely in memory before even inspecting/creating the lock.
    # A bounded reader adds its success sentinel. Reading through a pipe without
    # -n permits buffered I/O; check EOF separately to reject embedded wire NUL.
    {
        IFS= read -r -d '' wire || fail
        if IFS= read -r -d '' -n 1 extra; then fail; fi
        [[ -z "$extra" ]] || fail
    } < <(head --bytes=2796211 && printf '\\0')
    wait "$!" || fail
    (( \${#wire} <= 2796210 )) || fail
    # Line reads avoid quadratic glob matching on a maximum-size frame.
    {
        IFS= read -r encoded_proposed || fail
        IFS= read -r encoded_original || fail
        if IFS= read -r -n 1 extra; then fail; fi
        [[ -z "$extra" ]] || fail
    } < <(printf '%s' "$wire")
    wait "$!" || fail
    decode_frame() {
        local encoded=$2 decoded canonical
        (( \${#encoded} <= 1398104 )) || fail
        # The bounded encoded line can decode to at most 1 MiB plus two bytes.
        IFS= read -r -d '' decoded < <(
            printf '%s' "$encoded" | base64 --decode && printf '\\0'
        ) || fail
        wait "$!" || fail
        (( \${#decoded} <= 1048576 )) || fail
        # This also rejects invalid padding, decoded NUL and truncated decodes,
        # while preserving every trailing newline in the original UTF-8 bytes.
        canonical=$(printf '%s' "$decoded" | base64 --wrap=0) || fail
        [[ "$canonical" == "$encoded" ]] || fail
        utf8_text "$decoded" || fail
        printf -v "$1" '%s' "$decoded"
    }
    decode_frame proposed "$encoded_proposed"
    [[ -n "$proposed" ]] || fail
    decode_frame original "$encoded_original"
    unset wire encoded_proposed encoded_original
fi
[[ -d "$directory" && ! -L "$directory" ]] || fail
[[ $(stat -c '%u' -- "$directory") == "$owner" ]] || fail
mode=$(stat -c '%a' -- "$directory")
(( (8#$mode & 0022) == 0 )) || fail
regular() {
    [[ -f "$1" && ! -L "$1" ]] || fail
    [[ $(stat -c '%u:%G:%a:%h' -- "$1") == "$owner:$group:640:1" ]] || fail
}
if [[ ! -e "$lock" && ! -L "$lock" ]]; then
    [[ "$action" != inspect ]] || fail
    (set -o noclobber; : > "$lock") || fail
fi
[[ -f "$lock" && ! -L "$lock" ]] || fail
[[ $(stat -c '%u:%a:%h' -- "$lock") == "$owner:600:1" ]] || fail
before=$(stat -c '%d:%i' -- "$lock")
if [[ "$action" == inspect ]]; then
    exec 9<"$lock"
    flock --exclusive --timeout 5 9 || fail
else
    exec 9>>"$lock"
    flock --exclusive 9
fi
[[ $(stat -Lc '%d:%i' -- /proc/self/fd/9) == "$before" ]] || fail
[[ $(stat -c '%d:%i' -- "$lock") == "$before" ]] || fail
if [[ "$action" == read ]]; then
    regular "$installed"
    size=$(stat -c '%s' -- "$installed")
    (( size <= 1048576 )) || fail
    dd if="$installed" iflag=nofollow,count_bytes count=1048576 status=none
    exit
fi
if [[ "$action" == inspect ]]; then
    # This branch creates no lock, comparison files, backup or other artifacts.
    [[ -r "$directory" && -x "$directory" ]] || fail
    inspect_file() {
        file_state=unknown observed=
        if [[ ! -e "$1" && ! -L "$1" ]]; then file_state=absent; return; fi
        [[ -f "$1" && ! -L "$1" ]] || return 0
        [[ $(stat -c '%u:%G:%a:%h' -- "$1") == "$owner:$group:640:1" ]] || return 0
        local metadata size extra
        metadata=$(stat -c '%d:%i:%u:%G:%a:%h:%s:%y:%z' -- "$1") || return 0
        size=$(stat -c '%s' -- "$1") || return 0
        (( size <= 1048576 )) || return 0
        # A success sentinel follows only a complete no-follow, nonblocking read.
        # Embedded NUL, invalid UTF-8, growth and failed reads remain unknown.
        if ! {
            IFS= read -r -d '' -n 1048577 observed &&
            (( \${#observed} <= 1048576 )) &&
            { if IFS= read -r -d '' -n 1 extra; then false; else [[ -z "$extra" ]]; fi; }
        } < <(dd if="$1" iflag=nofollow,nonblock,noatime,count_bytes count=1048577 status=none && printf '\\0'); then
            observed=
            return 0
        fi
        utf8_text "$observed" || { observed=; return 0; }
        [[ -f "$1" && ! -L "$1" && $(stat -c '%d:%i:%u:%G:%a:%h:%s:%y:%z' -- "$1") == "$metadata" ]] || { observed=; return 0; }
        file_state=present
    }
    compared() {
        if [[ "$file_state" != present ]]; then printf '%s' "$file_state"
        elif [[ "$observed" == "$1" ]]; then printf matching
        else printf changed
        fi
    }
    inspect_file "$candidate"
    candidate_state=$(compared "$proposed")
    inspect_file "$installed"
    installed_base=$(compared "$original")
    installed_candidate=$(compared "$proposed")
    inspect_file "$backup"
    backup_base=$(compared "$original")
    printf '{"candidate":"%s","installedBase":"%s","installedCandidate":"%s","backupBase":"%s"}\\n' "$candidate_state" "$installed_base" "$installed_candidate" "$backup_base"
    exit
fi
expected_candidate= expected_base= predecessor= confirmation=
cleanup() {
    [[ -z "$expected_candidate" ]] || rm -f -- "$expected_candidate"
    [[ -z "$expected_base" ]] || rm -f -- "$expected_base"
    [[ -z "$predecessor" ]] || rm -f -- "$predecessor"
    [[ -z "$confirmation" ]] || rm -f -- "$confirmation"
    return 0
}
trap cleanup EXIT
expected_candidate=$(mktemp "$directory/.candidate-input.XXXXXX")
expected_base=$(mktemp "$directory/.installed-input.XXXXXX")
printf '%s' "$proposed" > "$expected_candidate"
printf '%s' "$original" > "$expected_base"
regular "$installed"
cmp -s -- "$installed" "$expected_base" || fail
case "$action" in
confirm)
    confirmation=$(mktemp "$directory/.confirmation.XXXXXX")
    # PID1 may write a pipe, never this root-owned configuration-directory file.
    # Bound only the local collector. Capture both statuses before any other
    # command so a collector refusal cannot release plausible partial output or
    # replace the launcher's original status when collection succeeded.
    if "$@" | (ulimit -f 4096 || exit "$?"; exec cat > "$confirmation"); then
        status=0
    else
        statuses=("\${PIPESTATUS[@]}")
        (( statuses[1] == 0 )) || exit "\${statuses[1]}"
        status=\${statuses[0]}
    fi
    case "$status" in 0|10|20|30|40|50) ;; *) exit "$status" ;; esac
    (( $(stat -c '%s' -- "$confirmation") <= 4194304 )) || fail
    regular "$installed"
    cmp -s -- "$installed" "$expected_base" || fail
    cat -- "$confirmation"
    exit "$status"
    ;;
write)
    if [[ -e "$candidate" || -L "$candidate" ]]; then
        regular "$candidate"
        cmp -s -- "$candidate" "$expected_candidate" || fail
        # Reuse a proven exact candidate without replacing its inode.
        exit 0
    fi
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

function encodeFrame(value: string): string {
    const bytes = new TextEncoder().encode(value);
    let binary = '';
    for (let offset = 0; offset < bytes.length; offset += 8192)
        binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192));
    return btoa(binary);
}

function invocation(
    action: 'read' | 'inspect' | 'write' | 'guard' | 'install' | 'remove' | 'confirm',
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
        input: guard === null
            ? ''
            : encodeFrame(guard.candidateContent) + '\n' +
            encodeFrame(guard.installedContent) + '\n',
    };
}

export function readInstalledInvocation(fixture?: ConfigurationFixture): GuardedInvocation {
    return invocation('read', null, [], fixture);
}

/* Reconcile only the four fixed paths against captured bytes. Unknown evidence
 * never becomes permission to write, reinstall, remove or clean up a candidate. */
export function inspectCandidateInvocation(
    guard: CandidateGuard, fixture?: ConfigurationFixture,
): GuardedInvocation {
    return invocation('inspect', guard, [], fixture);
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

/* Confirm the installed bytes after install consumed the candidate pathname. */
export function guardInstalledInvocation(
    argv: string[], expected: string, fixture?: ConfigurationFixture,
): GuardedInvocation {
    if (argv[0] !== 'systemd-run' || argv.includes('--config') || argv.includes('--idempotency-key') ||
        argv.slice(-2).join(' ') !== 'config validate')
        throw new Error('Installed confirmation requires the fixed installed validation adapter');
    return invocation('confirm', { candidateContent: expected, installedContent: expected }, argv, fixture);
}
