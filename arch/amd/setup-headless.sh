#!/bin/bash
# Post-installation script for headless AI stack configuration
# Run after install-ai-stack.sh completes
# Usage: bash ~/setup-headless.sh

set -e

echo "=============================================="
echo "Headless AI Stack Configuration"
echo "=============================================="
echo ""

# Get username
USER=$(whoami)

echo "=== Enabling user lingering for $USER ==="
echo "This allows systemd user services to run without being logged in."
sudo loginctl enable-linger "$USER"

echo ""
echo "=== Reloading systemd user daemon ==="
systemctl --user daemon-reload

echo ""
echo "=== Enabling JupyterLab service ==="
systemctl --user enable jupyterlab.service

echo ""
echo "=== Starting JupyterLab service ==="
systemctl --user start jupyterlab.service

echo ""
echo "=== Checking JupyterLab service status ==="
systemctl --user status jupyterlab.service --no-pager || true

echo ""
echo "=============================================="
echo "Headless Configuration Complete!"
echo "=============================================="
echo ""
echo "JupyterLab is now running as a systemd service."
echo ""
echo "IMPORTANT: Set a JupyterLab password:"
echo "  source ~/.config/ai-env.sh && jupyter lab password"
echo ""
echo "Access JupyterLab at:"
echo "  - Local: http://localhost:8888"
echo "  - Remote: http://<your-ip>:8888"
echo "  - Tailscale: http://<tailscale-hostname>:8888"
echo ""
echo "Useful commands:"
echo "  - Check status: systemctl --user status jupyterlab"
echo "  - View logs: journalctl --user -u jupyterlab -f"
echo "  - Restart: systemctl --user restart jupyterlab"
echo "  - Stop: systemctl --user stop jupyterlab"
echo ""
echo "For long-running jobs, use tmux:"
echo "  tmux new -s job-name    # Start new session"
echo "  Ctrl+B, D               # Detach from session"
echo "  tmux attach -t job-name # Reattach to session"
echo "  tmux ls                 # List all sessions"
