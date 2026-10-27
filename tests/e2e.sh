#!/usr/bin/env bash
# Live check of bin/board against a scratch repo: tests/e2e.sh OWNER/REPO
set -euo pipefail

REPO="${1:?usage: e2e.sh OWNER/REPO}"
[[ "${REPO#*/}" == *scratch* ]] || { echo "refusing: repo name must contain 'scratch'" >&2; exit 2; }

BOARD="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/bin/board"
WORK="$(mktemp -d)"
P="e2e-$(date +%s)"
NUMS=()

cleanup() {
  cd "$WORK/repo"
  for n in "${NUMS[@]}"; do "$BOARD" drop "$n" >/dev/null 2>&1 || true; done
  rm -rf "$WORK"
}
trap cleanup EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

# retry <desc> <command...>: the Projects items connection lags after mutations.
retry() {
  local desc="$1"; shift
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if "$@" >/dev/null 2>&1; then echo "ok: $desc"; return; fi
    sleep 2
  done
  fail "$desc"
}

gh repo clone "$REPO" "$WORK/repo" -- -q
cd "$WORK/repo"

add() { # add <suffix> -> issue number
  local out; out="$("$BOARD" add --title "$P $1" --body - <<<"e2e card")"
  local n; n="$(sed -E 's/^#([0-9]+).*/\1/' <<<"$out")"
  echo "$n"
}
list() { "$BOARD" list; }
line_has() { list | grep -F "$1" | grep -qF "$2"; }
line_lacks() { ! list | grep -F "$1" | grep -qF "$2"; }
above() { list | grep -nF "$1" | head -1 | cut -d: -f1 | { read -r a; list | grep -nF "$2" | head -1 | cut -d: -f1 | { read -r b; [ -n "$a" ] && [ -n "$b" ] && [ "$a" -lt "$b" ]; }; }; }

A="$(add A)"; B="$(add B)"; C="$(add C)"; NUMS=("$A" "$B" "$C")
retry "cards appear on list" bash -c "$(declare -f list); BOARD='$BOARD'; list | grep -qF '$P C'"
echo "--- list after add"; list

"$BOARD" move "$A" planned >/dev/null
"$BOARD" move "$B" in-progress >/dev/null
"$BOARD" move "$C" planned >/dev/null
"$BOARD" order "$C" --before "$A" >/dev/null
retry "C ordered above A" above "$P C" "$P A"

"$BOARD" block "$A" --by "$B" >/dev/null
retry "A blocked by B" line_has "$P A" "blocked by #$B"

"$BOARD" move "$B" done >/dev/null
retry "A unblocked after B done" line_lacks "$P A" "blocked by"
[ "$(gh issue view "$B" --json state -q .state)" = CLOSED ] || fail "B not closed"

"$BOARD" move "$B" triage >/dev/null
[ "$(gh issue view "$B" --json state -q .state)" = OPEN ] || fail "B not reopened"

"$BOARD" drop "$C" >/dev/null
retry "C searchable as not planned" bash -c "'$BOARD' search '$P' | grep -F '$P C' | grep -qF 'not planned'"

# pagination: tiny pages must match the default listing
retry "paginated list matches" bash -c "[ \"\$(BOARD_PAGE_SIZE=2 '$BOARD' list)\" = \"\$('$BOARD' list)\" ]"

echo "PASS"
