@echo off
chcp 65001 >nul
cls
echo.
echo ========================================
echo  Testing MongoDB Connection
echo ========================================
echo.

cd /d d:\appNguyenHoangDang

REM Try different Python commands
echo Trying to find Python...
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo Found python command
    python test_mongodb.py
    goto end
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    echo Found py launcher
    py test_mongodb.py
    goto end
)

where python3 >nul 2>&1
if %errorlevel% equ 0 (
    echo Found python3 command
    python3 test_mongodb.py
    goto end
)

echo.
echo ❌ Python not found in PATH!
echo.
echo Try one of these:
echo 1. Search for Python in C:\ drive
echo 2. Add Python to PATH (Windows Settings ^> Environment Variables)
echo.
pause

:end
echo.
echo Press any key to exit...
pause
