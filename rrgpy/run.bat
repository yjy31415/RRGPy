@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting Streamlit... http://localhost:8501
echo Press Ctrl+C to stop
echo.
python -m streamlit run app.py
pause
