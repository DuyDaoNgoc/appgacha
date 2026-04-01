@echo off
chcp 65001 >nul
cls
echo.
echo ========================================
echo  Installing Python Dependencies
echo ========================================
echo.

cd /d d:\appNguyenHoangDang

echo Installing pymongo and python-dotenv...
C:\Python313\python.exe -m pip install pymongo python-dotenv

if %errorlevel% equ 0 (
    echo.
    echo ✅ Dependencies installed! Running test...
    echo ========================================
    echo.

    C:\Python313\python.exe test_mongodb.py
) else (
    echo ❌ Installation failed!
)

echo.
pause
