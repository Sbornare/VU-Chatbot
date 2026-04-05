"""
VU Chatbot - Single File Application
Simple, clean, and functional chatbot for Vishwakarma University
"""

import sys
import os
import time
import logging
from typing import Optional

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple configuration
class Settings:
    APP_NAME = "VU Chatbot"
    DEBUG = True

settings = Settings()

# Pydantic models
class ChatRequest(BaseModel):
    question: str
    conversation_history: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    response_time_ms: float
    tokens_used: Optional[int] = None

# Simple response generator
def generate_response(question: str) -> str:
    """Generate helpful responses for Vishwakarma University queries"""
    question_lower = question.lower().strip()
    
    # Handle greetings
    if any(word in question_lower for word in ["hi", "hello", "hey", "namaste", "good morning"]):
        return """Hello! Welcome to Vishwakarma University's virtual assistant! 🎓

I'm here to help you with information about:
• Academic programs and courses
• Admission procedures and requirements  
• Fee structure and payments
• Campus facilities and infrastructure
• Placement opportunities and statistics
• Contact information and location

What would you like to know about VU?"""
    
    # Handle program inquiries
    elif "program" in question_lower or "course" in question_lower or "degree" in question_lower:
        return """📚 **Vishwakarma University Programs:**

**Undergraduate (B.Tech):**
• Computer Science & Engineering
• Mechanical Engineering
• Electrical Engineering  
• Civil Engineering
• Electronics & Telecommunication
• Information Technology

**Postgraduate (M.Tech):**
• Computer Science & Engineering
• Mechanical Engineering
• Electrical Engineering

**Management Programs:**
• MBA (Marketing, Finance, HR, Operations)
• BBA (Bachelor of Business Administration)

**Other Programs:**
• M.Sc. (Computer Science, Mathematics, Physics)
• B.Sc. (Computer Science, Mathematics, Physics)

For detailed syllabus and specializations, contact: admissions@vupune.ac.in"""
    
    # Handle admission queries
    elif "admission" in question_lower or "eligibility" in question_lower or "apply" in question_lower:
        return """🎯 **Admission Information:**

**B.Tech Admissions:**
• Eligibility: 12th with Physics, Chemistry, Maths (Min 50%)
• Entrance: JEE Main / MHT-CET / VU Entrance Test
• Application Period: Usually June-July

**MBA Admissions:**  
• Eligibility: Bachelor's degree (Min 50%)
• Entrance: CAT / MAT / CMAT / VU Management Test
• Application Period: Usually November-March

**Application Process:**
1. Visit: https://www.vupune.ac.in
2. Fill online application form
3. Submit required documents
4. Pay application fee
5. Appear for entrance test/interview

**Contact:** 
📞 +91-20-28114400
📧 admissions@vupune.ac.in"""
    
    # Handle fee inquiries
    elif "fee" in question_lower or "cost" in question_lower or "tuition" in question_lower:
        return """💰 **Fee Information:**

**Engineering Programs (B.Tech):**
• Annual Fee: ₹3,10,000 - ₹4,00,000 (varies by branch)
• Additional: Hostel, Transport, Food charges

**Management Programs (MBA):**
• Annual Fee: ₹2,50,000 - ₹3,00,000
• Additional: Case study materials, industry visits

**Payment Options:**
• Semester-wise payment available
• Educational loans assistance provided
• Merit-based scholarships available

**Important:**
Fee structure may change for new academic year.
For exact current fees, contact:
📞 +91-20-28114400
📧 fees@vupune.ac.in"""
    
    # Handle placement queries  
    elif "placement" in question_lower or "job" in question_lower or "career" in question_lower:
        return """🚀 **Placement & Career Support:**

**Top Recruiting Companies:**
• TCS, Infosys, Wipro, Cognizant
• L&T, Mahindra, Bajaj Auto
• Microsoft, Amazon, Google
• Deloitte, KPMG, PwC

**Placement Statistics:**
• Average Package: ₹4-8 LPA
• Highest Package: ₹15+ LPA  
• Placement Rate: 85%+ consistently

**Career Services:**
• Resume building workshops
• Mock interviews and GD sessions
• Soft skills training
• Industry interaction sessions
• Internship opportunities

**Contact Placement Cell:**
📞 +91-20-28114401
📧 placements@vupune.ac.in"""
    
    # Handle campus/facilities queries
    elif "campus" in question_lower or "facility" in question_lower or "infrastructure" in question_lower:
        return """🏛️ **Campus Facilities:**

**Academic Infrastructure:**
• Modern classrooms with AV facilities
• Well-equipped laboratories
• Central library with 50,000+ books
• High-speed WiFi across campus
• Computer centers with latest software

**Sports & Recreation:**
• Cricket, Football, Basketball courts
• Indoor games: Table tennis, Chess, Carrom
• Gymnasium and fitness center
• Annual sports fest and cultural events

**Student Facilities:**
• Boys & Girls hostels
• Cafeteria and food courts
• Medical center with qualified staff
• Bank ATM and stationery shop
• Transportation facility

**Location:** Kondhwa, Pune - Well connected by public transport"""
    
    # Handle contact queries
    elif "contact" in question_lower or "phone" in question_lower or "email" in question_lower:
        return """📞 **Contact Vishwakarma University:**

**Main Office:**
📍 Survey No. 2, 3, 4, Kondhwa Budruk, Pune, Maharashtra 411048

**Phone Numbers:**
📞 Main: +91-20-28114400
📞 Admissions: +91-20-28114401  
📞 Placements: +91-20-28114402

**Email Contacts:**
📧 General: info@vupune.ac.in
📧 Admissions: admissions@vupune.ac.in
📧 Placements: placements@vupune.ac.in

**Website:** https://www.vupune.ac.in

**Office Hours:** Monday to Friday, 9:00 AM to 6:00 PM
**Saturday:** 9:00 AM to 1:00 PM"""
    
    # Handle location queries
    elif "location" in question_lower or "address" in question_lower or "where" in question_lower:
        return """📍 **Vishwakarma University Location:**

**Full Address:**
Survey No 2 3, 4, Kondhwa Main Rd, 
Laxmi Nagar, Betal Nagar, 
Kondhwa, Pune, Maharashtra 411048





**Campus:** Spread over 100+ acres with modern infrastructure"""
    
    # Default helpful response
    else:
        return """I'm here to help with questions about Vishwakarma University! 🎓

**I can provide information about:**
• 📚 Academic programs and courses
• 🎯 Admission procedures and requirements
• 💰 Fee structure and payment options  
• 🚀 Placement opportunities and statistics
• 🏛️ Campus facilities and infrastructure
• 📞 Contact information and location

**Please ask about any specific topic you're interested in!**

For example, you can ask:
- "What programs does VU offer?"
- "How do I apply for admission?"
- "What are the fees for engineering?"
- "Tell me about placements"
- "Where is the campus located?"

How can I help you today?"""

