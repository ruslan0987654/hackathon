@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ============================================
echo  SOCAR ML servisi: ilk quraşdırma
echo ============================================
where python >nul 2>nul
if errorlevel 1 (
  echo [XETA] Python tapilmadi. https://www.python.org/downloads/ saytindan Python 3.11 ve ya 3.12 yukleyin.
  echo        Quraşdırarken "Add python.exe to PATH" qutusunu MUTLEQ isaretleyin.
  pause & exit /b 1
)
if not exist venv (
  echo [1/4] Virtual muhit yaradilir...
  python -m venv venv || (echo [XETA] venv yaradila bilmedi & pause & exit /b 1)
)
call venv\Scripts\activate.bat
echo [2/4] Kitabxanalar yuklenir (internet lazimdir, 2-5 deqiqe)...
python -m pip install --upgrade pip
pip install -r requirements.txt || (echo [XETA] Kitabxanalar yuklenmedi & pause & exit /b 1)
echo [3/4] Konfiqurasiya (.env) hazirlanir...
python scripts\init_env.py
echo [4/4] Modeller oyredilir (sintetik data, 1-3 deqiqe)...
python -m training.train_all || (echo [XETA] Telim ugursuz oldu & pause & exit /b 1)
echo.
echo HAZIRDIR. Servisi baslatmaq ucun run.bat faylini isledin.
pause
