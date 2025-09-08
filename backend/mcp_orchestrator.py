# backend/mcp_orchestrator.py
import os
import re
import asyncio
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum

from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from agno.tools.mcp import MCPTools
from dotenv import load_dotenv
import sys

load_dotenv()

class MCPType(Enum):
    JIRA = "jira"
    CONFLUENCE = "confluence"
    BITBUCKET = "bitbucket"

@dataclass
class MCPConfig:
    mcp_type: MCPType
    command: str
    timeout: int = 60
    instructions: str = ""

class MCPOrchestrator:
    def __init__(self):
        self.model = AzureOpenAI(
            id="gpt-4o-mini",
            api_key=os.getenv("AZURE_OPEN_AI_KEY"),
            api_version="2024-05-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment="gpt-4o-mini",
        )
        

        
        self.mcp_configs = {
            MCPType.JIRA: MCPConfig(
                mcp_type=MCPType.JIRA,
                command="python ../mcps/jira_mcp.py",
                timeout=30,  # Reduced timeout to debug faster
                instructions="""You are a JIRA operations agent. Use JIRA MCP tools for:
                - Issue tracking and management
                - Sprint and project management
                - User and permission management
                - Workflow and status tracking
                Always use JIRA tools for issue-related queries."""
            ),
            MCPType.CONFLUENCE: MCPConfig(
                mcp_type=MCPType.CONFLUENCE,
                command="python ../mcps/confluence_mcp.py",
                instructions="""You are a Confluence operations agent. Use Confluence MCP tools for:
                - Documentation search and retrieval
                - Space and page management
                - Knowledge base queries
                - Content analysis
                Always search Confluence rather than generating answers from internal knowledge."""
            ),
            MCPType.BITBUCKET: MCPConfig(
                mcp_type=MCPType.BITBUCKET,
                command="python ../mcps/bitbucket_mcp.py",
                instructions="""You are a Bitbucket operations agent. Use Bitbucket MCP tools for:
                - Repository management
                - Pull request operations
                - Code review analysis
                - Commit and branch tracking
                Always use Bitbucket tools for repository-related queries."""
            )
        }
        
        # Keywords for intelligent routing
        self.keywords = {
            MCPType.JIRA: {
                'primary': ['jira', 'issue', 'ticket', 'sprint', 'epic', 'story', 'bug', 'task'],
                'secondary': ['assignee', 'priority', 'workflow', 'project', 'board', 'backlog']
            },
            MCPType.CONFLUENCE: {
                'primary': ['confluence', 'documentation', 'wiki', 'page', 'space', 'knowledge'],
                'secondary': ['guide', 'manual', 'procedure', 'policy', 'how-to', 'tutorial']
            },
            MCPType.BITBUCKET: {
                'primary': ['bitbucket', 'repository', 'repo', 'pull request', 'pr', 'commit', 'branch'],
                'secondary': ['code review', 'merge', 'git', 'source code', 'version control']
            }
        }

    def analyze_query(self, query: str) -> Set[MCPType]:
        """Analyze query to determine which MCPs are needed"""
        query_lower = query.lower()
        needed_mcps = set()
        scores = {mcp_type: 0 for mcp_type in MCPType}
        
        # Score based on keyword matches
        for mcp_type, keywords in self.keywords.items():
            for keyword in keywords['primary']:
                if keyword in query_lower:
                    scores[mcp_type] += 3
            for keyword in keywords['secondary']:
                if keyword in query_lower:
                    scores[mcp_type] += 1
        
        # Pattern-based detection
        patterns = {
            MCPType.JIRA: [
                r'\b[A-Z]{2,}-\d+\b',  # JIRA issue keys like ABC-123
                r'create.*(?:issue|ticket|story)',
                r'assign.*to',
                r'sprint.*\d+',
            ],
            MCPType.CONFLUENCE: [
                r'search.*(?:documentation|wiki|confluence)',
                r'how\s+(?:to|do|can)',
                r'documentation.*about',
                r'find.*(?:page|guide)',
            ],
            MCPType.BITBUCKET: [
                r'pull\s+request',
                r'code\s+review',
                r'commit.*analysis',
                r'repository.*[A-Z][A-Z0-9_]+/[a-zA-Z0-9_-]+',  # repo pattern
            ]
        }
        
        for mcp_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, query_lower):
                    scores[mcp_type] += 2
        
        # Determine which MCPs to use
        max_score = max(scores.values())
        if max_score >= 2:
            # Use MCPs with scores >= 50% of max score
            threshold = max(1, max_score * 0.5)
            needed_mcps = {mcp for mcp, score in scores.items() if score >= threshold}
        else:
            # Default fallback - try to infer from context
            if any(word in query_lower for word in ['find', 'search', 'documentation', 'how']):
                needed_mcps.add(MCPType.CONFLUENCE)
            if any(word in query_lower for word in ['issue', 'bug', 'task']):
                needed_mcps.add(MCPType.JIRA)
            if any(word in query_lower for word in ['code', 'repository', 'commit']):
                needed_mcps.add(MCPType.BITBUCKET)
        
        return needed_mcps or {MCPType.CONFLUENCE}  # Default to Confluence

    async def execute_query(self, query: str, selected_mcps: Optional[Set[MCPType]] = None, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """Execute query using determined or selected MCPs with conversation history"""
        print(f"[ORCHESTRATOR] Starting execute_query with: {query}")
        
        if selected_mcps is None:
            selected_mcps = self.analyze_query(query)
            print(f"[ORCHESTRATOR] Auto-selected MCPs: {[mcp.value for mcp in selected_mcps]}")
        else:
            print(f"[ORCHESTRATOR] Using provided MCPs: {[mcp.value for mcp in selected_mcps]}")
        
        results = {
            'query': query,
            'mcps_used': [mcp.value for mcp in selected_mcps],
            'responses': {},
            'synthesis': None
        }
        
        if len(selected_mcps) == 1:
            # Single MCP execution
            mcp_type = list(selected_mcps)[0]
            print(f"[ORCHESTRATOR] Single MCP execution: {mcp_type.value}")
            try:
                response = await self._execute_single_mcp(query, mcp_type, conversation_history)
                results['responses'][mcp_type.value] = response
                results['synthesis'] = response
                print(f"[ORCHESTRATOR] Single MCP execution completed successfully")
            except Exception as e:
                error_msg = f"Error executing {mcp_type.value}: {str(e)}"
                print(f"[ORCHESTRATOR] Single MCP execution failed: {error_msg}")
                results['responses'][mcp_type.value] = error_msg
                results['synthesis'] = error_msg
        else:
            # Multiple MCP execution
            print(f"[ORCHESTRATOR] Multiple MCP execution: {[mcp.value for mcp in selected_mcps]}")
            responses = {}
            for mcp_type in selected_mcps:
                try:
                    print(f"[ORCHESTRATOR] Executing MCP: {mcp_type.value}")
                    response = await self._execute_single_mcp(query, mcp_type, conversation_history)
                    responses[mcp_type.value] = response
                    print(f"[ORCHESTRATOR] MCP {mcp_type.value} completed successfully")
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    print(f"[ORCHESTRATOR] MCP {mcp_type.value} failed: {error_msg}")
                    responses[mcp_type.value] = error_msg
            
            results['responses'] = responses
            
            # Synthesize results from multiple MCPs
            if len(responses) > 1:
                try:
                    print(f"[ORCHESTRATOR] Starting synthesis of {len(responses)} responses")
                    synthesis = await self._synthesize_results(query, responses, conversation_history)
                    results['synthesis'] = synthesis
                    print(f"[ORCHESTRATOR] Synthesis completed successfully")
                except Exception as e:
                    error_msg = f"Synthesis error: {str(e)}"
                    print(f"[ORCHESTRATOR] Synthesis failed: {error_msg}")
                    results['synthesis'] = error_msg
            else:
                results['synthesis'] = list(responses.values())[0]
        
        print(f"[ORCHESTRATOR] execute_query completed")
        return results

    async def _execute_single_mcp(self, query: str, mcp_type: MCPType, conversation_history: Optional[List[Dict]] = None) -> str:
        """Execute query on a single MCP with conversation context"""
        config = self.mcp_configs[mcp_type]
        
        print(f"[ORCHESTRATOR] Executing {mcp_type.value} with command: {config.command}")
        print(f"[ORCHESTRATOR] Query: {query}")
        
        mcp_tools = MCPTools(
            command=config.command,
            timeout_seconds=config.timeout,
            env={**os.environ}
        )
        
        try:
            print(f"[ORCHESTRATOR] Connecting to {mcp_type.value} MCP...")
            await mcp_tools.connect()
            print(f"[ORCHESTRATOR] Connected to {mcp_type.value} MCP successfully")
            
            # Test MCP connection first
            print(f"[ORCHESTRATOR] Testing {mcp_type.value} MCP connection...")
            try:
                # Get available tools to verify connection
                tools = await mcp_tools.list_tools()
                print(f"[ORCHESTRATOR] {mcp_type.value} MCP has {len(tools)} tools available")
                for tool in tools[:3]:  # Show first 3 tools
                    print(f"[ORCHESTRATOR]   - {tool.name}: {tool.description[:100]}...")
            except Exception as e:
                print(f"[ORCHESTRATOR] Warning: Could not list tools from {mcp_type.value}: {e}")
            
            # Build context from conversation history
            context_instructions = config.instructions
            if conversation_history:
                context_messages = self._build_context_from_history(conversation_history)
                context_instructions += f"\n\nConversation Context:\n{context_messages}"
            
            print(f"[ORCHESTRATOR] Creating agent for {mcp_type.value}")
            agent = Agent(
                model=self.model,
                tools=[mcp_tools],
                instructions=context_instructions,
                markdown=True,
                show_tool_calls=False,
            )
            
            print(f"[ORCHESTRATOR] Running agent for {mcp_type.value} with query...")
            print(f"[ORCHESTRATOR] Agent instructions: {context_instructions[:200]}...")
            
            # Add timeout to prevent hanging
            try:
                # Use arun to get the response as a string with timeout
                response = await asyncio.wait_for(
                    agent.arun(query), 
                    timeout=config.timeout
                )
                print(f"[ORCHESTRATOR] {mcp_type.value} agent completed successfully")
            except asyncio.TimeoutError:
                print(f"[ORCHESTRATOR] {mcp_type.value} agent timed out after {config.timeout} seconds")
                raise Exception(f"{mcp_type.value} agent execution timed out")
            except Exception as e:
                print(f"[ORCHESTRATOR] Agent execution failed: {str(e)}")
                raise e
            
            # Handle different response types
            if hasattr(response, 'content'):
                return response.content
            elif hasattr(response, 'message'):
                return response.message
            else:
                return str(response)
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Error in {mcp_type.value} execution: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e
        finally:
            try:
                print(f"[ORCHESTRATOR] Closing {mcp_type.value} tools...")
                await mcp_tools.close()
                print(f"[ORCHESTRATOR] {mcp_type.value} tools closed successfully")
            except Exception as e:
                print(f"[ORCHESTRATOR] Warning: Error closing {mcp_type.value} tools: {e}")

    def _build_context_from_history(self, conversation_history: List[Dict]) -> str:
        """Build context string from conversation history (last 5 messages)"""
        if not conversation_history:
            return ""
        
        # Take only the last 5 messages for context
        recent_history = conversation_history[-5:]
        
        context_parts = []
        for msg in recent_history:
            role = "User" if msg.get('is_user', False) else "Assistant"
            text = msg.get('text', '')
            mcps = msg.get('mcps_used', [])
            
            context_part = f"{role}: {text}"
            if mcps and not msg.get('is_user', False):
                context_part += f" (Used: {', '.join(mcps)})"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)

    async def _synthesize_results(self, query: str, responses: Dict[str, str], conversation_history: Optional[List[Dict]] = None) -> str:
        """Synthesize results from multiple MCPs with conversation context"""
        context_instructions = """You are a concise synthesis agent. Combine information from multiple systems 
        to provide a direct, clean response that answers the user's question without unnecessary elaboration."""
        
        if conversation_history:
            context_messages = self._build_context_from_history(conversation_history)
            context_instructions += f"\n\nConversation Context:\n{context_messages}"
        
        synthesis_agent = Agent(
            model=self.model,
            tools=[],
            instructions=context_instructions,
            markdown=True,
            show_tool_calls=False,
        )
        
        synthesis_prompt = f"""
        User Query: {query}
        
        System Results:
        {chr(10).join([f"{system.upper()}: {response}" for system, response in responses.items()])}
        
        Provide a direct, concise answer to the user's query. Focus only on what was asked. 
        Do not add insights, connections, or suggestions unless specifically requested.
        """
        
        response = await synthesis_agent.arun(synthesis_prompt)
        
        # Handle different response types
        if hasattr(response, 'content'):
            return response.content
        elif hasattr(response, 'message'):
            return response.message
        else:
            return str(response)

