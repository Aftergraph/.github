#!/usr/bin/env bash
set -euo pipefail

ROOT="${AFTERGRAPH_RUNNER_ROOT:-/opt/aftergraph-runner-fabric}"
EXPECTED="${AFTERGRAPH_RUNNER_COUNT:-2}"
CHECK_TMPFS="${AFTERGRAPH_RUNNER_CHECK_TMPFS:-1}"
TMPFS_PATH="${AFTERGRAPH_RUNNER_TMPFS_PATH:-/tmp}"
TMPFS_MAX_USED_PCT="${AFTERGRAPH_RUNNER_TMPFS_MAX_USED_PCT:-85}"
TMPFS_MIN_FREE_INODES="${AFTERGRAPH_RUNNER_TMPFS_MIN_FREE_INODES:-10000}"

[[ "$EXPECTED" =~ ^[1-4]$ ]] || { echo "invalid expected count" >&2; exit 2; }
[[ "$CHECK_TMPFS" =~ ^[01]$ ]] || { echo "AFTERGRAPH_RUNNER_CHECK_TMPFS must be 0 or 1" >&2; exit 2; }
[[ "$TMPFS_MAX_USED_PCT" =~ ^[0-9]+$ && "$TMPFS_MAX_USED_PCT" -ge 1 && "$TMPFS_MAX_USED_PCT" -le 99 ]] || {
  echo "AFTERGRAPH_RUNNER_TMPFS_MAX_USED_PCT must be 1..99" >&2
  exit 2
}
[[ "$TMPFS_MIN_FREE_INODES" =~ ^[0-9]+$ ]] || {
  echo "AFTERGRAPH_RUNNER_TMPFS_MIN_FREE_INODES must be a non-negative integer" >&2
  exit 2
}

ok=0
for i in $(seq 1 "$EXPECTED"); do
  home="$ROOT/runner-${i}"
  if [[ ! -f "$home/.runner" || ! -x "$home/run.sh" ]]; then
    printf 'MISSING runner-%s root=%s\n' "$i" "$home"
    continue
  fi

  version=""
  if [[ -f "$home/.runner" ]]; then
    version="$(grep -o '"runnerId":[0-9]*' "$home/.runner" 2>/dev/null | head -n1 || true)"
  fi
  # svc.sh resolves service metadata relative to the runner root. Calling it
  # from an arbitrary operator working directory can therefore report a false
  # NOT_RUNNING for a healthy service.
  service="$(cd "$home" && ./svc.sh status 2>/dev/null || true)"
  if grep -qiE 'active|running' <<<"$service"; then
    printf 'PASS runner-%s %s\n' "$i" "$version"
    ok=$((ok+1))
  else
    printf 'NOT_RUNNING runner-%s\n' "$i"
  fi
done

printf 'RUNNER_FABRIC_READY=%s/%s\n' "$ok" "$EXPECTED"
[[ "$ok" -eq "$EXPECTED" ]] || exit 1

