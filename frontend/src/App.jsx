import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Send, Plus, History, LogOut, User, MessageSquare, 
  RefreshCcw, FileText, Globe, Search, MoreVertical, 
  Settings, HelpCircle, ChevronLeft, Bot, User as UserIcon,
  Zap, Paperclip, Shield, Database, ExternalLink, Info
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Markdown from 'markdown-to-jsx';

const API_BASE_URL = 'http://localhost:8000';

const WelcomeScreen = ({ onSampleClick, projectsCount }) => (
  <motion.div 
    className="welcome-container"
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 0.5 }}
  >
    <div className="welcome-header">
      <div className="logo-large">
        <Zap size={32} fill="white" />
      </div>
      <h1>DRFEER AI Intelligence</h1>
      <p className="subtitle">Enterprise Knowledge Base & DataRoom Analysis Assistant</p>
    </div>

    <div className="stats-row">
      <div className="stat-card">
        <Database size={20} className="text-emerald-500" />
        <div className="stat-val">{projectsCount || 0}</div>
        <div className="stat-label">Indexed Docs</div>
      </div>
      <div className="stat-card">
        <Shield size={20} className="text-blue-500" />
        <div className="stat-val">Secure</div>
        <div className="stat-label">Encryption</div>
      </div>
      <div className="stat-card">
        <Globe size={20} className="text-cyan-500" />
        <div className="stat-val">Live</div>
        <div className="stat-label">SharePoint Sync</div>
      </div>
    </div>

    <div className="suggested-queries">
      <h3>Quick Actions</h3>
      <div className="query-grid">
        <button className="query-btn" onClick={() => onSampleClick("Summarize the main points of the latest transaction memos.")}>
          <MessageSquare size={14} />
          Summarize Transaction Memos
        </button>
        <button className="query-btn" onClick={() => onSampleClick("What are the key risks identified in the BII folder?")}>
          <Info size={14} />
          Analyze BII Risks
        </button>
        <button className="query-btn" onClick={() => onSampleClick("Check for any exclusivity agreements signed in 2023.")}>
          <FileText size={14} />
          Find Exclusivity Agreements
        </button>
        <button className="query-btn" onClick={() => onSampleClick("List the primary participants in the InfraCredit arrangement.")}>
          <Search size={14} />
          Query InfraCredit Details
        </button>
      </div>
    </div>
  </motion.div>
);

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncedFiles, setSyncedFiles] = useState([]);
  const [sessionId] = useState('session-' + Math.random().toString(36).substr(2, 9));
  
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
    autoResizeTextarea();
  }, [messages, input]);

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/files`);
        if (response.data.files) {
          setSyncedFiles(response.data.files);
        }
      } catch (error) {
        console.error("Error fetching files:", error);
      }
    };
    fetchFiles();
    
    // Auto-fetch every 30s if not syncing
    const interval = setInterval(() => {
      if (!isSyncing) fetchFiles();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [isSyncing]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const autoResizeTextarea = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
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
      setMessages(prev => [...prev, { role: 'ai', content: '**System Error**: Unable to reach intelligence layer. Verify backend connectivity on port 8000.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSync = async () => {
    if (isSyncing) return;
    setIsSyncing(true);
    try {
      await axios.post(`${API_BASE_URL}/ingest`);
    } catch (error) {
      console.error("Sync Error:", error);
    } finally {
      setIsSyncing(false);
    }
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
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-logo">
            <Zap size={18} fill="white" />
          </div>
          <span className="brand-name">DRFEER CORE</span>
          <div className="status-badge live">
            <span className="pulsate"></span>
            LIVE
          </div>
        </div>

        <button className="new-chat-btn" onClick={() => setMessages([])}>
          <Plus size={16} />
          New Intelligence Session
        </button>

        <div className="history-section">
          <div className="section-label">
            <Database size={12} />
            Knowledge Assets ({syncedFiles.length})
          </div>
          <div className="knowledge-list">
            {syncedFiles.length === 0 ? (
              <div className="empty-knowledge">
                <RefreshCcw size={20} className="mb-2 opacity-50" />
                No documents indexed yet.
              </div>
            ) : (
              syncedFiles.slice(0, 50).map((file, i) => (
                <div key={i} className="knowledge-item" title={file.name}>
                  <FileText size={14} className="text-emerald-500" />
                  <span className="truncate">{file.name}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="user-profile">
          <div className="avatar">AD</div>
          <div className="flex-1 overflow-hidden">
            <div className="text-xs font-bold truncate">ADMINISTRATOR</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest">Enterprise Access</div>
          </div>
          <div className="flex gap-2">
            <Settings size={14} className="text-slate-500 cursor-pointer hover:text-emerald-400" />
            <LogOut size={14} className="text-slate-500 cursor-pointer hover:text-red-400" />
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="main-content">
        <header className="main-header">
          <div className="flex items-center gap-3">
             <Bot size={20} className="text-emerald-500" />
             <span className="font-semibold text-sm">AI Analysis Engine v2.4</span>
          </div>
          <div className="flex gap-4">
            <button 
              className={`sync-btn ${isSyncing ? 'loading' : ''}`}
              onClick={handleSync}
              disabled={isSyncing}
            >
              <RefreshCcw size={14} />
              {isSyncing ? 'Syncing...' : 'Sync DataRoom'}
            </button>
          </div>
        </header>

        <div className="messages-area">
          {messages.length === 0 ? (
            <WelcomeScreen projectsCount={syncedFiles.length} onSampleClick={(q) => handleSend(q)} />
          ) : (
            <AnimatePresence>
              {messages.map((msg, index) => (
                <motion.div 
                  key={index} 
                  className={`message-wrapper ${msg.role}`}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                >
                  <div className="message-icon">
                    {msg.role === 'ai' ? <Zap size={18} fill="white" /> : <UserIcon size={18} />}
                  </div>
                  <div className={`message-bubble ${msg.role}`}>
                    {msg.role === 'ai' ? (
                      <div className="markdown">
                        <Markdown>{msg.content}</Markdown>
                      </div>
                    ) : (
                      <div className="user-text">{msg.content}</div>
                    )}
                  </div>
                </motion.div>
              ))}

              {isLoading && (
                <motion.div className="message-wrapper ai" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <div className="message-icon"><Zap size={18} fill="white" /></div>
                  <div className="message-bubble ai italic text-slate-500">
                    <div className="flex items-center gap-2">
                      <Search size={14} className="animate-pulse" />
                      Analyzing knowledge base...
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <section className="input-section">
          <div className="input-container">
            <button className="action-btn" title="System Settings">
              <MoreVertical size={18} />
            </button>
            <textarea
              ref={textareaRef}
              placeholder="Query documents, analyze risks or request summaries..."
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button 
              className="send-btn" 
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
            >
              <Send size={16} />
            </button>
          </div>
          <div className="disclaimer">
            <Shield size={10} />
            Encrypted Corporate Assistant. Responses guaranteed by Internal Compliance.
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
