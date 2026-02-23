@echo off
REM StarSound Setup - Install Dependencies
REM This script installs all required Python packages

setlocal enabledelayedexpansion

echo.
echo 🎵 StarSound - Dependency Installation
echo ===============================================
echo.
echo This script will install the required Python packages:
echo  • PyQt5 (GUI framework)
echo  • PyDub (audio processing)
echo  • Other dependencies
echo.

REM Try to find Python
set PYTHON_FOUND=0
set PYTHON_EXE=

REM Check 1: Python in system PATH
where python >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%i in ('where python') do set PYTHON_EXE=%%i
    set PYTHON_FOUND=1
    goto :check_pip
)

REM Check 2: Python installed via Microsoft Store
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    set PYTHON_EXE=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe
    set PYTHON_FOUND=1
    goto :check_pip
)

REM Check 3: Program Files
if exist "C:\Program Files\Python311\python.exe" (
    set PYTHON_EXE=C:\Program Files\Python311\python.exe
    set PYTHON_FOUND=1
    goto :check_pip
)

if exist "C:\Program Files\Python310\python.exe" (
    set PYTHON_EXE=C:\Program Files\Python310\python.exe
    set PYTHON_FOUND=1
    goto :check_pip
)

REM If Python not found
if !PYTHON_FOUND! equ 0 (
    echo ❌ ERROR: Python could not be found
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

:check_pip
echo ✓ Found Python: !PYTHON_EXE!
echo.

REM Check if pip is available
"!PYTHON_EXE!" -m pip --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ ERROR: pip is not available
    echo Please reinstall Python and make sure pip is included
    pause
    exit /b 1
)

echo Installing dependencies from requirements.txt...
echo.

REM Install from requirements.txt
"!PYTHON_EXE!" -m pip install --upgrade pip setuptools wheel

REM Look for requirements.txt in the current directory or parent directory
if exist "requirements.txt" (
    set REQUIREMENTS_FILE=requirements.txt
) else if exist "..\requirements.txt" (
    set REQUIREMENTS_FILE=..\requirements.txt
) else if exist "pygui\requirements.txt" (
    set REQUIREMENTS_FILE=pygui\requirements.txt
) else (
    echo ⚠️ requirements.txt not found, installing common dependencies...
    set REQUIREMENTS_FILE=
)

if defined REQUIREMENTS_FILE (
    echo Installing from: !REQUIREMENTS_FILE!
    "!PYTHON_EXE!" -m pip install -r "!REQUIREMENTS_FILE!"
) else (
    REM Fallback: install common packages manually
    echo Installing PyQt5...
    "!PYTHON_EXE!" -m pip install PyQt5
    echo Installing PyDub...
    "!PYTHON_EXE!" -m pip install pydub
)

if !errorlevel! neq 0 (
    echo.
    echo ❌ ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ All dependencies installed successfully!
echo.
pause
exit /b 0
