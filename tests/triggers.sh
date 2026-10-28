#!/usr/bin/env bash
# On-demand check (costs model calls; not run by unittest) that plain-language
# phrasings fire the right codebox skill headlessly: tests/triggers.sh [claude|codex|opencode ...]
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
# Ctrl-C: timeout runs the harness in its own process group, out of the terminal's reach, so stop it here.
trap 'kill "${tpid:-}" 2>/dev/null; exit 130' INT TERM

# Temp repo, no remote: any `board` call fails harmlessly with "no board".
mkdir "$WORK/repo" && cd "$WORK/repo" && git init -q
mkdir -p .claude/skills .agents/skills "$WORK/stubs"
# Stubs so a model calling gh/board can't reach the real account.
for c in gh board; do
  printf '#!/bin/sh\necho "disabled in trigger check" >&2\nexit 1\n' >"$WORK/stubs/$c"; chmod +x "$WORK/stubs/$c"
done
export PATH="$WORK/stubs:$PATH"
for s in "$ROOT"/plugins/*/skills/*; do
  ln -s "$s" ".claude/skills/${s##*/}"; ln -s "$s" ".agents/skills/${s##*/}"
done

PHRASES=("park this idea for later: add retries to the uploader"
         "what's next on the board?"
         "set up the board for this repo"
         "what does git status do?")
SKILLS=(codebox-defer codebox-next codebox-board-setup none)

# run HARNESS PROMPT: raw JSON events on stdout.
# claude: project settings only, so same-description user-level skills (defer, next) don't tie.
run() {
  case "$1" in
    claude)   claude -p --setting-sources project --output-format stream-json --verbose "$2" ;;
    codex)    codex exec --json --skip-git-repo-check -s read-only "$2" ;;
    opencode) opencode run --format json "$2" ;;
  esac
}

# fired HARNESS SKILL FILE: does the event output show SKILL being activated? (exact name, so `next` != `codebox-next`)
#   claude:   Skill tool_use with input.skill == SKILL
#   codex:    a command_execution whose command (not its output) names <SKILL>/SKILL.md
#   opencode: skill tool call with input.id == SKILL
fired() {
  case "$1" in
    claude)   grep -q "\"name\":\"Skill\",\"input\":{\"skill\":\"$2\"[,}]" "$3" ;;
    codex)    grep -qE "\"command\":\"([^\"\\\\]|\\\\.)*/$2/SKILL\\.md" "$3" ;;
    opencode) grep -q "\"tool\":\"skill\",\"state\":{\"status\":\"[a-z]*\",\"input\":{\"id\":\"$2\"" "$3" ;;
  esac
}

# any_fired HARNESS FILE: did any codebox-* skill fire (for the negative control)?
any_fired() {
  local s
  for s in "${SKILLS[@]:0:3}"; do fired "$1" "$s" "$2" && return 0; done
  return 1
}

harnesses=("$@"); [[ $# -gt 0 ]] || harnesses=(claude codex opencode)
rc=0
for h in "${harnesses[@]}"; do
  if ! command -v "$h" >/dev/null; then echo "SKIP $h (not on PATH)"; continue; fi
  for i in "${!PHRASES[@]}"; do
    out="$WORK/$h-$i.json"
    # In the background so a Ctrl-C trap runs at once instead of after the call; timeout kills its whole group.
    timeout 300 bash -c "$(declare -f run); run $h \"\$1\"" _ "${PHRASES[$i]}" >"$out" 2>"$out.err" </dev/null &
    tpid=$!
    wait "$tpid"; st=$?
    if (( st != 0 )); then
      echo "SKIP $h: ${PHRASES[$i]} (exit $st: $(head -c 120 "$out.err" | tr '\n' ' '))"; continue
    fi
    if [[ "${SKILLS[$i]}" == none ]]; then any_fired "$h" "$out" && ok=0 || ok=1
    else fired "$h" "${SKILLS[$i]}" "$out" && ok=1 || ok=0; fi
    if (( ok )); then echo "PASS $h: ${PHRASES[$i]} -> ${SKILLS[$i]}"
    else echo "FAIL $h: ${PHRASES[$i]} -> expected ${SKILLS[$i]}"; rc=1; fi
  done
done
exit "$rc"
