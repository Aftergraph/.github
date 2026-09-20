#!/usr/bin/env bash
set -euo pipefail
umask 027

RUNNER_VERSION="2.337.0"
RUNNER_SHA256="70920811a4f8ad4328818682bca5c6469c1c942fab52448868071d0063816613"
ARCHIVE="actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
DOWNLOAD_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${ARCHIVE}"

SCOPE_URL="${AFTERGRAPH_RUNNER_SCOPE_URL:-https://github.com/Aftergraph}"
ROOT="${AFTERGRAPH_RUNNER_ROOT:-/opt/aftergraph-runner-fabric}"
COUNT="${AFTERGRAPH_RUNNER_COUNT:-2}"
NAME_PREFIX="${AFTERGRAPH_RUNNER_NAME_PREFIX:-aftergraph-ci}"
LABELS="${AFTERGRAPH_RUNNER_LABELS:-aftergraph-ci}"
USER_PREFIX="${AFTERGRAPH_RUNNER_USER_PREFIX:-aftergraph-ci}"

fail(){ printf 'Aftergraph runner fabric bootstrap: %s\n' "$1" >&2; exit 2; }

[[ ${EUID:-$(id -u)} -eq 0 ]] || fail "run as root"
[[ "$(uname -s)" == "Linux" ]] || fail "Linux required"
case "$(uname -m)" in x86_64|amd64) ;; *) fail "Linux x86-64 required" ;; esac
[[ "$COUNT" =~ ^[1-4]$ ]] || fail "AFTERGRAPH_RUNNER_COUNT must be 1..4"
: "${AFTERGRAPH_RUNNER_REGISTRATION_TOKEN:?set a fresh organization runner registration token}"
for cmd in curl sha256sum tar useradd runuser; do command -v "$cmd" >/dev/null || fail "$cmd required"; done

install -d -m 0755 -o root -g root "$ROOT"
TMP="$(mktemp -d)"
cleanup(){ rm -rf "$TMP"; unset AFTERGRAPH_RUNNER_REGISTRATION_TOKEN || true; }
trap cleanup EXIT

curl --fail --location --silent --show-error "$DOWNLOAD_URL" -o "$TMP/$ARCHIVE"
printf '%s  %s\n' "$RUNNER_SHA256" "$TMP/$ARCHIVE" | sha256sum -c -

for i in $(seq 1 "$COUNT"); do
  user="${USER_PREFIX}-${i}"
  home="$ROOT/runner-${i}"
  name="${NAME_PREFIX}-${i}-$(hostname -s)"

  if ! id "$user" >/dev/null 2>&1; then
    useradd --create-home --shell /bin/bash "$user"
  fi

  install -d -m 0750 -o "$user" -g "$user" "$home"
  if [[ -e "$home/.runner" ]]; then
    printf 'runner %s already configured at %s; leaving intact\n' "$name" "$home"
    continue
  fi

  tar -xzf "$TMP/$ARCHIVE" -C "$home"
  chown -R "$user:$user" "$home"
  "$home/bin/installdependencies.sh"

  args=(
    --unattended
    --url "$SCOPE_URL"
    --token "$AFTERGRAPH_RUNNER_REGISTRATION_TOKEN"
    --name "$name"
    --labels "$LABELS"
    --work _work
    --disableupdate
    --replace
  )
  if [[ -n "${AFTERGRAPH_RUNNER_GROUP:-}" ]]; then
    args+=(--runnergroup "$AFTERGRAPH_RUNNER_GROUP")
  fi

  (
    cd "$home"
    runuser -u "$user" -- ./config.sh "${args[@]}"
    ./svc.sh install "$user"
    ./svc.sh start
  )

  runuser -u "$user" -- test -x "$home/run.sh"
  printf 'configured runner name=%s labels=%s root=%s\n' "$name" "$LABELS" "$home"
done

unset AFTERGRAPH_RUNNER_REGISTRATION_TOKEN
printf 'Aftergraph runner fabric bootstrap complete: count=%s scope=%s labels=%s\n' "$COUNT" "$SCOPE_URL" "$LABELS"
