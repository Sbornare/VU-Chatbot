import { useState, useRef, useEffect } from "react";
import { Send, StopCircle, Menu, MessageSquare, Sparkles, RefreshCw, Settings, User, Bot, Zap } from "lucide-react";
import Layout from "../components/Layout";
import ModernChatMessage from "../components/ModernChatMessage";
import Sidebar from "../components/Sidebar";
import { sendMessage, submitFeedback } from "../services/chatService";
import { useChatSessions } from "../hooks/useChatSessions";
import ChatErrorBoundary from "../components/Common/ChatErrorBoundary";

const WELCOME_MESSAGE = {
  role: "assistant" as const,
  content: "🎓 **Welcome to VU Smart Assistant!**\n\nI'm your AI-powered university companion, here to help you navigate everything about Vishwakarma University!\n\n✨ **What I can help you with:**\n📚 Academic programs and course details\n💰 Fees, scholarships, and financial aid\n🏛️ Campus facilities and student life\n📝 Admission requirements and deadlines\n🎯 Placement statistics and career opportunities\n📞 Contact information and important dates\n\n💡 **Quick Tips:**\n• Ask me anything about VU\n• I provide instant, accurate responses\n• Use natural language - I understand context\n\n🚀 **Ready to explore VU together?**"
};

const QUICK_ACTIONS = [
  { text: "🎓 Show Programs", query: "What programs does VU offer?" },
  { text: "💰 Fees & Scholarships", query: "Tell me about fees and scholarships" },
  { text: "🏢 Placement Stats", query: "Show me placement statistics" },
  { text: "📞 Contact Info", query: "How can I contact VU admissions?" }
];

