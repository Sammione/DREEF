import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Send, Plus, MessageSquare, Copy, RotateCcw, 
  Settings, LogOut, Bot, User as UserIcon, Sparkles, Terminal
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Markdown from 'markdown-to-jsx';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('session-' + Math.random().toString(36).substr(2, 9));
  const [chatHistory, setChatHistory] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
    autoResizeTextarea();
  }, [messages, input]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
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

  const toggleSettings = () => {
    setShowSettings(!showSettings);
  };

  return (
    <div className="chat-app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
           <span className="brand">DREEF AI</span>
        </div>

        <button className="new-chat-btn" onClick={handleNewChat} title="New Intelligence Session">
          <Plus size={16} />
          New Chat
        </button>

        <div className="history-section">
          {chatHistory.length > 0 && chatHistory.slice(0, 15).map((chat, i) => (
            <div key={i} className="history-item" onClick={() => handleSend(`Tell me about ${chat.name}`)}>
              <MessageSquare size={14} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
              {chat.name}
            </div>
          ))}
        </div>

        {/* Footer Area with Settings */}
        <div style={{ padding: '1rem', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>v2.5 Stable</div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <Settings 
              size={18} 
              className="cursor-pointer hover:text-emerald-400 transition-colors" 
              onClick={toggleSettings}
            />
            <LogOut size={18} className="cursor-pointer hover:text-red-400 transition-colors" />
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header className="main-header">
          <div className="flex items-center gap-3">
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
              
              {showSettings && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="settings-card"
                  style={{ 
                    marginTop: '2rem', 
                    padding: '1.5rem', 
                    background: 'var(--bg-card)', 
                    borderRadius: '12px', 
                    border: '1px solid var(--border)',
                    maxWidth: '400px',
                    margin: '2rem auto'
                  }}
                >
                  <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#fff' }}>System Settings</h3>
                  <div style={{ textAlign: 'left', fontSize: '0.85rem' }}>
                    <div style={{ marginBottom: '10px', display: 'flex', justifyContent: 'space-between' }}>
                      <span>Model</span>
                      <span style={{ color: 'var(--accent)' }}>GPT-4o Enterprise</span>
                    </div>
                    <div style={{ marginBottom: '10px', display: 'flex', justifyContent: 'space-between' }}>
                      <span>API Status</span>
                      <span style={{ color: '#10b981' }}>Connected</span>
                    </div>
                  </div>
                  <button 
                    onClick={toggleSettings}
                    style={{ marginTop: '1rem', background: 'var(--accent)', border: 'none', color: '#fff', padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer' }}
                  >
                    Close Settings
                  </button>
                </motion.div>
              )}
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

              {showSettings && (
                 <motion.div 
                 initial={{ opacity: 0 }}
                 animate={{ opacity: 1 }}
                 style={{ 
                   position: 'fixed', 
                   top: '50%', 
                   left: '50%', 
                   transform: 'translate(-50%, -50%)',
                   zIndex: 1000,
                   background: 'rgba(0,0,0,0.8)',
                   width: '100%',
                   height: '100%',
                   display: 'flex',
                   alignItems: 'center',
                   justifyContent: 'center'
                 }}
                 onClick={toggleSettings}
               >
                 <div 
                   style={{ 
                     background: 'var(--bg-card)', 
                     padding: '2rem', 
                     borderRadius: '16px', 
                     border: '1px solid var(--border)',
                     minWidth: '320px',
                     boxShadow: '0 20px 50px rgba(0,0,0,0.5)'
                   }}
                   onClick={(e) => e.stopPropagation()}
                 >
                   <h3 style={{ marginBottom: '1.5rem', color: '#fff' }}>System Settings</h3>
                   <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Connection URL</span>
                        <code style={{ color: 'var(--accent)' }}>{API_BASE_URL}</code>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Version</span>
                        <span>2.5.0-stable</span>
                      </div>
                   </div>
                   <button 
                     onClick={toggleSettings}
                     style={{ width: '100%', marginTop: '2rem', background: 'var(--accent)', border: 'none', color: '#fff', padding: '0.75rem', borderRadius: '8px', cursor: 'pointer' }}
                   >
                     Done
                   </button>
                 </div>
               </motion.div>
              )}
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
