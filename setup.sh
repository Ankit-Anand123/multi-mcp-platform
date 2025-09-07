#!/bin/bash

echo "Setting up Multi-MCP Platform for Local Development"
echo "=================================================="

# Create directories
echo "Creating project structure..."
mkdir -p backend mcps frontend/src

# Backend setup
echo "1. Setting up Python backend..."
cd backend

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "Error: Python not found. Please install Python 3.8+ first."
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "   Using $PYTHON_CMD"

# Create virtual environment
$PYTHON_CMD -m venv venv

# Activate virtual environment (cross-platform)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
pip install --upgrade pip

# Create requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-dotenv==1.0.0
requests==2.31.0
agno==0.4.0
mcp==1.0.0
python-multipart==0.0.6
EOF
fi

# Install dependencies
echo "   Installing Python dependencies..."
pip install -r requirements.txt

echo "   - Virtual environment created"
echo "   - Dependencies installed"

cd ..

# Frontend setup
echo "2. Setting up React frontend..."
cd frontend

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "Error: Node.js not found. Please install Node.js 16+ first."
    exit 1
fi

echo "   Using Node.js $(node --version)"

# Create package.json if it doesn't exist
if [ ! -f package.json ]; then
    cat > package.json << 'EOF'
{
  "name": "multi-mcp-frontend",
  "version": "1.0.0",
  "description": "Multi-MCP Enterprise Integration Frontend",
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 3000",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.1.0",
    "vite": "^5.0.0"
  }
}
EOF
fi

# Create vite.config.js if it doesn't exist
if [ ! -f vite.config.js ]; then
    cat > vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
EOF
fi

# Create index.html if it doesn't exist
if [ ! -f index.html ]; then
    cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Multi-MCP Enterprise Integration</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOF
fi

# Create main.jsx if it doesn't exist
if [ ! -f src/main.jsx ]; then
    cat > src/main.jsx << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
EOF
fi

# Install Node dependencies
echo "   Installing Node.js dependencies..."
npm install

echo "   - Node dependencies installed"

cd ..

# Make MCP scripts executable
if [ -d mcps ]; then
    chmod +x mcps/*.py
    echo "   - MCP scripts made executable"
fi

# Create .env if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "3. Creating environment configuration..."
    cat > backend/.env << 'EOF'
# Azure OpenAI Configuration
AZURE_OPEN_AI_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_DEPLOYMENT=gpt-4o-mini

# Bitbucket Configuration
BITBUCKET_URL=https://sourcecode.socialcoding.bosch.com/rest/api/1.0
BITBUCKET_USERNAME=your-username
BITBUCKET_PASSWORD=your-password-or-app-password
BITBUCKET_PROJECT=BIGDATAANALYTICS
BITBUCKET_VERIFY_SSL=true

# Confluence Configuration
CONFLUENCE_URL=https://inside-docupedia.bosch.com/confluence/rest/api
CONFLUENCE_TOKEN=your-bearer-token
CONFLUENCE_VERIFY_SSL=true

# JIRA Configuration
JIRA_URL=https://your-jira-instance.atlassian.net
JIRA_TOKEN=your-bearer-token
JIRA_VERIFY_SSL=true
EOF

    echo "   - .env file created"
    echo "   - IMPORTANT: Edit backend/.env with your actual API keys and URLs"
else
    echo "   - .env file already exists"
fi

# Create start scripts
echo "4. Creating start scripts..."

# Create start-backend.sh
cat > start-backend.sh << 'EOF'
#!/bin/bash

echo "Starting Multi-MCP Backend..."

cd backend

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please run setup.sh first."
    exit 1
fi

# Start the backend server
echo "Backend running at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo "Press Ctrl+C to stop"

python -m uvicorn mcp_orchestrator:app --host 0.0.0.0 --port 8000 --reload
EOF

# Create start-frontend.sh
cat > start-frontend.sh << 'EOF'
#!/bin/bash

echo "Starting Multi-MCP Frontend..."

cd frontend

# Check if node_modules exists
if [ ! -d node_modules ]; then
    echo "Error: node_modules not found. Please run setup.sh first."
    exit 1
fi

echo "Frontend running at: http://localhost:3000"
echo "Press Ctrl+C to stop"

npm run dev
EOF

# Make start scripts executable
chmod +x start-backend.sh start-frontend.sh

echo "   - Start scripts created"

echo ""
echo "Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your actual API keys and URLs"
echo "2. Copy your existing MCP files to the mcps/ directory"
echo "3. Start the backend: ./start-backend.sh"
echo "4. Start the frontend: ./start-frontend.sh"
echo "5. Access at: http://localhost:3000"
echo ""
echo "Files created:"
echo "- backend/venv/ (Python virtual environment)"
echo "- backend/requirements.txt (Python dependencies)"
echo "- backend/.env (Configuration - EDIT THIS)"
echo "- frontend/package.json (Node dependencies)"
echo "- frontend/src/main.jsx (React entry point)"
echo "- start-backend.sh (Backend start script)"
echo "- start-frontend.sh (Frontend start script)"