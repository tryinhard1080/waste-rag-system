@echo off
echo ============================================================
echo WASTE Master Brain - Semantic RAG API
echo ============================================================
echo.

REM Check if GOOGLE_API_KEY is set
if "%GOOGLE_API_KEY%"=="" (
    echo ERROR: GOOGLE_API_KEY environment variable not set
    echo.
    echo Set it with:
    echo   set GOOGLE_API_KEY=your_api_key_here
    echo.
    echo Get your API key at: https://aistudio.google.com/app/apikey
    echo.
    pause
    exit /b 1
)

echo API Key: Set
echo Starting server on http://localhost:5000
echo.

REM Run the semantic API
python "%~dp0semantic_api.py"

pause
