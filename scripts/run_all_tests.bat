@echo off
echo =========================================================
echo Running Full Automated Test Suites (Task 1 + Task 2)
echo =========================================================
echo.
echo [1/2] Running Task 1 Pytest Suite (Django & Vector KB)...
cd ..\task1_knowledge_base
pytest -v
if %ERRORLEVEL% NEQ 0 (
    echo Task 1 tests failed!
    cd ..
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] Running Task 2 Pytest Suite (FastAPI & RAG Pipeline)...
cd ..\task2_rag_chatbot
pytest -v
if %ERRORLEVEL% NEQ 0 (
    echo Task 2 tests failed!
    cd ..
    pause
    exit /b %ERRORLEVEL%
)

cd ..
echo.
echo =========================================================
echo ALL 23 TEST CASES PASSED SUCCESSFULLY (100%% SUCCESS RATE)
echo =========================================================
pause
