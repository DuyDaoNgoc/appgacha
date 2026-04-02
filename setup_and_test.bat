@echo off
cd /d D:\appNguyenHoangDang

echo ========================================
echo Installing Dependencies + Testing MongoDB
echo ========================================
echo.

echo 📦 Installing pymongo and python-dotenv...
"C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe" -m pip install -q pymongo python-dotenv

echo.
echo 🔗 Testing MongoDB Connection...
echo.

"C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe" test_mongo_fast.py

echo.
pause
