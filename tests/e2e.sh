#!/usr/bin/env bash
# Live check of plugins/board/bin/board against a scratch repo: tests/e2e.sh OWNER/REPO
set -euo pipefail

REPO="${1:?usage: e2e.sh OWNER/REPO}"
[[ "${REPO#*/}" == *scratch* ]] || { echo "refusing: repo name must contain 'scratch'" >&2; exit 2; }

BOARD="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/plugins/board/bin/board"
WORK="$(mktemp -d)"
P="e2e-$(date +%s)"
NUMS=()

cleanup() {
  local rc=$? n
  cd "$WORK/repo" 2>/dev/null || cd "$WORK"
  for n in ${NUMS[@]+"${NUMS[@]}"}; do
    "$BOARD" drop "$n" >/dev/null 2>&1 || { echo "leaked #$n" >&2; rc=1; }
  done
  cd / && rm -rf "$WORK"
  exit "$rc"
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

LAST=""
add() { # add <suffix>: creates a card, sets LAST, records it for cleanup
  local out; out="$("$BOARD" add --title "$P $1" --body - <<<"e2e card")"
  LAST="$(sed -E 's/^#([0-9]+).*/\1/' <<<"$out")"
  NUMS+=("$LAST")
}
# group <Status>: the item lines under that status header of `board list`
group() { "$BOARD" list | awk -v h="$1" '$0==h{on=1;next} /^$/{on=0} on'; }
in_group() { group "$1" | grep -qF "$2"; }                 # in_group Status text
not_in_group() { ! in_group "$@"; }
above() { group "$1" | grep -nF "$2" | head -1 | cut -d: -f1 | { read -r a || true
          group "$1" | grep -nF "$3" | head -1 | cut -d: -f1 | { read -r b || true
          [ -n "$a" ] && [ -n "$b" ] && [ "$a" -lt "$b" ]; }; }; }   # above Status first second
line_has() { "$BOARD" list | grep -F "$1" | grep -qF "$2"; }
line_lacks() { ! line_has "$@"; }
state_is() { [ "$(gh issue view "$1" --json state -q .state)" = "$2" ]; }

add A; A=$LAST; add B; B=$LAST; add C; C=$LAST
retry "A in Triage" in_group Triage "$P A"
retry "B in Triage" in_group Triage "$P B"
retry "C in Triage" in_group Triage "$P C"
echo "--- list after add"; "$BOARD" list

"$BOARD" move "$A" planned >/dev/null
"$BOARD" move "$B" in-progress >/dev/null
retry "A in Planned" in_group Planned "$P A"
retry "B in In Progress" in_group "In Progress" "$P B"

"$BOARD" move "$C" planned >/dev/null
"$BOARD" order "$C" --before "$A" >/dev/null
retry "C in Planned" in_group Planned "$P C"
retry "C above A in Planned" above Planned "$P C" "$P A"

"$BOARD" block "$A" --by "$B" >/dev/null
retry "A blocked by B" line_has "$P A" "blocked by #$B"

"$BOARD" move "$B" done >/dev/null
retry "A unblocked after B done" line_lacks "$P A" "blocked by"
state_is "$B" CLOSED || fail "B not closed"

"$BOARD" move "$B" triage >/dev/null
state_is "$B" OPEN || fail "B not reopened"
retry "B back in Triage" in_group Triage "$P B"

"$BOARD" drop "$C" >/dev/null
retry "C searchable as not planned" bash -c "'$BOARD' search '$P' | grep -F '$P C' | grep -qF 'not planned'"

# pagination: tiny pages must match the default listing
retry "paginated list matches" bash -c "[ \"\$(BOARD_PAGE_SIZE=2 '$BOARD' list)\" = \"\$('$BOARD' list)\" ]"

echo "PASS"
