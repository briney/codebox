#!/usr/bin/env bash
# Pull the latest notebook submodule state.
#
# Usage:
#   notebook-pull.sh

set -euo pipefail

CODEBOX_DIR="${CODEBOX_DIR:-$HOME/codebox}"
NOTEBOOK_DIR="$CODEBOX_DIR/notebook"

cd "$NOTEBOOK_DIR"
git pull
