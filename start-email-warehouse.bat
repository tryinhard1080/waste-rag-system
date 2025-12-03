@echo off
REM Email Warehouse - All-in-One Startup Script
REM This launches both the RAG API and Dashboard servers

echo ================================================================================
echo Starting Email Warehouse System
echo ================================================================================
echo.

cd /d %~dp0

REM Check if API key is set
if "%GOOGLE_API_KEY%"=="" (
    echo ERROR: GOOGLE_API_KEY environment variable not set
    echo Please set it with: set GOOGLE_API_KEY=your_key
    echo.
    pause
    exit /b 1
)

REM Start RAG API in new window
echo Starting RAG API Server (port 5000)...
start "Email RAG API" powershell -NoExit -Command "cd '%~dp0api'; $env:GOOGLE_API_KEY='%GOOGLE_API_KEY%'; python rag_api.py"

REM Wait for API to start
timeout /t 3 /nobreak >nul

REM Start Dashboard Server in new window (from project root for proper file access)
echo Starting Dashboard Server (port 8000)...
start "Dashboard Server" powershell -NoExit -Command "cd '%~dp0'; python -m http.server 8000"

REM Wait for dashboard to start
timeout /t 2 /nobreak >nul

REM Open dashboard in browser
echo Opening dashboard in browser...
start http://localhost:8000/dashboard-v2/index.html

echo.
echo ================================================================================
echo Email Warehouse is running!
echo ================================================================================
echo.
echo RAG API Server:     http://localhost:5000
echo Dashboard:          http://localhost:8000
echo.
echo Two PowerShell windows have opened:
echo   1. Email RAG API - Keep this running for AI queries
echo   2. Dashboard Server - Keep this running to view the dashboard
echo.
echo To stop: Close both PowerShell windows
echo.
echo ================================================================================
pause
