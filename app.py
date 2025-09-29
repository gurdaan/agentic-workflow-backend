"""
Azure Boards AI Agent API

A comprehensive REST API for managing Azure DevOps work items through AI-powered agents.
This service provides intelligent automation for creating user stories, test cases, and development tasks
using Azure OpenAI and Azure AI Foundry services, with persistent chat history storage.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from agents import AgentService
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging for the API
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global agent instance
agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan management with simplified shutdown (auto-save now handled per message)"""
    global agent
    
    # Startup
    logger.info("🚀 FastAPI app starting up")
    agent = AgentService()
    await agent.initialize()
    logger.info("🤖 Agent service initialized")
    
    yield
    
    # Shutdown - Clean up only (auto-save now handled per message)
    logger.info("� Server shutdown initiated")
    
    # Clean up resources
    if agent:
        await agent.cleanup()
    logger.info("🧹 Application shutdown complete - Auto-save handled per message")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Azure Boards AI Agent API", 
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://witty-mud-0113ed00f.1.azurestaticapps.net",
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Accept-Language", "Content-Language", "Content-Type"],
)

logger.info("🌐 CORS middleware configured")

# Request/Response models
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    content: str
    metadata: dict

class SaveChatResponse(BaseModel):
    success: bool
    blob_name: str = None
    message: str

class ChatSessionResponse(BaseModel):
    sessions: List[Dict[str, Any]]

class NewSessionRequest(BaseModel):
    session_name: str = None

class SessionResponse(BaseModel):
    success: bool
    session_id: str = None
    message: str

class SwitchSessionRequest(BaseModel):
    session_id: str

# API endpoints
@app.post("/api/sessions/new", response_model=SessionResponse)
async def create_new_session(request: NewSessionRequest):
    """Create a new chat session"""
    logger.info(f"🆕 New session request: {request.session_name}")
    
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent service not initialized")
        
        session_id = await agent.create_new_session(request.session_name)
        logger.info(f"✅ New session created: {session_id}")
        
        return SessionResponse(
            success=True,
            session_id=session_id,
            message="New session created successfully"
        )
    except Exception as e:
        logger.error(f"❌ Create session error: {e}")
        return SessionResponse(
            success=False,
            message=f"Failed to create session: {str(e)}"
        )

@app.post("/api/sessions/switch", response_model=SessionResponse)
async def switch_session(request: SwitchSessionRequest):
    """Switch to an existing chat session"""
    logger.info(f"🔄 Switch session request: {request.session_id}")
    
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent service not initialized")
        
        success = await agent.switch_session(request.session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"✅ Switched to session: {request.session_id}")
        return SessionResponse(
            success=True,
            session_id=request.session_id,
            message="Session switched successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Switch session error: {e}")
        return SessionResponse(
            success=False,
            message=f"Failed to switch session: {str(e)}"
        )

@app.get("/api/sessions/current")
async def get_current_session():
    """Get current session information"""
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent service not initialized")
        
        return {
            "session_id": agent.current_session_id,
            "message_count": len(agent.conversation.messages) if agent.conversation else 0,
            "has_user_messages": agent.has_user_messages
        }
    except Exception as e:
        logger.error(f"❌ Get current session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat query through the agent"""
    logger.info("🌟 API Request received")
    logger.info(f"💬 Query: {request.query}")
    
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent service not initialized")
            
        result = await agent.process_query(request.query)
        
        response = ChatResponse(
            content=result["content"],
            metadata=result["metadata"]
        )
        
        logger.info("✅ API Response sent")
        return response
        
    except Exception as e:
        logger.error(f"❌ API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save-chat", response_model=SaveChatResponse)
async def save_chat_endpoint():
    """Manually save current chat history to blob storage"""
    logger.info("💾 Manual save chat request received")
    
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent service not initialized")
        
        # Only save if there are actual user messages
        if not agent.has_user_messages:
            return SaveChatResponse(
                success=True,
                message="No chat history to save (empty conversation)"
            )
            
        blob_name = await agent.save_chat_history()
        logger.info(f"✅ Chat saved to blob: {blob_name}")
        return SaveChatResponse(
            success=True,
            blob_name=blob_name,
            message=f"Session '{agent.current_session_id}' saved successfully"
        )
    except Exception as e:
        logger.error(f"❌ Save chat error: {e}")
        return SaveChatResponse(
            success=False,
            message=f"Failed to save chat: {str(e)}"
        )

@app.get("/api/chat-sessions", response_model=ChatSessionResponse)
async def get_chat_sessions():
    """Get list of all saved chat sessions"""
    logger.info("📋 Chat sessions request received")
    
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent service not initialized")
            
        sessions = await agent.get_chat_sessions()
        logger.info(f"✅ Found {len(sessions)} chat sessions")
        return ChatSessionResponse(sessions=sessions)
    except Exception as e:
        logger.error(f"❌ Get sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat-sessions/{blob_name}")
async def get_chat_session(blob_name: str):
    """Load a specific chat session"""
    logger.info(f"� Loading chat session: {blob_name}")
    
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent service not initialized")
            
        chat_data = await agent.load_chat_history(blob_name)
        if not chat_data:
            raise HTTPException(status_code=404, detail="Chat session not found")
            
        logger.info(f"✅ Chat session loaded: {blob_name}")
        return chat_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Load session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat-sessions/{blob_name}")
async def delete_chat_session(blob_name: str):
    """Delete a chat session"""
    logger.info(f"🗑️ Deleting chat session: {blob_name}")
    
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent service not initialized")
            
        success = await agent.delete_chat_session(blob_name)
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
            
        logger.info(f"✅ Chat session deleted: {blob_name}")
        return {"success": True, "message": "Chat session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "timestamp": logger.handlers[0].baseFilename if logger.handlers else "unknown"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)