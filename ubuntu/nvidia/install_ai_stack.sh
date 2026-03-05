#!/bin/bash
# AI Stack Installation Script for Ubuntu 22.04 with NVIDIA GPU
# Headless Claude Code box with remote access support
# Assumes NVIDIA drivers are already installed
# Run with: bash ~/install_ai_stack.sh

set -e

echo "=============================================="
echo "AI Stack Installation for NVIDIA GPU"
echo "Ubuntu 22.04 LTS - Headless/Remote Configuration"
echo "=============================================="
echo ""

# Add CUDA to PATH for this session
export PATH="/usr/local/cuda/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}"

echo "=== Phase 1: Installing CUDA Toolkit 12.8 ==="
echo "Note: NVIDIA drivers are assumed to be already installed."
echo ""

# Verify NVIDIA drivers are present
if ! command -v nvidia-smi &>/dev/null; then
    echo "ERROR: nvidia-smi not found. Please install NVIDIA drivers first."
    exit 1
fi
echo "NVIDIA driver detected:"
nvidia-smi --query-gpu=driver_version,name --format=csv,noheader
echo ""

# Add NVIDIA CUDA repository
if ! dpkg -l cuda-keyring 2>/dev/null | grep -q "^ii"; then
    wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
    sudo dpkg -i cuda-keyring_1.1-1_all.deb
    rm cuda-keyring_1.1-1_all.deb
    sudo apt-get update
fi

# Install CUDA toolkit (not drivers)
sudo apt-get install -y cuda-toolkit-12-8

# Install cuDNN and NCCL
sudo apt-get install -y libcudnn9-cuda-12
sudo apt-get install -y libnccl2 libnccl-dev

echo ""
echo "Verifying CUDA installation..."
nvcc --version || echo "nvcc check skipped"
nvidia-smi | head -5 || echo "nvidia-smi check skipped"

echo ""
echo "=== Phase 2: Installing build tools and remote session utilities ==="
sudo apt-get install -y build-essential tmux mosh

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
echo "=== Phase 5: Installing PyTorch with CUDA ==="
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

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
python -m ipykernel install --user --name ai --display-name "Python (AI/CUDA)"

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
echo "   bash ~/setup_headless.sh"
echo ""
echo "2. Set JupyterLab password:"
echo "   source ~/.config/ai-env.sh && jupyter lab password"
echo ""
echo "3. Start a new shell or run:"
echo "   source ~/.bashrc"
echo ""
echo "The AI environment will auto-activate on SSH login."
echo "JupyterLab will be available at http://<ip>:8888"
