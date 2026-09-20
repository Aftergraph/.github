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
[[ "$ok" -eq "$EXPECTED" ]] || exit 1

if [[ "${AFTERGRAPH_RUNNER_VERIFY_GITHUB:-0}" == "1" ]]; then
  command -v gh >/dev/null 2>&1 || { echo "gh CLI required for GitHub visibility verification" >&2; exit 2; }
  : "${GH_TOKEN:?GH_TOKEN with organization runner read permission is required}"

  prefix="${AFTERGRAPH_RUNNER_NAME_PREFIX:-aftergraph-ci}"
  required_label="${AFTERGRAPH_RUNNER_REQUIRED_LABEL:-aftergraph-ci}"

  inventory="$(gh api --paginate /orgs/Aftergraph/actions/runners \
    --jq '.runners[] | [.name, .status, (.busy|tostring), (.labels|map(.name)|join(","))] | @tsv')"

  visible=0
  while IFS=
\t' read -r name status busy labels; do
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
