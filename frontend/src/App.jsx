// frontend/src/App.jsx
import React, { useState, useRef, useEffect } from 'react';
import './App.css';

const Message = ({ message, isUser, mcpsUsed, timestamp }) => (
  <div className={`message ${isUser ? 'user-message' : 'bot-message'}`}>
    <div className="message-content">
      <div className="message-text">{message}</div>
      {!isUser && mcpsUsed && mcpsUsed.length > 0 && (
        <div className="mcps-used">
          <span className="mcps-label">Sources:</span>
          {mcpsUsed.map(mcp => (
            <span key={mcp} className={`mcp-badge ${mcp}`}>
              {mcp.toUpperCase()}
            </span>
          ))}
        </div>
      )}
    </div>
    <div className="message-timestamp">{timestamp}</div>
  </div>
);

const TypingIndicator = () => (
  <div className="message bot-message">
    <div className="message-content">
      <div className="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  </div>
);

const MCPSelector = ({ availableMcps, selectedMcps, onToggle, suggestedMcps }) => (
  <div className="mcp-selector">
    <div className="mcp-header">
      <span>Choose Systems:</span>
      <button 
        className="auto-select-btn"
        onClick={() => suggestedMcps.forEach(onToggle)}
        disabled={suggestedMcps.length === 0}
      >
        Auto-select ({suggestedMcps.length})
      </button>
    </div>
    <div className="mcp-options">
      {availableMcps.map(mcp => (
        <button
          key={mcp.id}
          className={`mcp-option ${selectedMcps.includes(mcp.id) ? 'selected' : ''} ${suggestedMcps.includes(mcp.id) ? 'suggested' : ''}`}
          onClick={() => onToggle(mcp.id)}
          title={mcp.description}
        >
          {mcp.name}
          {suggestedMcps.includes(mcp.id) && <span className="suggested-indicator">*</span>}
        </button>
      ))}
    </div>
    <div className="mcp-info">
      {selectedMcps.length === 0 ? (
        <span>Using smart routing</span>
      ) : (
        <span>Selected: {selectedMcps.join(', ')}</span>
      )}
    </div>
  </div>
);

const App = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hi! I'm your Enterprise Integration Assistant. I can help you search across JIRA, Confluence, and Bitbucket. What would you like to know?",
      isUser: false,
      timestamp: new Date().toLocaleTimeString(),
      mcpsUsed: []
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [availableMcps, setAvailableMcps] = useState([]);
  const [selectedMcps, setSelectedMcps] = useState([]);
  const [suggestedMcps, setSuggestedMcps] = useState([]);
  const [showMcpSelector, setShowMcpSelector] = useState(false);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    fetchAvailableMcps();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchAvailableMcps = async () => {
    try {
      const response = await fetch('/api/mcps');
      const data = await response.json();
      setAvailableMcps(data.mcps);
    } catch (error) {
      console.error('Failed to fetch MCPs:', error);
    }
  };

  const toggleMcp = (mcpId) => {
    setSelectedMcps(prev => 
      prev.includes(mcpId) 
        ? prev.filter(id => id !== mcpId)
        : [...prev, mcpId]
    );
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue,
      isUser: true,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: inputValue,
          selected_mcps: selectedMcps.length > 0 ? selectedMcps : undefined
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Update suggested MCPs for next query
      setSuggestedMcps(data.suggested_mcps || []);

      const botMessage = {
        id: Date.now() + 1,
        text: data.synthesis,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        mcpsUsed: data.mcps_used
      };

      setMessages(prev => [...prev, botMessage]);

    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        text: `Sorry, I encountered an error: ${error.message}`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        mcpsUsed: []
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 1,
        text: "Chat cleared. How can I help you?",
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        mcpsUsed: []
      }
    ]);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>Enterprise Assistant</h1>
          <div className="header-controls">
            <button 
              className={`toggle-mcp-btn ${showMcpSelector ? 'active' : ''}`}
              onClick={() => setShowMcpSelector(!showMcpSelector)}
            >
              Systems
            </button>
            <button className="clear-btn" onClick={clearChat}>
              Clear
            </button>
          </div>
        </div>
        
        {showMcpSelector && (
          <MCPSelector
            availableMcps={availableMcps}
            selectedMcps={selectedMcps}
            onToggle={toggleMcp}
            suggestedMcps={suggestedMcps}
          />
        )}
      </header>

      <main className="chat-container">
        <div className="messages">
          {messages.map(message => (
            <Message
              key={message.id}
              message={message.text}
              isUser={message.isUser}
              mcpsUsed={message.mcpsUsed}
              timestamp={message.timestamp}
            />
          ))}
          {isLoading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask me about issues, documentation, or repositories..."
              className="message-input"
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="send-button"
            >
              {isLoading ? '...' : 'Send'}
            </button>
          </div>
          
          {suggestedMcps.length > 0 && (
            <div className="quick-suggestions">
              <span>Suggested for your query:</span>
              {suggestedMcps.map(mcp => (
                <span key={mcp} className={`suggestion-badge ${mcp}`}>
                  {mcp.toUpperCase()}
                </span>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default App;