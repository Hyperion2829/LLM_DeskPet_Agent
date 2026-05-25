@echo off
chcp 65001 > nul

echo ====================================================
echo Start configuring [Shu] Local Inference Env (v5.0)
echo ====================================================

:: 1. 创建虚拟环境
echo 1. Creating Python 3.11 environment...
call conda create -n pet_local python=3.11 -y

:: 2. 使用 conda run 静默配置 pip 镜像源
echo 2. Configuring Pip Mirror...
call conda run -n pet_local pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

:: 3. 使用 conda run 隔离安装 PyTorch
echo 3. Installing PyTorch 2.5 (CUDA 12.1)...
call conda run -n pet_local pip install --default-timeout=1000 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

:: 4. 使用 conda run 隔离安装其余推理包
echo 4. Installing inference packages (transformers, peft, modelscope, etc.)...
call conda run -n pet_local pip install transformers datasets accelerate peft bitsandbytes modelscope fastapi uvicorn openai

echo ====================================================
echo ✅ Environment setup completed successfully!
echo To start using, please run: conda activate pet_local
echo ====================================================
pause