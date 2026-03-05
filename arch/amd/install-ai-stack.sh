#!/bin/bash
# AI Stack Installation Script for AMD Strix Halo (gfx1151)
# Headless Claude Code box with remote access support
# Run with: bash ~/install-ai-stack.sh

set -e

echo "=============================================="
echo "AI Stack Installation for AMD Strix Halo"
echo "Headless/Remote Configuration"
echo "=============================================="
echo ""

# Add ROCm to PATH for this session
export PATH="/opt/rocm/bin:$PATH"

echo "=== Phase 1: Installing ROCm Stack ==="
sudo pacman -S --needed rocm-hip-sdk rocm-opencl-sdk hip-runtime-amd \
    hipblas hipblaslt miopen-hip rocblas rocfft rccl roctracer

echo ""
echo "Verifying ROCm installation..."
/opt/rocm/bin/rocminfo | grep -E "Name:|Marketing|gfx" | head -10 || echo "rocminfo check skipped"

echo ""
echo "=== Phase 2: Installing tmux and mosh for persistent/remote sessions ==="
sudo pacman -S --needed tmux mosh

echo ""
echo "=== Phase 3: Installing Miniforge/Mamba ==="
if [ -d "$HOME/miniforge3" ]; then
    echo "Miniforge already installed at ~/miniforge3"
else
    curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
    bash Miniforge3-Linux-x86_64.sh -b -p "$HOME/miniforge3"
    rm Miniforge3-Linux-x86_64.sh
fi

# Initialize mamba (mamba 2.x uses 'shell init' instead of 'init')
export MAMBA_ROOT_PREFIX="$HOME/miniforge3"
"$HOME/miniforge3/bin/mamba" shell init -s bash -p "$HOME/miniforge3" 2>/dev/null || true
source "$HOME/miniforge3/etc/profile.d/mamba.sh"

echo ""
echo "=== Phase 4: Creating AI Environment ==="
if mamba env list | grep -q "^ai "; then
    echo "Environment 'ai' already exists"
else
    mamba create -n ai python=3.12 -y
fi
mamba activate ai

echo ""
echo "=== Phase 5: Installing PyTorch with ROCm ==="
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2

echo ""
echo "=== Phase 6: Installing HuggingFace Ecosystem ==="
pip install transformers datasets tokenizers safetensors
pip install accelerate
pip install peft
pip install evaluate huggingface_hub
pip install optimum

echo ""
echo "=== Phase 7: Installing DeepSpeed ==="
pip install deepspeed

echo ""
echo "=== Phase 8: Installing JupyterLab ==="
pip install jupyterlab jupyterlab-lsp ipywidgets
pip install ipykernel
python -m ipykernel install --user --name ai --display-name "Python (AI/ROCm)"

echo ""
echo "=== Phase 9: Installing Additional Packages ==="
pip install numpy scipy pandas matplotlib seaborn
pip install scikit-learn tensorboard wandb

echo ""
echo "=============================================="
echo "Installation Complete!"
echo "=============================================="
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Run the post-install script to configure headless services:"
echo "   bash ~/setup-headless.sh"
echo ""
echo "2. Set JupyterLab password:"
echo "   source ~/.config/ai-env.sh && jupyter lab password"
echo ""
echo "3. Start a new shell or run:"
echo "   source ~/.bash_profile"
echo ""
echo "The AI environment will auto-activate on SSH login."
echo "JupyterLab will be available at http://<ip>:8888"
