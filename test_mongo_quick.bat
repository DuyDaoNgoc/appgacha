@echo off
cd /d D:\appNguyenHoangDang
echo Running MongoDB Connection Test (5s timeout)...
echo.
python test_mongo_fast.py
if errorlevel 1 (
    echo.
    echo Trying with python3...
    python3 test_mongo_fast.py
)
echo.
pause
