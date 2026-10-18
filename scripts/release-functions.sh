#!/usr/bin/env bash
# Read-only quiescence and atomic release switching (API-014, decision 121).
# Sourced by install-release.sh; disposable tests exercise these same functions.

release_die() { printf 'install-release: %s\n' "$*" >&2; return 1; }

canonical_absolute_path() {
  [[ $1 == /* && $1 != / && $1 != */ && $1 != *//* && $1 != *\\* &&
    /$1/ != */../* && /$1/ != */./* && ! $1 =~ [[:cntrl:]] ]]
}

valid_release_version() {
  [[ $1 =~ ^[0-9][A-Za-z0-9.+-]*$ ]] || release_die 'invalid release version'
}

require_quiescent() {
  local unit properties key value load active main control tasks cgroup
  local manager=${HFCACHE_SYSTEMCTL:-systemctl}
  local runtime=${HFCACHE_RUNTIME_DIRECTORY:-/run/hfcache}
  canonical_absolute_path "${runtime}" || { release_die 'unsafe runtime directory'; return 1; }
  local units=(hfcache-sync.timer hfcache-verify.timer hfcache-sync.service
    hfcache-verify.service hfcache-api.socket hfcache-api.service
    hfcache-verification.socket hfcache-verification.service)
  for unit in "${units[@]}"; do
    properties=$("${manager}" show "${unit}" --no-pager \
      --property=LoadState,ActiveState,MainPID,ControlPID,TasksCurrent,ControlGroup 2>/dev/null) || {
      release_die "cannot establish ${unit} state; drain and check the actual executors"
      return 1
    }
    load= active= main= control= tasks= cgroup=unknown
    while IFS='=' read -r key value; do
      case ${key} in
        LoadState) load=${value} ;;
        ActiveState) active=${value} ;;
        MainPID) main=${value} ;;
        ControlPID) control=${value} ;;
        TasksCurrent) tasks=${value} ;;
        ControlGroup) cgroup=${value} ;;
      esac
    done <<< "${properties}"
    [[ ${load} == loaded || ${load} == not-found ]] &&
      [[ ${active} == inactive || ${active} == failed ]] || {
      release_die "${unit} is active or unexplained; stop admission and drain executors first"
      return 1
    }
    if [[ ${unit} == *.service && ${load} == loaded ]]; then
      [[ ${main} == 0 && ${control} == 0 ]] &&
        [[ ${tasks} == 0 || ( ${tasks} == '[not set]' && -z ${cgroup} ) ]] || {
        release_die "${unit} retains processes or cannot prove their absence"
        return 1
      }
    fi
  done
  # Do not create, replace, unlink, or truncate the application's shared lock.
  # Keep this descriptor/lock until installer exit, including an atomic switch.
  local path=${runtime}/hfcache.lock before after
  if [[ ! -e ${path} && ! -L ${path} ]]; then
    if [[ -e ${PREFIX}/current || -L ${PREFIX}/current ]]; then
      release_die 'existing installation has no explainable runtime lock; do not switch'
      return 1
    fi
    return 0
  fi
  [[ -d ${runtime} && ! -L ${runtime} && -f ${path} && ! -L ${path} ]] || {
    release_die 'runtime lock is not a safe ordinary file'
    return 1
  }
  [[ $(stat -Lc '%a' -- "${runtime}") == 700 ]] &&
    [[ $(stat -Lc '%a:%h' -- "${path}") == 600:1 ]] || {
    release_die 'runtime lock permissions or link count are unexplained'
    return 1
  }
  before=$(stat -Lc '%d:%i' -- "${path}") || return 1
  exec {RELEASE_LOCK_FD}<"${path}" || return 1
  after=$(stat -Lc '%d:%i' -- "/proc/self/fd/${RELEASE_LOCK_FD}") || return 1
  [[ ${before} == "${after}" ]] &&
    [[ $(stat -Lc '%d:%i' -- "${path}") == "${after}" ]] &&
    flock --nonblock "${RELEASE_LOCK_FD}" || {
    release_die 'archive lock is held, changed, or unexplained; an orphan executor may remain'
    return 1
  }
}

switch_to() {
  valid_release_version "$1" || return 1
  local version=$1 target=${PREFIX}/releases/$1
  [[ -d ${target} && ! -L ${target} ]] || {
    release_die "release ${version} is not an ordinary installed directory"
    return 1
  }
  [[ -x ${target}/.venv/bin/hfcache ]] || {
    release_die "release ${version} has no built environment"
    return 1
  }
  # A predecessor without the observer cannot safely consume retained handles.
  # Never discard them or let legacy scheduled commands silently start anew.
  local observers=${HFCACHE_CLIENT_STATE_DIRECTORY:-/var/lib/hfcache/scheduled}
  local pending links
  canonical_absolute_path "${observers}" || { release_die 'unsafe observation directory'; return 1; }
  if [[ -e ${observers} || -L ${observers} ]]; then
    links=$(find -P "${observers}" -type l -print -quit) || return 1
    [[ -z ${links} ]] || {
      release_die 'scheduled observation state contains unexplained links'
      return 1
    }
    pending=$(find -P "${observers}" -name pending.json -print -quit) || return 1
    if [[ -n ${pending} ]]; then
      [[ -x ${target}/.venv/bin/python ]] &&
        "${target}/.venv/bin/python" -I -c \
          'import importlib.util,sys; sys.exit(0 if importlib.util.find_spec("hfcache.scheduled_client") is not None else 1)' || {
        release_die 'target cannot observe retained scheduled handles; resolve them before rollback'
        return 1
      }
    fi
  fi
  local staged=${PREFIX}/.current.$$
  ln -s "releases/${version}" "${staged}" || return 1
  mv -T -- "${staged}" "${PREFIX}/current" || return 1
  printf 'current -> releases/%s\n' "${version}"
}

installed_releases() {
  [[ -d ${PREFIX}/releases ]] || return 0
  find "${PREFIX}/releases" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -V
}
