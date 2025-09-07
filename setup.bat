@echo off
echo Setting up Multi-MCP Platform for Local Development (Windows)
echo ============================================================

REM Create directories
echo Creating project structure...
if not exist backend mkdir backend
if not exist mcps mkdir mcps
if not exist frontend mkdir frontend
if not exist frontend\src mkdir frontend\src

REM Backend setup
echo 1. Setting up Python backend...
cd backend

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo    Using Python:
python --version

REM Create virtual environment
echo    Creating virtual environment...
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo    Upgrading pip...
python -m pip install --upgrade pip

REM Create requirements.txt if it doesn't exist
if not exist requirements.txt (
    echo Creating requirements.txt...
    echo fastapi> requirements.txt
    echo uvicorn[standard]>> requirements.txt
    echo pydantic>> requirements.txt
    echo python-dotenv>> requirements.txt
    echo requests>> requirements.txt
    echo agno>> requirements.txt
    echo mcp>> requirements.txt
    echo python-multipart>> requirements.txt
    echo openai>> requirements.txt
    echo uv>> requirements.txt
)

REM Install dependencies
echo    Installing Python dependencies...
pip install -r requirements.txt

echo    - Virtual environment created
echo    - Dependencies installed

cd ..

REM Frontend setup
echo 2. Setting up React frontend...
cd frontend

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js not found. Please install Node.js 16+ first.
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)

echo    Using Node.js:
node --version

REM Create package.json if it doesn't exist
if not exist package.json (
    echo Creating package.json...
    echo ^{> package.json
    echo   "name": "multi-mcp-frontend",>> package.json
    echo   "version": "1.0.0",>> package.json
    echo   "description": "Multi-MCP Enterprise Integration Frontend",>> package.json
    echo   "scripts": ^{>> package.json
    echo     "dev": "vite --host 0.0.0.0 --port 3000",>> package.json
    echo     "build": "vite build",>> package.json
    echo     "preview": "vite preview">> package.json
    echo   ^},>> package.json
    echo   "dependencies": ^{>> package.json
    echo     "react": "^18.2.0",>> package.json
    echo     "react-dom": "^18.2.0">> package.json
    echo   ^},>> package.json
    echo   "devDependencies": ^{>> package.json
    echo     "@vitejs/plugin-react": "^4.1.0",>> package.json
    echo     "vite": "^5.0.0">> package.json
    echo   ^}>> package.json
    echo ^}>> package.json
)

REM Create vite.config.js if it doesn't exist
if not exist vite.config.js (
    echo Creating vite.config.js...
    (
        echo import { defineConfig } from 'vite'
        echo import react from '@vitejs/plugin-react'
        echo.
        echo export default defineConfig({
        echo   plugins: [react()],
        echo   server: {
        echo     host: '0.0.0.0',
        echo     port: 3000,
        echo     proxy: {
        echo       '/api': {
        echo         target: 'http://localhost:8000',
        echo         changeOrigin: true
        echo       }
        echo     }
        echo   }
        echo })
    ) > vite.config.js
)

REM Create index.html if it doesn't exist
if not exist index.html (
    echo Creating index.html...
    (
        echo ^<!DOCTYPE html^>
        echo ^<html lang="en"^>
        echo   ^<head^>
        echo     ^<meta charset="UTF-8" /^>
        echo     ^<meta name="viewport" content="width=device-width, initial-scale=1.0" /^>
        echo     ^<title^>Multi-MCP Enterprise Integration^</title^>
        echo   ^</head^>
        echo   ^<body^>
        echo     ^<div id="root"^>^</div^>
        echo     ^<script type="module" src="/src/main.jsx"^>^</script^>
        echo   ^</body^>
        echo ^</html^>
    ) > index.html
)

