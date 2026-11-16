@echo off
chcp 65001 >nul
title Global Trade Assistant

REM ====== 改这里：你的 API Key ======
set LLM_BASE_URL=https://api.siliconflow.cn/v1
set LLM_API_KEY=sk-aaqtcsdmfnrgryqviakmqqqalscwobzduuykpvhgbdskfhkv
set LLM_MODEL=deepseek-ai/DeepSeek-V3

REM ====== 启动 Streamlit ======
cd /d "%~dp0"
echo.
echo ============================================
echo   Global Trade Assistant - 跨境物流助手
echo   浏览器将自动打开 http://localhost:8501
echo   关掉这个窗口就是停止服务
echo ============================================
echo.

REM ====== 后台启动，等几秒后自动打开浏览器 ======
start /b python -m streamlit run chatbot/app.py --server.headless true
timeout /t 5 /nobreak >nul
start http://localhost:8501

REM ====== 保持窗口，方便看日志 ======
echo.
echo 服务已启动。如需停止，直接关闭本窗口。
echo.
pause
