#!/bin/bash
# Post-installation script for headless AI stack configuration
# Run after install_ai_stack.sh completes
# Usage: bash ~/setup_headless.sh

set -e

echo "=============================================="
echo "Headless AI Stack Configuration"
echo "=============================================="
echo ""

# Get username
USER=$(whoami)

echo "=== Creating JupyterLab systemd service ==="
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/jupyterlab.service" << EOF
[Unit]
Description=JupyterLab Server
After=network.target

[Service]
Type=simple
ExecStart=%h/miniforge3/envs/ai/bin/jupyter lab --no-browser --port=8888 --ip=0.0.0.0
WorkingDirectory=%h
Restart=on-failure
RestartSec=10
Environment="PATH=%h/miniforge3/envs/ai/bin:/usr/local/cuda/bin:/usr/local/bin:/usr/bin:/bin"
Environment="LD_LIBRARY_PATH=/usr/local/cuda/lib64"

[Install]
WantedBy=default.target
EOF
echo "Created ~/.config/systemd/user/jupyterlab.service"

echo ""
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
