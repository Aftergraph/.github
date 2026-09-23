#!/usr/bin/env bash
set -euo pipefail
umask 027

ACTION="${1:-status}"
case "$ACTION" in status|recycle-idle) ;; *) echo "usage: $0 [status|recycle-idle]" >&2; exit 2 ;; esac

ROOT="${AFTERGRAPH_RUNNER_ROOT:-/opt/aftergraph-runner-fabric}"
EXPECTED="${AFTERGRAPH_RUNNER_COUNT:-2}"
TMPFS_PATH="${AFTERGRAPH_RUNNER_TMPFS_PATH:-/tmp}"
TMPFS_MAX_USED_PCT="${AFTERGRAPH_RUNNER_TMPFS_MAX_USED_PCT:-85}"
MIN_AGE_SECONDS="${AFTERGRAPH_RUNNER_RECYCLE_MIN_AGE_SECONDS:-3600}"

fail(){ printf 'Aftergraph runner fabric maintenance: %s\n' "$*" >&2; exit 2; }

[[ "$EXPECTED" =~ ^[1-4]$ ]] || fail "AFTERGRAPH_RUNNER_COUNT must be 1..4"
[[ "$TMPFS_MAX_USED_PCT" =~ ^[0-9]+$ && "$TMPFS_MAX_USED_PCT" -ge 1 && "$TMPFS_MAX_USED_PCT" -le 99 ]] || fail "AFTERGRAPH_RUNNER_TMPFS_MAX_USED_PCT must be 1..99"
[[ "$MIN_AGE_SECONDS" =~ ^[0-9]+$ ]] || fail "AFTERGRAPH_RUNNER_RECYCLE_MIN_AGE_SECONDS must be a non-negative integer"
[[ -d "$TMPFS_PATH" ]] || fail "tmpfs_path_missing:$TMPFS_PATH"

tmp_used_pct(){
  df -Pk "$TMPFS_PATH" | awk 'NR==2 {gsub(/%/,"",$5); print $5}'
}

listener_memfd_count(){
  local pid="$1"
  [[ -r "/proc/$pid/maps" ]] || { printf '0\n'; return 0; }
  grep -cE '/memfd:doublemapper' "/proc/$pid/maps" 2>/dev/null || true
}

listener_worker_children(){
  local pid="$1"
  if command -v pgrep >/dev/null 2>&1; then
    pgrep -P "$pid" -f 'Runner\.Worker' 2>/dev/null || true
  fi
}

listener_age_seconds(){
  local pid="$1" value
  value="$(ps -o etimes= -p "$pid" 2>/dev/null | tr -d ' ' || true)"
  [[ "$value" =~ ^[0-9]+$ ]] || value=0
  printf '%s\n' "$value"
}

runner_unit(){
  local home="$1"
  [[ -f "$home/.service" ]] || return 1
  tr -d '\r\n' <"$home/.service"
}

runner_status(){
  local i="$1" home unit pid age memfd workers
  home="$ROOT/runner-$i"
  [[ -d "$home" && -f "$home/.runner" && -x "$home/run.sh" ]] || {
    printf 'RUNNER_MAINTENANCE runner=%s state=MISSING\n' "$i"
    return 1
  }
  unit="$(runner_unit "$home" || true)"
  [[ -n "$unit" ]] || {
    printf 'RUNNER_MAINTENANCE runner=%s state=NO_SERVICE_METADATA\n' "$i"
    return 1
  }
  systemctl is-active --quiet "$unit" || {
    printf 'RUNNER_MAINTENANCE runner=%s unit=%s state=INACTIVE\n' "$i" "$unit"
    return 1
  }
  pid="$(systemctl show "$unit" -p MainPID --value)"
  [[ "$pid" =~ ^[1-9][0-9]*$ ]] || {
    printf 'RUNNER_MAINTENANCE runner=%s unit=%s state=INVALID_PID pid=%s\n' "$i" "$unit" "$pid"
    return 1
  }
  age="$(listener_age_seconds "$pid")"
  memfd="$(listener_memfd_count "$pid")"
  workers="$(listener_worker_children "$pid" | wc -l | tr -d ' ')"
  [[ "$workers" =~ ^[0-9]+$ ]] || workers=0
  printf 'RUNNER_MAINTENANCE runner=%s unit=%s pid=%s age_seconds=%s deleted_memfd_mappings=%s active_worker_children=%s\n' \
    "$i" "$unit" "$pid" "$age" "$memfd" "$workers"
}

