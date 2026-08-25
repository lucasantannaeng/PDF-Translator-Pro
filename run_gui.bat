@echo off
chcp 65001 > nul
title PDF-Translator-Pro - Web Dashboard

echo ===================================================
echo   Iniciando PDF-Translator-Pro Web Dashboard...
echo ===================================================
echo.

cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo Abrindo interface web no seu navegador padrao...
streamlit run gui\app.py --server.port 8501 --server.headless false

pause
