import React from 'react';
import ReactMarkdown from 'react-markdown';

const Message = ({ message, isUser, mcpsUsed = [], timestamp, isInContext = false }) => {
  return (
    <div className={`message ${isUser ? 'user' : 'assistant'} ${isInContext ? 'in-context' : ''}`}>
      <div className={`avatar ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? 'U' : 'A'}
      </div>
      
      <div className="message-content">
        <div className="message-text">
          {isUser ? (
            message
          ) : (
            <ReactMarkdown>{message}</ReactMarkdown>
          )}
        </div>
        
        <div className="message-meta">
          {mcpsUsed.length > 0 && (
            <div className="mcps-used">
              {mcpsUsed.map(mcp => (
                <span key={mcp} className={`mcp-badge ${mcp}`}>
                  {mcp.toUpperCase()}
                </span>
              ))}
            </div>
          )}
          <span className="timestamp">{timestamp}</span>
          {isInContext && (
            <span className="context-indicator-small">📝 Context</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default Message;