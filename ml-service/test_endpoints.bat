@echo off
chcp 65001 >nul
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo Servis ayri pencerede isleyirse, endpoint-ler yoxlanilir...
python scripts\test_endpoints.py
pause
