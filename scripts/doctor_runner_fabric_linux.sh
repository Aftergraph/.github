#!/usr/bin/env bash
set -euo pipefail

ROOT="${AFTERGRAPH_RUNNER_ROOT:-/opt/aftergraph-runner-fabric}"
EXPECTED="${AFTERGRAPH_RUNNER_COUNT:-2}"
[[ "$EXPECTED" =~ ^[1-4]$ ]] || { echo "invalid expected count" >&2; exit 2; }

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
  service="$("$home/svc.sh" status 2>/dev/null || true)"
  if grep -qiE 'active|running' <<<"$service"; then
    printf 'PASS runner-%s %s\n' "$i" "$version"
    ok=$((ok+1))
  else
    printf 'NOT_RUNNING runner-%s\n' "$i"
  fi
done

printf 'RUNNER_FABRIC_READY=%s/%s\n' "$ok" "$EXPECTED"
[[ "$ok" -eq "$EXPECTED" ]]