# FastAPI backend
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Multi-MCP Enterprise Integration")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = MCPOrchestrator()

class MessageHistory(BaseModel):
    text: str
    is_user: bool
    timestamp: str
    mcps_used: Optional[List[str]] = []

class QueryRequest(BaseModel):
    query: str
    selected_mcps: Optional[List[str]] = None
    conversation_history: Optional[List[MessageHistory]] = []

class QueryResponse(BaseModel):
    query: str
    mcps_used: List[str]
    responses: Dict[str, str]
    synthesis: str
    suggested_mcps: List[str]

@app.post("/api/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    print(f"[API] Received query request: {request.query}")
    print(f"[API] Selected MCPs: {request.selected_mcps}")
    print(f"[API] Conversation history length: {len(request.conversation_history) if request.conversation_history else 0}")
    
    try:
        # Convert string MCPs to enum types
        selected_mcps = None
        if request.selected_mcps:
            selected_mcps = {MCPType(mcp) for mcp in request.selected_mcps}
            print(f"[API] Converted MCPs to enums: {[mcp.value for mcp in selected_mcps]}")
        
        # Convert Pydantic models to dict for conversation history
        conversation_history = None
        if request.conversation_history:
            conversation_history = [
                {
                    'text': msg.text,
                    'is_user': msg.is_user,
                    'timestamp': msg.timestamp,
                    'mcps_used': msg.mcps_used or []
                }
                for msg in request.conversation_history
            ]
            print(f"[API] Converted conversation history: {len(conversation_history)} messages")
        
        # Get suggested MCPs for frontend
        suggested_mcps = orchestrator.analyze_query(request.query)
        suggested_mcp_names = [mcp.value for mcp in suggested_mcps]
        print(f"[API] Suggested MCPs: {suggested_mcp_names}")
        
        # Execute query with conversation history
        print(f"[API] Starting orchestrator execution...")
        results = await orchestrator.execute_query(request.query, selected_mcps, conversation_history)
        print(f"[API] Orchestrator execution completed successfully")
        
        response = QueryResponse(
            query=results['query'],
            mcps_used=results['mcps_used'],
            responses=results['responses'],
            synthesis=results['synthesis'],
            suggested_mcps=suggested_mcp_names
        )
        print(f"[API] Returning response with {len(results['responses'])} MCP responses")
        return response
        
    except Exception as e:
        print(f"[API] Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcps")
async def get_available_mcps():
    """Get list of available MCPs"""
    return {
        "mcps": [
            {"id": "jira", "name": "JIRA", "description": "Issue tracking and project management"},
            {"id": "confluence", "name": "Confluence", "description": "Documentation and knowledge base"},
            {"id": "bitbucket", "name": "Bitbucket", "description": "Code repositories and reviews"}
        ]
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Serve static files for production (commented out for development)
# app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)