REM Create main.jsx if it doesn't exist
if not exist src\main.jsx (
    echo Creating src\main.jsx...
    (
        echo import React from 'react'
        echo import ReactDOM from 'react-dom/client'
        echo import App from './App.jsx'
        echo.
        echo ReactDOM.createRoot(document.getElementById('root'^)^).render(
        echo   ^<React.StrictMode^>
        echo     ^<App /^>
        echo   ^</React.StrictMode^>,
        echo ^)
    ) > src\main.jsx
)

REM Install Node dependencies
echo    Installing Node.js dependencies...
npm install

echo    - Node dependencies installed

cd ..

REM Create .env if it doesn't exist
if not exist backend\.env (
    echo 3. Creating environment configuration...
    (
        echo # Azure OpenAI Configuration
        echo AZURE_OPEN_AI_KEY=your-azure-openai-key
        echo AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
        echo AZURE_DEPLOYMENT=gpt-4o-mini
        echo.
        echo # Bitbucket Configuration
        echo BITBUCKET_URL=https://sourcecode.socialcoding.bosch.com/rest/api/1.0
        echo BITBUCKET_USERNAME=your-username
        echo BITBUCKET_PASSWORD=your-password-or-app-password
        echo BITBUCKET_PROJECT=BIGDATAANALYTICS
        echo BITBUCKET_VERIFY_SSL=true
        echo.
        echo # Confluence Configuration
        echo CONFLUENCE_URL=https://inside-docupedia.bosch.com/confluence/rest/api
        echo CONFLUENCE_TOKEN=your-bearer-token
        echo CONFLUENCE_VERIFY_SSL=true
        echo.
        echo # JIRA Configuration
        echo JIRA_URL=https://your-jira-instance.atlassian.net
        echo JIRA_TOKEN=your-bearer-token
        echo JIRA_VERIFY_SSL=true
    ) > backend\.env

    echo    - .env file created
    echo    - IMPORTANT: Edit backend\.env with your actual API keys and URLs
) else (
    echo    - .env file already exists
)

REM Create start scripts
echo 4. Creating start scripts...

REM Create start-backend.bat
(
    echo @echo off
    echo echo Starting Multi-MCP Backend...
    echo.
    echo cd backend
    echo.
    echo REM Check if .env exists
    echo if not exist .env (
    echo     echo Error: .env file not found. Please run setup.bat first.
    echo     pause
    echo     exit /b 1
    echo ^)
    echo.
    echo REM Activate virtual environment
    echo call venv\Scripts\activate.bat
    echo.
    echo echo Backend running at: http://localhost:8000
    echo echo API docs at: http://localhost:8000/docs
    echo echo Press Ctrl+C to stop
    echo.
    echo python -m uvicorn mcp_orchestrator:app --host 0.0.0.0 --port 8000 --reload
) > start-backend.bat

REM Create start-frontend.bat
(
    echo @echo off
    echo echo Starting Multi-MCP Frontend...
    echo.
    echo cd frontend
    echo.
    echo REM Check if node_modules exists
    echo if not exist node_modules (
    echo     echo Error: node_modules not found. Please run setup.bat first.
    echo     pause
    echo     exit /b 1
    echo ^)
    echo.
    echo echo Frontend running at: http://localhost:3000
    echo echo Press Ctrl+C to stop
    echo.
    echo npm run dev
) > start-frontend.bat

echo    - Start scripts created

echo.
echo Setup Complete!
echo.
echo Next steps:
echo 1. Edit backend\.env with your actual API keys and URLs
echo 2. Copy your existing MCP files to the mcps\ directory
echo 3. Start the backend: start-backend.bat
echo 4. Start the frontend: start-frontend.bat
echo 5. Access at: http://localhost:3000
echo.
echo Files created:
echo - backend\venv\ (Python virtual environment)
echo - backend\requirements.txt (Python dependencies)
echo - backend\.env (Configuration - EDIT THIS)
echo - frontend\package.json (Node dependencies)
echo - frontend\src\main.jsx (React entry point)
echo - start-backend.bat (Backend start script)
echo - start-frontend.bat (Frontend start script)

pause