import React from 'react';

const TypingIndicator = ({ isStreaming = false }) => {
  return (
    <div className="typing-indicator">
      <div className="avatar assistant">A</div>
      <div className="message-content">
        <div className="typing-dots">
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
        </div>
        
        {isStreaming && (
          <div className="streaming-indicator">
            <span className="streaming-text">🔄 Streaming response...</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default TypingIndicator;