# Create FastAPI app
app = FastAPI(title=settings.APP_NAME, version="2.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "VU Chatbot is running"}

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Simple, reliable chat endpoint"""
    
    start_time = time.time()
    
    # Validate input
    if not req.question or not req.question.strip():
        return ChatResponse(
            response="Please ask a question about Vishwakarma University. I'm here to help!",
            response_time_ms=1
        )
    
    try:
        # Generate response
        response = generate_response(req.question.strip())
        
        total_time = (time.time() - start_time) * 1000
        
        logger.info(f"Response generated in {total_time:.1f}ms for: {req.question[:50]}")
        
        return ChatResponse(
            response=response,
            response_time_ms=total_time,
            tokens_used=len(response.split())
        )
        
    except Exception as e:
        error_time = (time.time() - start_time) * 1000
        logger.error(f"Chat error after {error_time:.1f}ms: {str(e)}")
        
        return ChatResponse(
            response="I encountered an issue processing your question. Please try rephrasing your question about Vishwakarma University.",
            response_time_ms=error_time
        )

@app.post("/api/chat/quality", response_model=ChatResponse)
def enhanced_chat(req: ChatRequest):
    """Enhanced chat endpoint (same functionality for now)"""
    return chat(req)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting VU Chatbot Server...")
    print("📚 Ready to help with Vishwakarma University information!")
    uvicorn.run(app, host="0.0.0.0", port=8000)