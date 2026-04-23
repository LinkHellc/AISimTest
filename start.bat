@echo off
chcp 65001 >nul

cd /d "%~dp0"

echo ========================================
echo   AISimTest Startup Script
echo ========================================

echo Starting services...
echo.

start /b cmd /c "cd backend && python -m uvicorn main:app --reload --port 8000"
echo [OK] Backend starting on http://localhost:8000

start /b cmd /c "cd frontend && npm run dev"
echo [OK] Frontend starting on http://localhost:5173

timeout /t 5 /nobreak >nul

start http://localhost:5173

echo.
echo ========================================
echo   Startup Complete
echo   Frontend: http://localhost:5173
echo   Backend: http://localhost:8000
echo ========================================
echo Press any key to exit...
pause >nul