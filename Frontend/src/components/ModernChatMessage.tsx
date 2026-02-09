import { Copy, ThumbsUp, ThumbsDown, Check, Sparkles, Clock } from "lucide-react";
import { useState } from "react";
import TypewriterText from './TypewriterText';
import SourceCitation from './SourceCitation';

type Source = {
  category: string;
  filename: string;
  snippet: string;
};

type ChatMessageProps = {
  message: {
    id: string;
    role: "user" | "assistant";
    content: string;
    sources?: Source[];
    feedback?: 'like' | 'dislike';
    timestamp?: Date;
  };
  onFeedback?: (messageId: string, type: 'like' | 'dislike') => void;
  isDarkMode?: boolean;
};

export default function ChatMessage({
  message,
  onFeedback,
  isDarkMode = false
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleFeedback = (type: 'like' | 'dislike') => {
    if (onFeedback) {
      onFeedback(message.id, message.feedback === type ? null as any : type);
    }
  };

  return (
    <div className={`group ${isUser ? 'flex justify-end' : 'flex justify-start'}`}>
      <div className={`max-w-[85%] ${
        isUser 
          ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white' 
          : isDarkMode 
            ? 'bg-gray-700 text-gray-100' 
            : 'bg-white text-gray-800 shadow-sm'
      } rounded-2xl px-4 py-3 relative transition-all duration-300 hover:shadow-lg`}>
        
        {/* Message Content */}
        <div className="space-y-3">
          {isUser ? (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          ) : (
            <TypewriterText 
              text={message.content} 
              className={`whitespace-pre-wrap break-words ${
                isDarkMode ? 'text-gray-100' : 'text-gray-800'
              }`}
            />
          )}

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="space-y-2 border-t border-opacity-20 pt-3">
              <div className="flex items-center gap-1 text-xs opacity-75">
                <Sparkles size={12} />
                <span>Sources:</span>
              </div>
              <div className="space-y-1">
                {message.sources.map((source, index) => (
                  <SourceCitation 
                    key={index} 
                    source={source} 
                    isDarkMode={isDarkMode}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className={`flex items-center justify-between mt-2 pt-2 border-t border-opacity-10 ${
          isUser ? 'border-white' : isDarkMode ? 'border-gray-600' : 'border-gray-200'
        }`}>
          <div className="flex items-center gap-1 text-xs opacity-60">
            <Clock size={10} />
            <span>{message.timestamp ? message.timestamp.toLocaleTimeString() : 'now'}</span>
          </div>

          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {/* Copy Button */}
            <button
              onClick={handleCopy}
              className={`p-1.5 rounded-lg transition-all hover:scale-110 ${
                isUser 
                  ? 'hover:bg-white/20' 
                  : isDarkMode 
                    ? 'hover:bg-gray-600' 
                    : 'hover:bg-gray-100'
              }`}
              title="Copy message"
            >
              {copied ? (
                <Check size={12} className="text-green-400" />
              ) : (
                <Copy size={12} />
              )}
            </button>

            {/* Feedback Buttons (Assistant only) */}
            {!isUser && onFeedback && (
              <>
                <button
                  onClick={() => handleFeedback('like')}
                  className={`p-1.5 rounded-lg transition-all hover:scale-110 ${
                    message.feedback === 'like' 
                      ? 'bg-green-100 text-green-600' 
                      : isDarkMode 
                        ? 'hover:bg-gray-600' 
                        : 'hover:bg-gray-100'
                  }`}
                  title="Like this response"
                >
                  <ThumbsUp size={12} />
                </button>
                <button
                  onClick={() => handleFeedback('dislike')}
                  className={`p-1.5 rounded-lg transition-all hover:scale-110 ${
                    message.feedback === 'dislike' 
                      ? 'bg-red-100 text-red-600' 
                      : isDarkMode 
                        ? 'hover:bg-gray-600' 
                        : 'hover:bg-gray-100'
                  }`}
                  title="Dislike this response"
                >
                  <ThumbsDown size={12} />
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}