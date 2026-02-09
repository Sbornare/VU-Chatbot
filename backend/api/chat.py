from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
try:
    from backend.granite.granite_client import granite_client
except ImportError:
    from granite.granite_client import granite_client
import logging
import time
import re

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    conversation_history: Optional[str] = None

class Source(BaseModel):
    category: str
    filename: str
    snippet: str

class ChatResponse(BaseModel):
    response: str
    sources: List[Source] = []
    response_time_ms: float
    tokens_used: Optional[int] = None

@router.post("/chat", response_model=ChatResponse)
def simple_chat(req: ChatRequest):
    """Simple working chat that handles all questions properly"""
    
    start_time = time.time()
    
    # Validate input
    if not req.question or not req.question.strip():
        return ChatResponse(
            response="Please ask a question about Vishwakarma University. I'm here to help!",
            sources=[],
            response_time_ms=1
        )
    
    question = req.question.strip().lower()
    
    # Handle greetings
    greeting_patterns = [r'\bhi\b', r'\bhello\b', r'\bhey\b', r'\bnamaste\b']
    if any(re.search(pattern, question) for pattern in greeting_patterns):
        return ChatResponse(
            response="Hello! I'm the VU Chatbot, here to help you with information about Vishwakarma University. I can assist you with programs, admissions, fees, placements, campus facilities, and more. What would you like to know?",
            sources=[],
            response_time_ms=(time.time() - start_time) * 1000
        )
    
    try:
        # Create a contextual prompt for university questions
        context_prompt = f"""You are a helpful assistant for Vishwakarma University. 
        Answer the following question about VU in a friendly, informative way:
        
        Question: {req.question}
        
        Provide a helpful response about Vishwakarma University. If you don't have specific information, guide them to contact the university directly."""
        
        # Use direct granite client call
        response = granite_client.generate_chat_response(context_prompt)
        
        total_time = (time.time() - start_time) * 1000
        
        logger.info(f"Simple chat response generated in {total_time:.1f}ms for: {req.question[:50]}")
        
        return ChatResponse(
            response=response,
            sources=[],
            response_time_ms=total_time,
            tokens_used=len(response.split()) if response else 0
        )
        
    except Exception as e:
        error_time = (time.time() - start_time) * 1000
        logger.error(f"Chat error after {error_time:.1f}ms: {str(e)}")
        
        return ChatResponse(
            response="I'm here to help with questions about Vishwakarma University! Could you please rephrase your question? I can provide information about programs, admissions, fees, placements, and campus facilities.",
            sources=[],
            response_time_ms=error_time
        )

@router.post("/chat/quality", response_model=ChatResponse) 
def enhanced_chat(req: ChatRequest):
    """Enhanced endpoint that uses same simple logic"""
    # Redirect to simple working chat
    return simple_chat(req)
