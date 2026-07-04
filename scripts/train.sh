#!/bin/bash

# --- 1. Conda 激活 ---
# 自动获取 conda 的安装路径并初始化
CONDA_PATH=$(conda info --base)
source "$CONDA_PATH/etc/profile.d/conda.sh"
conda activate deskpet

# --- 2. 环境变量设置 ---
export PYTHONNOUSERSITE=1
export CUDA_VISIBLE_DEVICES=1  # 请根据 nvidia-smi 确认显卡编号

# --- 3. 启动训练 ---
# 直接在根目录运行即可
llamafactory-cli train configs/shu_sft.yaml