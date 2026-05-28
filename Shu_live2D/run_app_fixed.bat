@echo off
chcp 65001 > nul
echo ====================================================
echo 🌾 正在清理残留、注入环境变量并启动明日方舟桌宠...
echo ====================================================

:: 1. 自动切换到当前目录
cd /d "%~dp0"

:: 2. 【核心防卡死】启动前，强制杀掉可能残留的旧后台进程，确保全新启动
taskkill /F /IM "Mini Live2D AI.exe" >nul 2>&1
taskkill /F /IM backend.exe >nul 2>&1

:: 3. 向系统内存强行写入环境变量，防止 .env 找不到
set DEEPSEEK_API_KEY=
set DEEPSEEK_BASE_URL=

set DASHSCOPE_API_KEY=
set DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

:: 4. 【核心修复】在后台静默启动 backend.exe，并将输出重定向，完美绕过 isatty 崩溃 Bug [1]
echo 正在后台修复并启动中转服务...
start /b "" backend.exe > backend.log 2>&1

:: 5. 启动前端主程序
echo 正在拉起 Live2D 画面...
start "" "Mini Live2D AI.exe"

echo ====================================================
echo ✅ 启动指令已全部发送！本窗口将在 3 秒后自动关闭。
echo ====================================================
ping -n 4 127.0.0.1 >nul