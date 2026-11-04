@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist venv\Scripts\activate.bat (echo Evvelce setup.bat isledin. & pause & exit /b 1)
call venv\Scripts\activate.bat
echo Servis baslayir: http://127.0.0.1:8000  (API sənədləri: http://127.0.0.1:8000/docs)
echo Dayandirmaq ucun Ctrl+C basin.
uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
