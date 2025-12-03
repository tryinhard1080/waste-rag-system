@echo off
REM Start the Email Warehouse RAG API

echo ================================================================================
echo Email Warehouse RAG API Starter
echo ================================================================================
echo.

REM Check if API key is already set
if "%GOOGLE_API_KEY%"=="" (
    echo ERROR: GOOGLE_API_KEY environment variable not set
    echo Please set it with: set GOOGLE_API_KEY=your_key
    echo.
    pause
    exit /b 1
)

REM Navigate to API directory
cd /d %~dp0

echo Starting Flask server...
echo API will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ================================================================================
echo.

python rag_api.py
