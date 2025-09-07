import React from 'react';

const Message = ({ message, isUser, mcpsUsed = [], timestamp }) => {
  return (
    <div className={`message ${isUser ? 'user' : 'assistant'}`}>
      <div className={`avatar ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? 'U' : 'A'}
      </div>
      
      <div className="message-content">
        <div className="message-text">
          {message}
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
        </div>
      </div>
    </div>
  );
};

export default Message;