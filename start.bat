@echo off
echo Starting Multi-MCP Platform...

REM Check if setup was run
if not exist backend\.env (
    echo Error: Configuration not found. Please run setup.bat first.
    pause
    exit /b 1
)

if not exist backend\venv (
    echo Error: Python environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

if not exist frontend\node_modules (
    echo Error: Node modules not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Check if ports are in use (Windows)
netstat -an | findstr ":8000" >nul
if not errorlevel 1 (
    echo Error: Port 8000 is already in use. Please stop the service using that port.
    pause
    exit /b 1
)

netstat -an | findstr ":3000" >nul
if not errorlevel 1 (
    echo Error: Port 3000 is already in use. Please stop the service using that port.
    pause
    exit /b 1
)

REM Start backend in new window
echo Starting backend server...
start "Multi-MCP Backend" /min cmd /k "cd backend && call venv\Scripts\activate.bat && python -m uvicorn mcp_orchestrator:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to start
echo Waiting for backend to initialize...
timeout /t 8 /nobreak >nul

REM Test backend health
echo Checking backend health...
for /L %%i in (1,1,10) do (
    curl -s http://localhost:8000/api/health >nul 2>&1
    if not errorlevel 1 (
        echo Backend is ready!
        goto :backend_ready
    )
    echo Waiting for backend... (%%i/10)
    timeout /t 2 /nobreak >nul
)

echo Warning: Backend health check failed, but continuing...
echo Check the backend window for any error messages.

:backend_ready

REM Start frontend in new window
echo Starting frontend server...
start "Multi-MCP Frontend" /min cmd /k "cd frontend && npm run dev"

REM Wait for frontend to start
echo Waiting for frontend to initialize...
timeout /t 8 /nobreak >nul

echo.
echo ==================================
echo Multi-MCP Platform Started!
echo ==================================
echo.
echo Access URLs:
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo Two new command windows have opened:
echo   - Backend (minimized)
echo   - Frontend (minimized)
echo.
echo To stop the servers:
echo   - Close both command windows, or
echo   - Press Ctrl+C in each window
echo.
echo Press any key to exit this setup window...
pause >nul