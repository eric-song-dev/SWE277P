#!/usr/bin/env bash
# Final acceptance run: lint, tests, build, e2e, then the A1-A10 table.
# Usage (from anywhere): bash scripts/acceptance.sh
# Stops on the first failing step. Needs the dev DB on 127.0.0.1:5432 and Docker.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
RESULTS="$ROOT/docs/benchmark-results.md"

CURRENT="(none)"
trap 'rc=$?; if [ $rc -ne 0 ]; then echo; echo "ACCEPTANCE FAILED at step: $CURRENT (exit $rc)" >&2; fi' EXIT

step() {
  CURRENT="$1"
  shift
  echo
  echo "=== $CURRENT ==="
  echo "+ $*"
  "$@"
}

cd "$BACKEND"
step "1a. ruff check" uv run ruff check .
step "1b. ruff format --check" uv run ruff format --check .
step "2. pytest (all)" uv run pytest -v
step "3. pytest -m acceptance" uv run pytest -m acceptance -v

cd "$FRONTEND"
step "4. Vitest" npm test -- --run
step "5a. oxlint" npm run lint
step "5b. build" npm run build
step "6. Playwright e2e" npm run e2e

CURRENT="results table"

# Status of one A-row from the Acceptance summary table in benchmark-results.md.
doc_status() {
  local s
  s="$(awk -F'|' -v id="$1" '{ a=$2; b=$3; gsub(/^ +| +$/, "", a); gsub(/^ +| +$/, "", b); if (a == id) { print b; exit } }' "$RESULTS")"
  echo "${s:-MISSING}"
}

echo
echo "=== Acceptance results ==="
printf '%-4s %-10s %s\n' "ID" "Status" "Source"
for id in A1 A2 A5 A6 A8 A9; do
  printf '%-4s %-10s %s\n' "$id" "PASS" "pytest -m acceptance"
done
DOC_FAILED=""
for id in A3 A4 A10; do
  row_status="$(doc_status "$id")"
  printf '%-4s %-10s %s\n' "$id" "$row_status" "docs/benchmark-results.md"
  if [ "$row_status" != "PASS" ]; then DOC_FAILED="$DOC_FAILED $id"; fi
done
printf '%-4s %-10s %s\n' "A7" "deferred" "login in backlog"
if [ -n "$DOC_FAILED" ]; then
  echo "ACCEPTANCE INCOMPLETE: not PASS in docs/benchmark-results.md:$DOC_FAILED" >&2
  exit 1
fi
