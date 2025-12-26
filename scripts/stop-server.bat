@echo off
:: Stop Fetal MRI Reconstruction Server
:: Double-click this file to stop the server

title Stopping Fetal MRI Server
color 0E

echo ==========================================
echo   Stopping Fetal MRI Server
echo ==========================================
echo.

cd /d "%~dp0.."

echo Stopping web application...
docker-compose -f docker-compose.webapp.yml down

echo.
echo [OK] Server stopped
echo.
pause
