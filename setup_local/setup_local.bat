@echo off
echo ====================================================
echo Start configuring [Shu] Local Inference Env...
echo ====================================================

:: 1. Create Conda Env
echo 1. Creating Python 3.11 environment...
call conda create -n pet_local python=3.11 -y

echo 2. Activating environment...
call conda activate pet_local

:: 2. Set Pip Mirror
echo 3. Setting Tsinghua Pip Mirror...
call pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

:: 3. Install PyTorch with high timeout limit
echo 4. Installing PyTorch 2.4 (CUDA 12.1)...
call pip install --default-timeout=1000 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

:: 4. Install other inference dependencies
echo 5. Installing inference packages...
call pip install transformers datasets accelerate peft bitsandbytes modelscope fastapi uvicorn openai

echo ====================================================
echo Environment setup completed!
echo ====================================================
pause