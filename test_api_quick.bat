@echo off
REM Test API endpoint directly using curl
echo ========================================
echo Testing Online Users API Endpoint
echo ========================================
echo.

set API_URL=https://appgacha.onrender.com/api/online-users

echo 🔗 Endpoint: %API_URL%
echo ⏳ Requesting...
echo.

curl -s --connect-timeout 10 %API_URL%

echo.
echo.
if %errorlevel% equ 0 (
    echo ✅ API responded!
) else (
    echo ❌ API timeout or error
)

echo.
pause
