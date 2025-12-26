@echo off
:: Fetal MRI Reconstruction Server Startup Script for Windows
:: Double-click this file to start the server

title Fetal MRI Reconstruction Server
color 0A

echo ==========================================
echo   Fetal MRI Reconstruction Server
echo ==========================================
echo.

:: Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [!] Docker is not running. Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo     Waiting for Docker to start (this may take a minute)...
    :wait_docker
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if errorlevel 1 goto wait_docker
    echo [OK] Docker is ready
) else (
    echo [OK] Docker is running
)

echo.

:: Navigate to project directory
cd /d "%~dp0.."
echo [OK] Working directory: %cd%

echo.
echo Starting web application...
docker-compose -f docker-compose.webapp.yml up -d

if errorlevel 1 (
    echo [ERROR] Failed to start web application
    pause
    exit /b 1
)

echo [OK] Web application started
echo.

:: Check if cloudflared is installed
where cloudflared >nul 2>&1
if errorlevel 1 (
    echo [!] cloudflared not found.
    echo     Install it with: winget install Cloudflare.cloudflared
    echo.
    echo     The web app is running locally at: http://localhost:8501
    echo.
    pause
    exit /b 0
)

:: Check if tunnel config exists
if exist "%USERPROFILE%\.cloudflared\config.yml" (
    echo Starting Cloudflare Tunnel...
    echo.
    echo ==========================================
    echo   Server is starting...
    echo   Local:  http://localhost:8501
    echo   Remote: Check your Cloudflare domain
    echo ==========================================
    echo.
    echo Press Ctrl+C to stop the tunnel
    echo.
    cloudflared tunnel run
) else (
    echo [!] Cloudflare Tunnel not configured.
    echo     Run setup-tunnel.ps1 first for remote access.
    echo.
    echo     The web app is running locally at: http://localhost:8501
    echo.
    echo Press any key to open the local app in browser...
    pause >nul
    start http://localhost:8501
)
