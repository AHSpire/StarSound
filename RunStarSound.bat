@echo off
REM StarSound Music Mod Generator - Python Launcher
REM This script finds and runs StarSound even if Python isn't in the system PATH

setlocal enabledelayedexpansion

echo 🎵 StarSound - Music Mod Generator
echo.

REM Try to find Python in common locations
set PYTHON_FOUND=0
set PYTHON_EXE=

REM Check 1: Python in system PATH (easiest)
where python >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%i in ('where python') do set PYTHON_EXE=%%i
    set PYTHON_FOUND=1
    echo ✓ Found Python in PATH: !PYTHON_EXE!
    goto :run_starsound
)

REM Check 2: Python installed via Microsoft Store
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    set PYTHON_EXE=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe
    set PYTHON_FOUND=1
    echo ✓ Found Python (Microsoft Store): !PYTHON_EXE!
    goto :run_starsound
)

REM Check 3: Python installed in Program Files
if exist "C:\Program Files\Python311\python.exe" (
    set PYTHON_EXE=C:\Program Files\Python311\python.exe
    set PYTHON_FOUND=1
    echo ✓ Found Python (Program Files): !PYTHON_EXE!
    goto :run_starsound
)

if exist "C:\Program Files\Python310\python.exe" (
    set PYTHON_EXE=C:\Program Files\Python310\python.exe
    set PYTHON_FOUND=1
    echo ✓ Found Python (Program Files): !PYTHON_EXE!
    goto :run_starsound
)

if exist "C:\Program Files (x86)\Python311\python.exe" (
    set PYTHON_EXE=C:\Program Files (x86)\Python311\python.exe
    set PYTHON_FOUND=1
    echo ✓ Found Python (Program Files x86): !PYTHON_EXE!
    goto :run_starsound
)

if exist "C:\Program Files (x86)\Python310\python.exe" (
    set PYTHON_EXE=C:\Program Files (x86)\Python310\python.exe
    set PYTHON_FOUND=1
    echo ✓ Found Python (Program Files x86): !PYTHON_EXE!
    goto :run_starsound
)

REM Check 4: Python installed via Anaconda
if exist "%USERPROFILE%\Anaconda3\python.exe" (
    set PYTHON_EXE=%USERPROFILE%\Anaconda3\python.exe
    set PYTHON_FOUND=1
    echo ✓ Found Python (Anaconda): !PYTHON_EXE!
    goto :run_starsound
)

REM Check 5: Python installed via Miniconda
if exist "%USERPROFILE%\Miniconda3\python.exe" (
    set PYTHON_EXE=%USERPROFILE%\Miniconda3\python.exe
    set PYTHON_FOUND=1
    echo ✓ Found Python (Miniconda): !PYTHON_EXE!
    goto :run_starsound
)

REM Check 6: Virtual environment in this project
if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
    set PYTHON_FOUND=1
    echo ✓ Found Python (Virtual environment): !PYTHON_EXE!
    goto :run_starsound
)

REM If we get here, Python wasn't found
if !PYTHON_FOUND! equ 0 (
    echo.
    echo ❌ ERROR: Python could not be found on this computer
    echo.
    echo 📋 To fix this, please:
    echo    1. Install Python from: https://www.python.org/downloads/
    echo    2. During installation, CHECK the box: "Add Python to PATH"
    echo    3. Then run this script again
    echo.
    echo 💡 Alternatively, if Python IS installed but not in PATH:
    echo    • Copy your Python.exe path (e.g., C:\Program Files\Python311\python.exe)
    echo    • Edit this script and add it to the PYTHON_EXE variable
    echo.
    pause
    exit /b 1
)

REM Run StarSound with the Python executable we found
:run_starsound
echo.
echo Starting StarSound...
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Run the app with the found Python executable
"!PYTHON_EXE!" "!SCRIPT_DIR!pygui\starsound_gui.py"

REM If the app exits with an error, show it
if !errorlevel! neq 0 (
    echo.
    echo ❌ StarSound encountered an error and exited
    echo Error code: !errorlevel!
    echo.
    pause
    exit /b !errorlevel!
)

exit /b 0
