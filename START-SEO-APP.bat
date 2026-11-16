@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Install Python 3.10 or newer, then run this file again.
    pause
    exit /b 1
  )
)

set "PYTHON=%CD%\.venv\Scripts\python.exe"
"%PYTHON%" -c "import flask, googleapiclient, google_auth_oauthlib" >nul 2>nul
if errorlevel 1 (
  echo Installing the app's Python packages...
  "%PYTHON%" -m pip install --upgrade pip
  if errorlevel 1 goto :failed
  "%PYTHON%" -m pip install -r requirements.txt
  if errorlevel 1 goto :failed
)

start "" http://127.0.0.1:5000
echo Starting SEO app. Keep this window open; press Ctrl+C to stop.
"%PYTHON%" dashboard\app.py
goto :eof

:failed
echo Could not install Python packages. Check your internet connection and try again.
pause
exit /b 1