export default function Chat() {
  const {
    sessions,
    activeSession,
    createSession,
    switchSession,
    addMessage,
    updateMessage,
    deleteSession,
    renameSession
  } = useChatSessions();

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const initializedRef = useRef(false);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  // Auto-scroll to bottom with smooth animation
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [activeSession?.messages, isLoading]);

  // Check system dark mode preference
  useEffect(() => {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setIsDarkMode(true);
    }
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + 'px';
    }
  }, [input]);

  // Create first session if none exist
  useEffect(() => {
    if (!initializedRef.current && sessions.length === 0) {
      initializedRef.current = true;
      const newSession = createSession();
      addMessage(WELCOME_MESSAGE);
    }
  }, [sessions.length, createSession, addMessage]);

  // Hide quick actions when messages exist
  useEffect(() => {
    if (activeSession?.messages && activeSession.messages.length > 1) {
      setShowQuickActions(false);
    }
  }, [activeSession?.messages]);

  const handleSend = async (message?: string) => {
    const userMsg = message || input.trim();
    if (!userMsg || isLoading || !activeSession) return;

    setInput("");
    setShowQuickActions(false);
    setIsTyping(true);

    // Add user message with animation
    addMessage({ role: "user", content: userMsg });
    setIsLoading(true);

    try {
      // Simulate typing delay for better UX
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const response = await sendMessage(userMsg);

      // Add assistant response with typing effect
      addMessage({
        role: "assistant",
        content: response.response,
        sources: response.sources || []
      });

    } catch (error) {
      console.error('Chat error:', error);
      addMessage({
        role: "assistant",
        content: "🚨 Oops! I encountered an error. Please try again or contact support if the issue persists."
      });
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const handleQuickAction = (action: typeof QUICK_ACTIONS[0]) => {
    handleSend(action.query);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFeedback = async (messageId: string, type: 'like' | 'dislike' | null) => {
    updateMessage(messageId, { feedback: type as any });

    const message = activeSession?.messages.find(m => m.id === messageId);
    if (message && message.role === "assistant") {
      try {
        await submitFeedback({
          messageId,
          feedbackType: type!,
          question: "",
          answer: message.content
        });
      } catch (error) {
        console.error('Feedback error:', error);
      }
    }
  };

  return (
    <ChatErrorBoundary>
      <Layout>
        <div className={`flex h-screen transition-all duration-300 ${
          isDarkMode ? 'bg-gray-900' : 'bg-gradient-to-br from-blue-50 via-white to-purple-50'
        }`}>
          {/* Modern Sidebar */}
          <div className={`transition-all duration-300 ${
            sidebarOpen ? 'w-80' : 'w-0'
          } overflow-hidden`}>
            <Sidebar
              sessions={sessions}
              activeSession={activeSession}
              onSwitchSession={switchSession}
              onDeleteSession={deleteSession}
              onRenameSession={renameSession}
              onNewChat={() => {
                createSession();
                setShowQuickActions(true);
              }}
              isDarkMode={isDarkMode}
              onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
            />
          </div>

          {/* Main Chat Area */}
          <div className="flex-1 flex flex-col relative">
            {/* Modern Header */}
            <div className={`flex items-center justify-between p-4 border-b backdrop-blur-sm ${
              isDarkMode 
                ? 'bg-gray-800/90 border-gray-700' 
                : 'bg-white/90 border-gray-200'
            }`}>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className={`p-2 rounded-lg transition-all hover:scale-110 ${
                    isDarkMode 
                      ? 'hover:bg-gray-700 text-gray-300' 
                      : 'hover:bg-gray-100 text-gray-600'
                  }`}
                >
                  <Menu size={20} />
                </button>
                
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                      <Sparkles size={16} className="text-white" />
                    </div>
                    <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white"></div>
                  </div>
                  <div>
                    <h1 className={`font-bold text-lg ${
                      isDarkMode ? 'text-white' : 'text-gray-800'
                    }`}>VU Smart Assistant</h1>
                    <p className={`text-xs ${
                      isDarkMode ? 'text-gray-400' : 'text-gray-500'
                    }`}>Always online • Instant responses</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1 px-3 py-1 rounded-full bg-green-100 text-green-800 text-xs font-medium">
                  <Zap size={12} />
                  <span>Instant AI</span>
                </div>
                <button
                  onClick={() => setIsDarkMode(!isDarkMode)}
                  className={`p-2 rounded-lg transition-all ${
                    isDarkMode 
                      ? 'hover:bg-gray-700 text-gray-300' 
                      : 'hover:bg-gray-100 text-gray-600'
                  }`}
                >
                  <Settings size={16} />
                </button>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6 flex flex-col">
              {activeSession?.messages.map((message, index) => (
                <div
                  key={message.id}
                  className={`flex gap-3 animate-in slide-in-from-bottom-4 duration-500 ${
                    message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                  }`}
                >
                  {/* Avatar */}
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-blue-500 to-blue-600'
                      : 'bg-gradient-to-r from-purple-500 to-pink-500'
                  }`}>
                    {message.role === 'user' ? (
                      <User size={16} className="text-white" />
                    ) : (
                      <Bot size={16} className="text-white" />
                    )}
                  </div>

                  {/* Message Content */}
                  <div className={`flex-1 max-w-3xl ${
                    message.role === 'user' ? 'text-right' : 'text-left'
                  }`}>
                    <ModernChatMessage
                      message={message}
                      onFeedback={handleFeedback}
                      isDarkMode={isDarkMode}
                    />
                  </div>
                </div>
              ))}

              {/* Quick Action Suggestions - Show only with welcome message and when no other messages */}
              {showQuickActions && activeSession?.messages.length === 1 && (
                <div className="space-y-4 animate-in fade-in-50 duration-700 mt-8">
                  <div className={`text-center text-sm ${
                    isDarkMode ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    <p className="mb-4">💡 <strong>Try asking about:</strong></p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                    {QUICK_ACTIONS.map((action, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleQuickAction(action)}
                        className={`p-4 rounded-xl border-2 border-dashed transition-all hover:scale-105 hover:shadow-lg text-left ${
                          isDarkMode
                            ? 'border-gray-600 hover:border-purple-500 hover:bg-gray-800'
                            : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50'
                        }`}
                      >
                        <span className={`font-medium text-sm ${
                          isDarkMode ? 'text-gray-200' : 'text-gray-700'
                        }`}>{action.text}</span>
                      </button>
                    ))}
                  </div>
                  <div className={`text-center text-xs mt-6 ${
                    isDarkMode ? 'text-gray-500' : 'text-gray-500'
                  }`}>
                    Or type anything in the box below to ask your own question
                  </div>
                </div>
              )}

              {/* Typing Indicator */}
              {isLoading && (
                <div className="flex gap-3 animate-in slide-in-from-bottom-4 duration-300">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                    <Bot size={16} className="text-white" />
                  </div>
                  <div className={`flex items-center gap-2 px-4 py-3 rounded-2xl max-w-xs ${
                    isDarkMode ? 'bg-gray-700' : 'bg-white shadow-sm'
                  }`}>
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"></div>
                    </div>
                    <span className={`text-sm ${
                      isDarkMode ? 'text-gray-300' : 'text-gray-600'
                    }`}>AI is thinking...</span>
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            {/* Modern Input Area */}
            <div className={`p-4 border-t backdrop-blur-sm ${
              isDarkMode 
                ? 'bg-gray-800/90 border-gray-700' 
                : 'bg-white/90 border-gray-200'
            }`}>
              <div className="max-w-4xl mx-auto">
                <div className={`flex gap-3 p-3 rounded-2xl border-2 transition-all focus-within:border-purple-400 ${
                  isDarkMode 
                    ? 'bg-gray-700 border-gray-600' 
                    : 'bg-white border-gray-200 shadow-lg'
                }`}>
                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="Ask any question about admissions, fees, programs, placements, campus life, deadlines... anything about VU!"
                    className={`flex-1 resize-none border-0 outline-none bg-transparent placeholder-gray-400 min-h-[20px] max-h-[120px] ${
                      isDarkMode ? 'text-white' : 'text-gray-800'
                    }`}
                    rows={1}
                    disabled={isLoading}
                  />
                  
                  <div className="flex items-end gap-2">
                    {isLoading ? (
                      <button
                        onClick={() => setIsLoading(false)}
                        className="p-2 rounded-xl bg-red-500 hover:bg-red-600 text-white transition-all hover:scale-105"
                      >
                        <StopCircle size={18} />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleSend()}
                        disabled={!input.trim()}
                        className={`p-2 rounded-xl transition-all hover:scale-105 ${
                          input.trim() 
                            ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg' 
                            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        }`}
                      >
                        <Send size={18} />
                      </button>
                    )}
                  </div>
                </div>
                
                <div className={`text-xs text-center mt-2 ${
                  isDarkMode ? 'text-gray-500' : 'text-gray-400'
                }`}>
                  Press Enter to send • Shift+Enter for new line • Powered by AI
                </div>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </ChatErrorBoundary>
  );
}