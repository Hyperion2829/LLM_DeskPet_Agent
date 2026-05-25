#!/bin/bash

export PYTHONNOUSERSITE=1
set -e

echo "===================================================="
echo " [黍-Shu] 环境一键配置"
echo "===================================================="

# 1. 彻底重建 Conda 环境
CONDA_ENV_NAME="deskpet"
echo "正在重建 Conda 环境: $CONDA_ENV_NAME ..."
conda deactivate || true
conda remove -n $CONDA_ENV_NAME --all -y || true
conda create -n $CONDA_ENV_NAME python=3.11 -y

# 激活环境
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate $CONDA_ENV_NAME

# 2. 设置国内镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 安装稳定版 PyTorch (CUDA 12.1)
echo "正在安装稳定版 PyTorch 2.4.0 (cu121)..."
pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu121 --no-cache-dir

# 4. 重新安装 LLaMA-Factory
# 逻辑：如果文件夹存在，先清理残留再重新 install
if [ -d "LLaMA-Factory" ]; then
    echo "检测到现有 LLaMA-Factory 文件夹，正在清理旧残留并重新安装..."
    cd LLaMA-Factory
    rm -rf build/ dist/ *.egg-info || true
    # 重新在当前环境下建立软链接安装
    pip install -e . --no-cache-dir
    cd ..
else
    echo "未检测到文件夹，正在克隆 LLaMA-Factory..."
    git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
    cd LLaMA-Factory
    pip install -e . --no-cache-dir
    cd ..
fi

# 5. 手动安装其他必备包 (确保版本对齐)
echo "正在安装核心算法依赖包..."
pip install modelscope bitsandbytes datasets accelerate peft trl rouge-chinese nltk jieba scikit-learn pandas tqdm vllm fastapi uvicorn openai --no-cache-dir

# 6. 最后清理（强迫症友好）
rm -rf ~/.local/lib/python3.11/site-packages/flash_attn* || true

echo "===================================================="
echo "✅ 环境配置完成！"
echo "===================================================="