tmpfs_health() {
  [[ -d "$TMPFS_PATH" ]] || {
    printf 'RUNNER_TMPFS_HEALTH=FAIL reason=path_missing path=%s\n' "$TMPFS_PATH"
    return 1
  }

  local used_pct free_kb free_inodes listener_count active_workers deleted_memfd unreadable_maps
  used_pct="$(df -Pk "$TMPFS_PATH" | awk 'NR==2 {gsub(/%/,"",$5); print $5}')"
  free_kb="$(df -Pk "$TMPFS_PATH" | awk 'NR==2 {print $4}')"
  free_inodes="$(df -Pi "$TMPFS_PATH" | awk 'NR==2 {print $4}')"

  [[ "$used_pct" =~ ^[0-9]+$ ]] || {
    printf 'RUNNER_TMPFS_HEALTH=FAIL reason=used_percent_unreadable path=%s\n' "$TMPFS_PATH"
    return 1
  }
  [[ "$free_kb" =~ ^[0-9]+$ ]] || {
    printf 'RUNNER_TMPFS_HEALTH=FAIL reason=free_space_unreadable path=%s\n' "$TMPFS_PATH"
    return 1
  }
  [[ "$free_inodes" =~ ^[0-9]+$ ]] || {
    printf 'RUNNER_TMPFS_HEALTH=FAIL reason=inode_state_unreadable path=%s\n' "$TMPFS_PATH"
    return 1
  }

  listener_count=0
  active_workers=0
  deleted_memfd=0
  unreadable_maps=0

  while IFS= read -r pid; do
    [[ "$pid" =~ ^[0-9]+$ ]] || continue
    listener_count=$((listener_count+1))

    if command -v pgrep >/dev/null 2>&1; then
      if pgrep -P "$pid" -f 'Runner\.Worker' >/dev/null 2>&1; then
        active_workers=$((active_workers+1))
      fi
    fi

    if [[ -r "/proc/$pid/maps" ]]; then
      count="$(grep -cE '/memfd:doublemapper.*\(deleted\)' "/proc/$pid/maps" 2>/dev/null || true)"
      [[ "$count" =~ ^[0-9]+$ ]] || count=0
      deleted_memfd=$((deleted_memfd+count))
    else
      unreadable_maps=$((unreadable_maps+1))
    fi
  done < <(pgrep -f '/Runner\.Listener run --startuptype service' 2>/dev/null || true)

  printf 'RUNNER_TMPFS_PATH=%s\n' "$TMPFS_PATH"
  printf 'RUNNER_TMPFS_USED_PCT=%s\n' "$used_pct"
  printf 'RUNNER_TMPFS_FREE_KB=%s\n' "$free_kb"
  printf 'RUNNER_TMPFS_FREE_INODES=%s\n' "$free_inodes"
  printf 'RUNNER_LISTENERS=%s\n' "$listener_count"
  printf 'RUNNER_LISTENER_ACTIVE_WORKERS=%s\n' "$active_workers"
  printf 'RUNNER_LISTENER_DELETED_MEMFD_MAPPINGS=%s\n' "$deleted_memfd"
  printf 'RUNNER_LISTENER_UNREADABLE_MAPS=%s\n' "$unreadable_maps"

  if (( used_pct > TMPFS_MAX_USED_PCT )); then
    printf 'RUNNER_TMPFS_HEALTH=FAIL reason=space_pressure threshold=%s actual=%s\n' "$TMPFS_MAX_USED_PCT" "$used_pct"
    return 1
  fi
  if (( free_inodes < TMPFS_MIN_FREE_INODES )); then
    printf 'RUNNER_TMPFS_HEALTH=FAIL reason=inode_pressure threshold=%s actual=%s\n' "$TMPFS_MIN_FREE_INODES" "$free_inodes"
    return 1
  fi

  printf 'RUNNER_TMPFS_HEALTH=PASS\n'
}

if [[ "$CHECK_TMPFS" == "1" ]]; then
  tmpfs_health || exit 1
else
  echo "RUNNER_TMPFS_HEALTH=SKIPPED"
fi

if [[ "${AFTERGRAPH_RUNNER_VERIFY_GITHUB:-0}" == "1" ]]; then
  command -v gh >/dev/null 2>&1 || { echo "gh CLI required for GitHub visibility verification" >&2; exit 2; }
  : "${GH_TOKEN:?GH_TOKEN with organization runner read permission is required}"

  prefix="${AFTERGRAPH_RUNNER_NAME_PREFIX:-aftergraph-ci}"
  required_label="${AFTERGRAPH_RUNNER_REQUIRED_LABEL:-aftergraph-ci}"

  inventory="$(gh api --paginate /orgs/Aftergraph/actions/runners \
    --jq '.runners[] | [.name, .status, (.busy|tostring), (.labels|map(.name)|join(","))] | @tsv')"

  visible=0
  while IFS=$'\t' read -r name status busy labels; do
    [[ -n "$name" ]] || continue
    if [[ "$name" == "$prefix-"* && "$status" == "online" && ",$labels," == *",$required_label,"* ]]; then
      visible=$((visible+1))
      printf 'ORG_VISIBLE name=%s status=%s busy=%s labels=%s\n' "$name" "$status" "$busy" "$labels"
    fi
  done <<<"$inventory"

  printf 'GITHUB_ORG_VISIBLE_READY=%s/%s\n' "$visible" "$EXPECTED"
  [[ "$visible" -ge "$EXPECTED" ]] || {
    echo "organization-visible capacity is below expected warm count" >&2
    exit 1
  }
fi

echo "RUNNER_FABRIC_DOCTOR=PASS"
