@echo off
cd /d "%~dp0"
echo ============================================
echo   板块 RRG + 扩散度分析系统
echo ============================================
echo.
echo 正在启动 Streamlit 应用...
echo 浏览器将自动打开 http://localhost:8501
echo 按 Ctrl+C 可停止
echo.
streamlit run app.py
pause
