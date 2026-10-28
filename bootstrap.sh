#!/usr/bin/env bash
set -euo pipefail
unset GIT_DIR GIT_WORK_TREE

REPO_URL="${CODEBOX_REPO:-https://github.com/briney/codebox.git}"
HOME_DIR="${CODEBOX_HOME:-$HOME/.codebox}"
LINK="$HOME/.local/bin/codebox"

die() { echo "codebox bootstrap: $*" >&2; exit 1; }

command -v git >/dev/null && command -v python3 >/dev/null || die "needs git and python3"

if [ ! -e "$HOME_DIR" ]; then
  next="codebox install"
  git clone --quiet "$REPO_URL" "$HOME_DIR"
  tag=$(git -C "$HOME_DIR" tag --list 'v[0-9]*' --sort=-v:refname | head -1)
  if [ -z "$tag" ]; then
    rm -rf "$HOME_DIR"
    die "$REPO_URL has no release tags yet"
  fi
  git -C "$HOME_DIR" checkout --quiet "$tag"
else
  next="codebox update"
  [ -e "$HOME_DIR/.git" ] || die "$HOME_DIR exists and is not a codebox checkout; remove it and re-run"
  git -C "$HOME_DIR" fetch --tags --quiet || echo "codebox bootstrap: warning: git fetch failed" >&2
fi

mkdir -p "$HOME/.local/bin"
if [ -e "$LINK" ] && [ ! -L "$LINK" ]; then
  die "~/.local/bin/codebox exists and isn't a link; move it and re-run"
fi
ln -sfn "$HOME_DIR/bin/codebox" "$LINK"

case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo 'add to your shell profile: export PATH="$HOME/.local/bin:$PATH"' ;;
esac
echo "next: $next"
