@echo off
REM Regenerate biome_tracks.json from Starbound unpacked data
REM This is a convenience batch file for Windows

setlocal enabledelayedexpansion

REM Paths (adjust if needed)
set STARBOUND_PATH=c:\Users\Stephanie\OneDrive\Documents\Original Unpacked Starbound
set OUTPUT_FILE=c:\Projects\StarSound\pygui\vanilla_tracks\biome_tracks.json
set SCRIPT_PATH=c:\Projects\StarSound\scripts\regenerate_biome_tracks.py

echo.
echo ========================================
echo  Regenerate StarSound Biome Tracks
echo ========================================
echo.

if not exist "%STARBOUND_PATH%" (
    echo ERROR: Starbound path not found:
    echo   %STARBOUND_PATH%
    echo.
    echo Please update the STARBOUND_PATH in this batch file.
    pause
    exit /b 1
)

echo Regenerating biome_tracks.json from Starbound data...
echo.

python "%SCRIPT_PATH%" "%STARBOUND_PATH%" "%OUTPUT_FILE%"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS: biome_tracks.json regenerated!
    echo ========================================
    echo Location: %OUTPUT_FILE%
    echo.
    pause
) else (
    echo.
    echo ERROR: Regeneration failed. Exit code: %errorlevel%
    pause
    exit /b %errorlevel%
)
