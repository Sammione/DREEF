import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Send, Plus, MessageSquare, Menu, X, Copy, RotateCcw, 
  Settings, LogOut, ChevronLeft, ChevronRight, Bot, 
  User as UserIcon, Sparkles, Terminal
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Markdown from 'markdown-to-jsx';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [sessionId, setSessionId] = useState('session-' + Math.random().toString(36).substr(2, 9));
  const [chatHistory, setChatHistory] = useState([]);
  
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
    autoResizeTextarea();
  }, [messages, input]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        // Simplified: Fetch names of files or previous sessions
        const response = await axios.get(`${API_BASE_URL}/files`);
        if (response.data.files) {
          setChatHistory(response.data.files);
        }
      } catch (error) {
        console.error("Error fetching history:", error);
      }
    };
    fetchHistory();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const autoResizeTextarea = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setSessionId('session-' + Math.random().toString(36).substr(2, 9));
  };

  const handleSend = async (customMessage = null) => {
    const textToSend = customMessage || input;
    if (!textToSend.trim() || isLoading) return;

    const userMessage = { role: 'user', content: textToSend };
    setMessages(prev => [...prev, userMessage]);
    if (!customMessage) setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        user_id: 'user1',
        session_id: sessionId,
        message: textToSend
      });

      const aiMessage = { role: 'ai', content: response.data.response };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages(prev => [...prev, { 
        role: 'ai', 
        content: '**System Error**: Unable to reach intelligence layer. Please check your connection.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-app">
      {/* Sidebar */}
      <aside className={`sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          {!isSidebarCollapsed && <span className="brand">DREEF AI</span>}
          <button className="new-chat-btn" onClick={handleNewChat} title="New Intelligence Session">
            <Plus size={16} />
            {!isSidebarCollapsed && "New Chat"}
          </button>
        </div>

        <div className="history-section">
          {!isSidebarCollapsed && chatHistory.length > 0 && chatHistory.slice(0, 15).map((chat, i) => (
            <div key={i} className="history-item" onClick={() => handleSend(`Tell me about ${chat.name}`)}>
              <MessageSquare size={14} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
              {chat.name}
            </div>
          ))}
        </div>

        <div className="user-profile">
          <div className="avatar">AD</div>
          {!isSidebarCollapsed && (
            <div className="flex-1 overflow-hidden" style={{ marginLeft: '10px' }}>
              <div className="text-xs font-bold truncate">ADMINISTRATOR</div>
              <div className="text-[10px] text-slate-500">Enterprise ID</div>
            </div>
          )}
          <Settings size={14} className="cursor-pointer hover:text-emerald-400" />
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header className="main-header">
          <div className="flex items-center gap-3">
            <button className="toggle-sidebar" onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}>
              {isSidebarCollapsed ? <Menu size={20} /> : <ChevronLeft size={20} />}
            </button>
            <span className="font-semibold text-sm">DREEF CHAT AI</span>
          </div>
          <div className="flex gap-4">
            <Terminal size={14} className="text-slate-500 cursor-pointer hover:text-emerald-400" />
          </div>
        </header>

        <div className="messages-container">
          {messages.length === 0 ? (
            <div style={{ textAlign: 'center', opacity: 0.5, marginTop: '20vh' }}>
              <Sparkles size={48} style={{ margin: '0 auto 1.5rem', color: '#10b981' }} />
              <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>How can I help you today?</h2>
              <p style={{ fontSize: '0.9rem' }}>Analyze documents, check risks, or ask for insights.</p>
            </div>
          ) : (
            <AnimatePresence>
              {messages.map((msg, index) => (
                <motion.div 
                  key={index} 
                  className={`message-box ${msg.role}`}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4 }}
                >
                  <div className={`avatar-icon ${msg.role}`}>
                    {msg.role === 'ai' ? <Bot size={18} fill="white" /> : <UserIcon size={18} />}
                  </div>
                  <div className="bubble-wrapper">
                    <div className="bubble">
                      {msg.role === 'ai' ? (
                        <div className="markdown-body">
                          <Markdown>{msg.content}</Markdown>
                        </div>
                      ) : (
                        <div className="user-text">
                          {msg.content}
                        </div>
                      )}
                    </div>
                    {msg.role === 'ai' && (
                      <div className="bubble-actions">
                        <button className="action-icon" onClick={() => copyToClipboard(msg.content)}>
                          <Copy size={12} />
                          Copy
                        </button>
                        <button className="action-icon" onClick={() => handleSend(messages[index - 1].content)}>
                          <RotateCcw size={12} />
                          Regenerate
                        </button>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
          
          {isLoading && (
            <div className="message-box ai">
              <div className="avatar-icon ai">
                <Bot size={18} fill="white" />
              </div>
              <div className="bubble-wrapper">
                <div className="thinking">
                  <div className="dot-flashing"></div>
                  Thinking...
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <section className="input-area">
          <div className="input-wrapper">
            <textarea
              ref={textareaRef}
              className="chat-input"
              placeholder="Ask anything about your documents, risks, or insights..."
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button 
              className="send-button" 
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
            >
              <Send size={16} />
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
