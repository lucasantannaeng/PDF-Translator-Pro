@echo off
chcp 65001 > nul
title PDF-Translator-Pro - Terminal CLI

echo ===================================================
echo   PDF-Translator-Pro - CLI Interativo
echo ===================================================
echo.

cd /d "%~dp0"
call .venv\Scripts\activate.bat

python cli.py list
echo.
echo Comandos uteis:
echo   python cli.py analyze "nome_do_arquivo.pdf"
echo   python cli.py translate "nome_do_arquivo.pdf" --pages 1-10
echo   python cli.py batch
echo   python cli.py test-api
echo.

cmd /k
