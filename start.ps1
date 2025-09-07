# start.ps1 - PowerShell version for Windows
Write-Host "Starting Multi-MCP Platform..." -ForegroundColor Green

# Check if setup was run
if (-not (Test-Path "backend\.env")) {
    Write-Host "Error: Configuration not found. Please run setup.bat first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "backend\venv")) {
    Write-Host "Error: Python environment not found. Please run setup.bat first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Error: Node modules not found. Please run setup.bat first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Function to check if port is in use
function Test-Port {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $Port)
        $listener.Start()
        $listener.Stop()
        return $false
    }
    catch {
        return $true
    }
}

# Check if ports are in use
if (Test-Port 8000) {
    Write-Host "Error: Port 8000 is already in use. Please stop the service using that port." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (Test-Port 3000) {
    Write-Host "Error: Port 3000 is already in use. Please stop the service using that port." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Start backend
Write-Host "Starting backend server..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath "cmd" -ArgumentList "/k", "cd backend && call venv\Scripts\activate.bat && python -m uvicorn mcp_orchestrator:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Minimized -PassThru

# Wait for backend to start
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Test backend health
Write-Host "Checking backend health..." -ForegroundColor Yellow
$healthCheck = $false
for ($i = 1; $i -le 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "Backend is ready!" -ForegroundColor Green
            $healthCheck = $true
            break
        }
    }
    catch {
        Write-Host "Waiting for backend... ($i/10)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

if (-not $healthCheck) {
    Write-Host "Warning: Backend health check failed, but continuing..." -ForegroundColor Yellow
    Write-Host "Check the backend window for any error messages." -ForegroundColor Yellow
}

# Start frontend
Write-Host "Starting frontend server..." -ForegroundColor Yellow
$frontendProcess = Start-Process -FilePath "cmd" -ArgumentList "/k", "cd frontend && npm run dev" -WindowStyle Minimized -PassThru

# Wait for frontend to start
Write-Host "Waiting for frontend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

Write-Host ""
Write-Host "==================================" -ForegroundColor Green
Write-Host "Multi-MCP Platform Started!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Two new command windows have opened (minimized):" -ForegroundColor Yellow
Write-Host "  - Backend (PID: $($backendProcess.Id))" -ForegroundColor White
Write-Host "  - Frontend (PID: $($frontendProcess.Id))" -ForegroundColor White
Write-Host ""
Write-Host "To stop the servers:" -ForegroundColor Yellow
Write-Host "  - Close both command windows, or" -ForegroundColor White
Write-Host "  - Press Ctrl+C in each window, or" -ForegroundColor White
Write-Host "  - Run: stop.ps1" -ForegroundColor White
Write-Host ""

# Create stop script
$stopScript = @"
# stop.ps1 - Stop Multi-MCP Platform
Write-Host "Stopping Multi-MCP Platform..." -ForegroundColor Yellow

# Find and stop backend processes
Get-Process | Where-Object {`$_.ProcessName -eq "python" -and `$_.CommandLine -like "*uvicorn*mcp_orchestrator*"} | Stop-Process -Force
Get-Process | Where-Object {`$_.ProcessName -eq "cmd" -and `$_.CommandLine -like "*uvicorn*"} | Stop-Process -Force

# Find and stop frontend processes  
Get-Process | Where-Object {`$_.ProcessName -eq "node" -and `$_.CommandLine -like "*vite*"} | Stop-Process -Force
Get-Process | Where-Object {`$_.ProcessName -eq "cmd" -and `$_.CommandLine -like "*npm run dev*"} | Stop-Process -Force

Write-Host "Servers stopped." -ForegroundColor Green
"@

$stopScript | Out-File -FilePath "stop.ps1" -Encoding UTF8

Write-Host "Press any key to exit this setup window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

---
# Simple Windows Quick Start Guide
# README-WINDOWS.md

# Multi-MCP Platform - Windows Setup Guide

## Quick Start for Windows

### Prerequisites
- Python 3.8+ ([Download](https://www.python.org/downloads/))
- Node.js 16+ ([Download](https://nodejs.org/))

### Setup (First Time Only)

1. **Download and extract** the project files to a folder
2. **Open Command Prompt** in the project folder
3. **Run setup:**
   ```cmd
   setup.bat
   ```
4. **Edit configuration** with your API keys:
   ```cmd
   notepad backend\.env
   ```

### Start Application

**Option 1: Batch File (Simple)**
```cmd
start.bat
```

**Option 2: PowerShell (Recommended)**
```powershell
powershell -ExecutionPolicy Bypass -File start.ps1
```

**Option 3: Manual (Step by Step)**
```cmd
REM Terminal 1: Start Backend
start-backend.bat

REM Terminal 2: Start Frontend  
start-frontend.bat
```

### Access
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Stop Application
- Close the command windows, or
- Run: `stop.ps1` (if using PowerShell version)

### Troubleshooting

**Port Already in Use:**
```cmd
REM Find what's using port 8000
netstat -ano | findstr :8000

REM Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Python/Node Not Found:**
- Make sure Python and Node.js are installed
- Restart Command Prompt after installation
- Add to PATH if needed

**Permission Issues:**
- Run Command Prompt as Administrator
- For PowerShell: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`