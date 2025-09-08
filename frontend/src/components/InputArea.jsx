import React, { useState, useRef } from 'react';

const InputArea = ({ 
  onSendMessage, 
  isLoading, 
  onSendExample, 
  lastUsedSystems = [], 
  hasMessages = false, // NEW: Track if conversation has started
  messagesLength = 0  // NEW: Track message count for context indicator
}) => {
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = () => {
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue);
      setInputValue('');
      resetTextareaHeight();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const autoResize = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  };

  const resetTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
    }
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
    autoResize();
  };

  // Smart suggestions based on context and last used systems
  const getSmartSuggestions = () => {
    const baseSuggestions = [
      { text: 'Show me my assigned tickets', category: 'jira', icon: '🎫' },
      { text: 'Find documentation about our API', category: 'confluence', icon: '📚' },
      { text: 'What repos were updated this week?', category: 'bitbucket', icon: '🔧' },
      { text: 'Critical bugs in current sprint', category: 'jira', icon: '🐛' }
    ];

    // If we have last used systems, prioritize those suggestions
    if (lastUsedSystems.length > 0) {
      const prioritySuggestions = baseSuggestions.filter(s => 
        lastUsedSystems.includes(s.category)
      );
      const otherSuggestions = baseSuggestions.filter(s => 
        !lastUsedSystems.includes(s.category)
      );
      return [...prioritySuggestions, ...otherSuggestions].slice(0, 4);
    }

    return baseSuggestions;
  };

  const suggestions = getSmartSuggestions();

  return (
    <div className="input-area">
      {/* Context Indicator - Show when we have conversation context */}
      {hasMessages && messagesLength > 0 && (
        <div className="context-indicator">
          <span className="context-text">
            💬 Using conversation context (last {Math.min(messagesLength, 5)} messages)
            {lastUsedSystems.length > 0 && (
              <span> • Recently used: {lastUsedSystems.map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(', ')}</span>
            )}
          </span>
        </div>
      )}
      
      {/* Suggestions - ONLY show before first message */}
      {!hasMessages && !isLoading && (
        <div className="suggestions">
          <div className="suggestions-header">
            💡 Quick start suggestions:
          </div>
          <div className="suggestions-grid">
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                className={`suggestion-chip ${suggestion.category} ${
                  lastUsedSystems.includes(suggestion.category) ? 'priority' : ''
                }`}
                onClick={() => onSendExample(suggestion.text)}
              >
                <span className="suggestion-icon">{suggestion.icon}</span>
                <span className="suggestion-text">{suggestion.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Input Container - Fixed at Bottom */}
      <div className="input-container">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            placeholder="Ask me anything about your projects, docs, or code..."
            className="message-input"
            rows={1}
            disabled={isLoading}
          />
          <button
            onClick={handleSubmit}
            disabled={!inputValue.trim() || isLoading}
            className="send-button"
          >
            {isLoading ? (
              <div className="loading-spinner">⟳</div>
            ) : (
              '↑'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default InputArea;