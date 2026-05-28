@echo off
chcp 65001 > nul
echo ====================================================
echo 🌾 正在启动 [黍-Shu] 本地大模型推理后端服务...
echo ====================================================

:: 1. 自动切换到项目根目录
cd /d "%~dp0"

:: 2. 绕过 conda 命令，直接调用环境里的 python 启动 uvicorn
:: 这样 100% 避免了 Windows 弹窗询问 .sh 打开方式的问题！
echo 正在加载本地显卡，请稍候...
"D:\Anaconda\envs\pet_local\python.exe" -m uvicorn src.main:app --host 127.0.0.1 --port 18080

pause