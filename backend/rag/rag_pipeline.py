from backend.rag.retriever import retrieve_context
from backend.granite.granite_client import granite_embeddings
import asyncio


def _generate_answer_question(question: str, conversation_history: str = None) -> dict:
    """
    Enhanced answer generation with better context retrieval and response quality
    """
    # Get enhanced context with sources
    result = retrieve_context(question, k=8)  # Get more context for better answers
    
    if isinstance(result, dict):
        context = result.get("context", "")
        sources = result.get("sources", [])
    else:
        context = result
        sources = []

    if not context.strip():
        return {
            "response": "I don't have specific information about that in my knowledge base. Could you ask about:\n\n• **Academic Programs** - BTech, MTech, MBA, etc.\n• **Admissions** - Requirements, deadlines, procedures\n• **Fees & Scholarships** - Cost details and financial aid\n• **Campus Life** - Facilities, hostels, activities\n• **Placements** - Job statistics and companies\n\nI'm here to help with all aspects of Vishwakarma University!",
            "sources": []
        }

    # Build enhanced prompt with conversation context
    from backend.granite.prompts import build_enhanced_prompt
    prompt = build_enhanced_prompt(context, question, conversation_history)

    # Generate response with improved model parameters
    response = granite_embeddings.generate_chat_response(
        prompt, 
        max_tokens=1500, 
        temperature=0.7  # Balanced creativity and accuracy
    )
    
    # Post-process response for better quality
    if response:
        # Clean up response formatting
        response = response.strip()
        
        # Ensure response ends properly
        if response and not response.endswith(('.', '!', '?', ':')):
            if len(response) > 50:  # Only add period to longer responses
                response += '.'
    else:
        response = "I apologize, but I'm having difficulty generating a response right now. Please try rephrasing your question or contact the admissions office directly."
    
    return {
        "response": response,
        "sources": sources[:5]  # Limit to top 5 sources
    }


def answer_question(question: str, conversation_history: str = None) -> dict:
    """Enhanced main entry point that returns response with sources"""
    return _generate_answer_question(question, conversation_history)


async def stream_answer_question(question: str, conversation_history: str = None):
    """
    Enhanced async streaming with better context and sources
    """
    result = retrieve_context(question, k=8)
    
    if isinstance(result, dict):
        context = result.get("context", "")
        sources = result.get("sources", [])
    else:
        context = result
        sources = []

    if not context.strip():
        response = "I don't have specific information about that in my knowledge base. Let me suggest some areas I can help with:\n\n• **Academic Programs** - Engineering, Management, Sciences\n• **Admissions** - Requirements, deadlines, application process\n• **Campus Life** - Facilities, hostels, student activities\n• **Placements** - Career opportunities and statistics\n\nWhat would you like to know about?"
        
        for chunk in response.split():
            yield {"chunk": chunk + " ", "sources": []}
            await asyncio.sleep(0.02)
        return

    from backend.granite.prompts import build_enhanced_prompt
    prompt = build_enhanced_prompt(context, question, conversation_history)

    # Stream enhanced response with sources
    first_chunk = True
    for token in granite_embeddings.generate_chat_stream(prompt):
        chunk_data = {"chunk": token}
        if first_chunk:
            chunk_data["sources"] = sources[:5]  # Include sources with first chunk
            first_chunk = False
        yield chunk_data
        await asyncio.sleep(0.001)