used_before="$(tmp_used_pct)"
[[ "$used_before" =~ ^[0-9]+$ ]] || fail "tmpfs_used_percent_unreadable"
printf 'RUNNER_TMPFS_USED_PCT_BEFORE=%s\n' "$used_before"

for i in $(seq 1 "$EXPECTED"); do
  runner_status "$i" || true
done

if [[ "$ACTION" == "status" ]]; then
  echo "RUNNER_FABRIC_MAINTENANCE=STATUS_ONLY"
  exit 0
fi

[[ "${EUID:-$(id -u)}" -eq 0 ]] || fail "root_required"
if (( used_before <= TMPFS_MAX_USED_PCT )); then
  printf 'RUNNER_FABRIC_MAINTENANCE=NOOP reason=tmpfs_below_threshold threshold=%s actual=%s\n' "$TMPFS_MAX_USED_PCT" "$used_before"
  exit 0
fi

recycled=0
busy=0
clean=0
young=0

for i in $(seq 1 "$EXPECTED"); do
  home="$ROOT/runner-$i"
  [[ -d "$home" && -f "$home/.service" ]] || continue
  unit="$(runner_unit "$home" || true)"
  [[ -n "$unit" ]] || continue
  systemctl is-active --quiet "$unit" || continue

  old_pid="$(systemctl show "$unit" -p MainPID --value)"
  [[ "$old_pid" =~ ^[1-9][0-9]*$ ]] || continue

  workers="$(listener_worker_children "$old_pid" | wc -l | tr -d ' ')"
  [[ "$workers" =~ ^[0-9]+$ ]] || workers=0
  if (( workers > 0 )); then
    printf 'SKIP runner=%s reason=active_worker_children count=%s\n' "$i" "$workers"
    busy=$((busy+1))
    continue
  fi

  age="$(listener_age_seconds "$old_pid")"
  if (( age < MIN_AGE_SECONDS )); then
    printf 'SKIP runner=%s reason=listener_too_young age_seconds=%s minimum=%s\n' "$i" "$age" "$MIN_AGE_SECONDS"
    young=$((young+1))
    continue
  fi

  memfd="$(listener_memfd_count "$old_pid")"
  [[ "$memfd" =~ ^[0-9]+$ ]] || memfd=0
  if (( memfd == 0 )); then
    printf 'SKIP runner=%s reason=no_deleted_memfd_mapping\n' "$i"
    clean=$((clean+1))
    continue
  fi

  printf 'RECYCLE runner=%s unit=%s old_pid=%s deleted_memfd_mappings=%s\n' "$i" "$unit" "$old_pid" "$memfd"
  systemctl restart "$unit"

  healthy=false
  for _ in $(seq 1 60); do
    if systemctl is-active --quiet "$unit"; then
      new_pid="$(systemctl show "$unit" -p MainPID --value)"
      if [[ "$new_pid" =~ ^[1-9][0-9]*$ && "$new_pid" != "$old_pid" ]]; then
        if ! listener_worker_children "$new_pid" | grep -q .; then
          healthy=true
          break
        fi
      fi
    fi
    sleep 0.5
  done
  [[ "$healthy" == true ]] || fail "runner_restart_readback_failed:$i"
  printf 'RECYCLED runner=%s new_pid=%s\n' "$i" "$new_pid"
  recycled=$((recycled+1))
done

used_after="$(tmp_used_pct)"
[[ "$used_after" =~ ^[0-9]+$ ]] || fail "tmpfs_used_percent_after_unreadable"
printf 'RUNNER_TMPFS_USED_PCT_AFTER=%s\n' "$used_after"
printf 'RUNNER_FABRIC_RECYCLED=%s\n' "$recycled"
printf 'RUNNER_FABRIC_SKIPPED_BUSY=%s\n' "$busy"
printf 'RUNNER_FABRIC_SKIPPED_CLEAN=%s\n' "$clean"
printf 'RUNNER_FABRIC_SKIPPED_YOUNG=%s\n' "$young"

if (( used_after > TMPFS_MAX_USED_PCT )); then
  printf 'RUNNER_FABRIC_MAINTENANCE=BLOCKED reason=tmpfs_pressure_remains threshold=%s actual=%s\n' "$TMPFS_MAX_USED_PCT" "$used_after"
  exit 1
fi

echo "RUNNER_FABRIC_MAINTENANCE=PASS"
