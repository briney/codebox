#!/usr/bin/env bash
set -euo pipefail

# ─── Resolve paths ───────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEBOX_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTRUCTIONS_DIR="$SCRIPT_DIR/instructions"
SKILLS_DIR="$CODEBOX_ROOT/skills"

# ─── Helpers ─────────────────────────────────────────────────────────────────
ok()   { printf '  ✓ %s\n' "$1"; }
info() { printf '\n%s\n' "$1"; }

copy_file() {
    local src="$1" dest="$2"
    cp "$src" "$dest"
    ok "$(basename "$src") → $dest"
}

symlink() {
    local target="$1" link="$2"
    ln -sf "$target" "$link"
    ok "$(basename "$link") → $target"
}

# ─── Install functions ───────────────────────────────────────────────────────

install_instructions() {
    local dest_dir="$1" instructions_name="$2"
    mkdir -p "$dest_dir"
    copy_file "$INSTRUCTIONS_DIR/INSTRUCTIONS.md" "$dest_dir/$instructions_name"
    copy_file "$INSTRUCTIONS_DIR/WEB.md" "$dest_dir/WEB.md"
    copy_file "$INSTRUCTIONS_DIR/COMPILED.md" "$dest_dir/COMPILED.md"
}

install_claude() {
    info "Setting up Claude Code (~/.claude/) ..."
    local dest="$HOME/.claude"

    install_instructions "$dest" "CLAUDE.md"

    # Claude Code-specific settings
    if [ -f "$SCRIPT_DIR/claude/settings.json" ]; then
        copy_file "$SCRIPT_DIR/claude/settings.json" "$dest/settings.json"
    fi

    # Register skills as slash commands
    mkdir -p "$dest/commands"
    for skill_dir in "$SKILLS_DIR"/*/; do
        skill_dir="${skill_dir%/}"
        local name
        name="$(basename "$skill_dir")"
        if [ -f "$skill_dir/SKILL.md" ]; then
            symlink "$skill_dir/SKILL.md" "$dest/commands/$name.md"
        fi
    done
}

install_codex() {
    info "Setting up Codex (~/.codex/) ..."
    local dest="$HOME/.codex"

    install_instructions "$dest" "AGENTS.md"
}

install_opencode() {
    info "Setting up OpenCode (~/.config/opencode/) ..."
    local dest="$HOME/.config/opencode"

    install_instructions "$dest" "AGENTS.md"

    # Register skills (OpenCode supports skills/*/SKILL.md natively)
    mkdir -p "$dest/skills"
    for skill_dir in "$SKILLS_DIR"/*/; do
        skill_dir="${skill_dir%/}"
        local name
        name="$(basename "$skill_dir")"
        if [ -f "$skill_dir/SKILL.md" ]; then
            symlink "$skill_dir" "$dest/skills/$name"
        fi
    done
}

# ─── Main ────────────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [--all | --claude | --codex | --opencode]

Install coding agent configuration files from codebox.

Options:
  --all        Set up all harnesses (default)
  --claude     Set up Claude Code only
  --codex      Set up Codex only
  --opencode   Set up OpenCode only
  -h, --help   Show this help message

Multiple flags can be combined, e.g.: $(basename "$0") --claude --opencode
EOF
}

targets=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --all)      targets=(claude codex opencode); shift ;;
        --claude)   targets+=(claude); shift ;;
        --codex)    targets+=(codex); shift ;;
        --opencode) targets+=(opencode); shift ;;
        -h|--help)  usage; exit 0 ;;
        *)          echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# Default to all if no flags given
if [ ${#targets[@]} -eq 0 ]; then
    targets=(claude codex opencode)
fi

echo "codebox install (root: $CODEBOX_ROOT)"

for target in "${targets[@]}"; do
    "install_$target"
done

info "Done."
