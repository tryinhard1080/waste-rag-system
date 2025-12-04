@echo off
echo ============================================================
echo WASTE Master Brain - Build Semantic Index
echo ============================================================
echo.
echo This will create embeddings for all 1,186+ emails in the warehouse.
echo This process takes 5-10 minutes (first time only).
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
echo.
echo Building semantic embeddings...
echo.

cd /d "%~dp0scripts"
python semantic_rag.py --build-embeddings

echo.
echo ============================================================
echo Done! You can now run queries with semantic search.
echo.
echo Start the API:
echo   api\start_semantic_api.bat
echo.
echo Or query directly:
echo   python scripts/semantic_rag.py --query "contamination issues"
echo ============================================================
pause
