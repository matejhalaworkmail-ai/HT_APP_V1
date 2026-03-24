@echo off
title TZ Databaze - Heat Treatment App
echo.
echo  ==========================================
echo    TZ Databaze - Heat Treatment Database
echo  ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python neni nainstalovan!
    echo  Stahni Python z https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install dependencies if needed
echo  Kontrola zavislosti...
pip install -r requirements.txt --quiet

echo.
echo  Spoustim aplikaci na http://localhost:5000
echo  Pro ukonceni stiskni Ctrl+C
echo.

REM Open browser after short delay
start "" cmd /c "timeout /t 2 >nul && start http://localhost:5000"

REM Start Flask
python app.py

pause
