@echo off
chcp 65001 >nul
cd /d D:\appNguyenHoangDang

echo Test kết nối MongoDB...
echo.

"C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe" test_mongo_fast.py

pause
