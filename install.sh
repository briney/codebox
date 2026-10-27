#!/usr/bin/env bash
# Link codebox skills and `board` into place. Safe to re-run.
set -euo pipefail

CODEBOX_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

link() { # link <target> <dest>
  mkdir -p "$(dirname "$2")"
  ln -sfn "$1" "$2"
  echo "✓ $2 -> $1"
}

# 1. Prune dangling links whose target mentions codebox (old installs).
for dir in ~/.claude/commands ~/.claude/skills ~/.agents/skills ~/.config/opencode/skills ~/.local/bin; do
  [ -d "$dir" ] || continue
  for f in "$dir"/* "$dir"/.[!.]*; do
    if [ -L "$f" ] && [ ! -e "$f" ] && [[ "$(readlink "$f")" == *codebox* ]]; then
      rm "$f"
      echo "- pruned $f"
    fi
  done
done

# 2. Skills (Claude Code reads ~/.claude/skills; Codex and OpenCode read ~/.agents/skills).
for s in "$CODEBOX_ROOT"/skills/*/; do
  name="$(basename "$s")"
  link "${s%/}" ~/.claude/skills/"$name"
  link "${s%/}" ~/.agents/skills/"$name"
done

# 3. board on PATH.
link "$CODEBOX_ROOT/bin/board" ~/.local/bin/board
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo "warning: ~/.local/bin is not on PATH; add it to use \`board\`" >&2 ;;
esac
