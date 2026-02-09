// Bulletproof chat service - no crashes allowed

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface Source {
  category: string;
  filename: string;
  snippet: string;
}

export interface ChatResponse {
  response: string;
  sources?: Source[];
  response_time_ms?: number;
}

const API_URL = "http://localhost:8000/api/chat";
const ENHANCED_API_URL = "http://localhost:8000/api/chat/quality";

export async function sendMessage(question: string): Promise<ChatResponse> {
  // Input validation
  if (!question || typeof question !== 'string' || question.trim().length === 0) {
    return {
      response: "Please enter a valid question.",
      sources: [],
      response_time_ms: 1
    };
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

    // Try enhanced API first
    let res = await fetch(ENHANCED_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        question: question.trim(),
        conversation_history: null // TODO: Add conversation support
      }),
      signal: controller.signal
    });

    // Fallback to basic API if enhanced fails
    if (!res.ok) {
      console.log('Enhanced API failed, trying basic API...');
      res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim() }),
        signal: controller.signal
      });
    }

    clearTimeout(timeoutId);

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();
    
    // Validate response structure
    if (!data || typeof data.response !== 'string') {
      throw new Error('Invalid response format');
    }
    
    return {
      response: data.response || "I apologize, but I wasn't able to generate a response. Please try rephrasing your question.",
      sources: Array.isArray(data.sources) ? data.sources : [],
      response_time_ms: typeof data.response_time_ms === 'number' ? data.response_time_ms : 1
    };
    
  } catch (error) {
    console.error('Chat service error:', error);
    
    return {
      response: "I'm having trouble connecting to the server. Please check your connection and try again. If the problem persists, please refresh the page.",
      sources: [],
      response_time_ms: 1
    };
  }
}

// Simplified streaming function (not used but kept for compatibility)
export async function sendMessageStream(
  question: string,
  onChunk: (text: string) => void,
): Promise<void> {
  try {
    const response = await sendMessage(question);
    onChunk(response.response);
  } catch (error) {
    console.error('Streaming error:', error);
    onChunk("Error: Unable to get response. Please try again.");
  }
}

export async function submitFeedback(data: {
  messageId: string;
  feedbackType: 'like' | 'dislike';
  question: string;
  answer: string;
}): Promise<void> {
  try {
    const res = await fetch("http://localhost:8000/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    if (!res.ok) {
      console.error("Failed to submit feedback");
    }
  } catch (error) {
    console.error("Error submitting feedback:", error);
  }
}

