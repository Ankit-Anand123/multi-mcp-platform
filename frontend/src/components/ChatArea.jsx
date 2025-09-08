import React, { useEffect, useRef } from 'react';
import Message from './Message';
import TypingIndicator from './TypingIndicator';

const ChatArea = ({ messages, isLoading }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Determine which messages are in context (last 5)
  const getContextIndicator = (index) => {
    if (messages.length <= 5) return true; // All messages are in context if 5 or fewer
    return index >= messages.length - 5; // Last 5 messages are in context
  };

  return (
    <div className="messages">
      {messages.map((message, index) => (
        <Message
          key={message.id || index}
          message={message.text}
          isUser={message.isUser}
          mcpsUsed={message.mcpsUsed}
          timestamp={message.timestamp}
          isInContext={getContextIndicator(index)}
        />
      ))}
      
      {isLoading && <TypingIndicator />}
      
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatArea;