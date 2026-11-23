@echo off
setlocal
cd /d "%~dp0"

if not exist "scripts\dashboard.py" (
  echo Promptwise could not find scripts\dashboard.py.
  pause
  exit /b 1
)

where py >nul 2>nul
if not errorlevel 1 (
  py -3 "scripts\dashboard.py" serve
  if not errorlevel 1 exit /b 0
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 is required. Install Python, then double-click this launcher again.
  pause
  exit /b 1
)

python "scripts\dashboard.py" serve
if errorlevel 1 pause
