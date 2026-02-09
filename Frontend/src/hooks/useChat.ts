import { useState, useCallback, useRef } from 'react';
import { sendMessage, Message, Source } from '@/services/chatService';

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  sources: Source[];
  error: string | null;
}

export const useChat = () => {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    sources: [],
    error: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const send = useCallback(async (content: string) => {
    // Clear any previous errors
    setState(prev => ({ ...prev, error: null }));
    
    // Validate input
    if (!content || content.trim().length === 0) {
      setState(prev => ({ 
        ...prev, 
        error: "Please enter a message" 
      }));
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content: content.trim(),
      role: 'user',
      timestamp: new Date(),
    };

    // Add user message immediately
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: null
    }));

    try {
      // Get response with error handling
      const response = await sendMessage(content.trim());
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.response || "I'm sorry, I couldn't generate a proper response. Please try again.",
        role: 'assistant',
        timestamp: new Date(),
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
        isLoading: false,
        sources: Array.isArray(response.sources) ? response.sources : [],
        error: null
      }));

    } catch (error) {
      console.error('Chat error:', error);
      
      // Add error message instead of crashing
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `🔧 **Connection Issue**

I'm having trouble connecting to the server right now. Here's what you can try:

• **Refresh the page** and try again
• **Check your internet connection**
• **Contact support** if the issue persists

**Quick Help:**
• For placement info, try: "show placement statistics"
• For admissions, try: "admission requirements"
• For fees, try: "fee structure"

I apologize for the inconvenience!`,
        role: 'assistant',
        timestamp: new Date(),
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, errorMessage],
        isLoading: false,
        error: "Connection failed - but you can still try again!"
      }));
    }
  }, []);

  const clearMessages = useCallback(() => {
    setState({
      messages: [],
      isLoading: false,
      sources: [],
      error: null,
    });
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    sources: state.sources,
    error: state.error,
    send,
    clearMessages,
    clearError,
  };
};
                content: fullResponse,
              };
            } else {
              newMessages.push({
                id: assistantMessageId,
                content: fullResponse,
                role: 'assistant',
                timestamp: new Date(),
              });
            }

            return {
              ...prev,
              messages: newMessages,
            };
          });
        }
      );

      setState(prev => ({
        ...prev,
        isLoading: false,
      }));
    } catch (error) {
      console.error('Chat error:', error);
      
      // Fallback to non-streaming if streaming fails
      const response = await sendMessage(content);
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, response.message],
        sources: response.sources,
        isLoading: false,
      }));
    }
  }, []);

  const clearChat = useCallback(() => {
    setState({
      messages: [],
      isLoading: false,
      sources: [],
    });
  }, []);

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    sources: state.sources,
    sendMessage: send,
    clearChat,
  };
};
