# README-LOCAL.md
# Multi-MCP Platform - Local Development Setup

Simple local development setup for the Multi-MCP Enterprise Integration Platform.

## Prerequisites

- Python 3.8+ 
- Node.js 16+
- Git

## Quick Start

### 1. Initial Setup

```bash
# Clone or create the project directory
mkdir multi-mcp-platform
cd multi-mcp-platform

# Make setup script executable and run it
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment

```bash
# Edit the configuration file with your actual values
nano backend/.env
```

Required configuration:
- `AZURE_OPEN_AI_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
- `BITBUCKET_URL`, `BITBUCKET_USERNAME`, `BITBUCKET_PASSWORD`: Bitbucket credentials
- `CONFLUENCE_URL`, `CONFLUENCE_TOKEN`: Confluence API access
- `JIRA_URL`, `JIRA_TOKEN`: JIRA API access

### 3. Test Configuration

```bash
# Check dependencies
python check-deps.py

# Test MCP servers
python test-mcps.py
```

### 4. Start the Application

**Option A: Start both services together**
```bash
./start.sh
```

**Option B: Start services separately**
```bash
# Terminal 1: Backend
./start-backend.sh

# Terminal 2: Frontend  
./start-frontend.sh
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Usage Examples

Try these queries in the frontend:

1. **Documentation Search**:
   - "Find documentation about code review best practices"
   - "How to set up CI/CD pipeline"

2. **Issue Management**:
   - "Show me all high priority bugs assigned to John"
   - "Create a task for updating documentation"

3. **Code Review Analysis**:
   - "Analyze recent PR comments in project ABC"
   - "Find code review guidelines and compare with recent PRs"

4. **Cross-System Queries**:
   - "Find documentation about deployment and check for related JIRA issues"
   - "Show sprint progress and any blocking documentation"

## Project Structure

```
multi-mcp-platform/
├── backend/
│   ├── mcp_orchestrator.py    # Main backend with intelligent routing
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Configuration (create from setup)
├── mcps/
│   ├── jira_mcp.py           # JIRA integration
│   ├── confluence_mcp.py     # Confluence integration
│   └── bitbucket_mcp.py      # Bitbucket integration
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main React component
│   │   ├── App.css           # Styles
│   │   └── main.jsx          # React entry point
│   ├── index.html            # HTML template
│   ├── package.json          # Node dependencies
│   └── vite.config.js        # Build configuration
├── setup.sh                  # Initial setup script
├── start.sh                  # Start both services
├── start-backend.sh          # Start backend only
├── start-frontend.sh         # Start frontend only
├── test-mcps.py              # Test MCP connections
└── check-deps.py             # Check dependencies
```

## Troubleshooting

### Common Issues

1. **MCP Connection Failures**
   - Check your .env file has correct URLs and tokens
   - Verify network connectivity to your services
   - Run `python test-mcps.py` to diagnose

2. **Backend Won't Start**
   - Check if virtual environment is activated
   - Verify all Python dependencies: `python check-deps.py`
   - Check port 8000 isn't already in use

3. **Frontend Won't Start**
   - Verify Node.js is installed: `node --version`
   - Check if dependencies are installed: `npm install` in frontend/
   - Check port 3000 isn't already in use

4. **Import Errors**
   - Make sure you're in the correct directory
   - Activate the Python virtual environment:
     - Linux/Mac: `source backend/venv/bin/activate`
     - Windows: `backend\venv\Scripts\activate`

### Getting Help

- Check the logs in your terminal for specific error messages
- Verify your API tokens have the correct permissions
- Test individual MCPs using the test script

### Development Tips

- Backend auto-reloads on code changes
- Frontend auto-reloads on code changes  
- API documentation available at http://localhost:8000/docs
- Use browser developer tools to debug frontend issues

## Next Steps

Once you have the local setup working:
1. Test with your actual enterprise data
2. Customize the query routing logic for your needs
3. Add additional MCP integrations
4. Consider containerization for team deployment