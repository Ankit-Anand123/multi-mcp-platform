import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatArea from './components/ChatArea';
import WelcomeScreen from './components/WelcomeScreen';
import InputArea from './components/InputArea';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [lastUsedSystems, setLastUsedSystems] = useState([]);

  // Available systems for the sidebar
  const availableSystems = [
    {
      id: 'jira',
      name: 'Jira',
      description: 'Issue tracking and project management',
      icon: '🎫',
      status: 'connected'
    },
    {
      id: 'confluence',
      name: 'Confluence',
      description: 'Documentation and knowledge base',
      icon: '📚',
      status: 'connected'
    },
    {
      id: 'bitbucket',
      name: 'Bitbucket',
      description: 'Code repositories and pull requests',
      icon: '🔧',
      status: 'connected'
    }
  ];

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const startNewChat = () => {
    setMessages([]);
    setLastUsedSystems([]);
  };

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    const userMessage = {
      text,
      isUser: true,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      mcpsUsed: []
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Prepare conversation history (last 5 messages for context)
      const conversationHistory = messages.slice(-5).map(msg => ({
        text: msg.text,
        is_user: msg.isUser,
        timestamp: msg.timestamp,
        mcps_used: msg.mcpsUsed || []
      }));

      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: text,
          conversation_history: conversationHistory
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const assistantMessage = {
        text: data.synthesis || data.response,
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mcpsUsed: data.mcps_used || []
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update last used systems for context
      if (data.mcps_used && data.mcps_used.length > 0) {
        setLastUsedSystems(data.mcps_used);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage = {
        text: `Sorry, I encountered an error: ${error.message}`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mcpsUsed: []
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendExampleMessage = (text) => {
    sendMessage(text);
  };

  // Test backend connection on component mount
  useEffect(() => {
    const testConnection = async () => {
      try {
        const response = await fetch('/api/health');
        if (response.ok) {
          console.log('✅ Backend connection successful');
        } else {
          console.warn('⚠️ Backend health check failed:', response.status);
        }
      } catch (error) {
        console.error('❌ Backend connection failed:', error);
      }
    };

    testConnection();
  }, []);

  // Check if conversation has started
  const hasMessages = messages.length > 0;

  return (
    <div className="app">
      <Sidebar 
        collapsed={sidebarCollapsed}
        onToggle={toggleSidebar}
        onNewChat={startNewChat}
        systems={availableSystems}
        lastUsedSystems={lastUsedSystems}
      />
      
      <div className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <Header 
          onToggleSidebar={toggleSidebar}
          sidebarCollapsed={sidebarCollapsed}
        />
        
        <div className="chat-container">
          {!hasMessages ? (
            <WelcomeScreen onSendExample={sendExampleMessage} />
          ) : (
            <ChatArea 
              messages={messages} 
              isLoading={isLoading}
            />
          )}
        </div>
        
        <InputArea 
          onSendMessage={sendMessage}
          isLoading={isLoading}
          onSendExample={sendExampleMessage}
          lastUsedSystems={lastUsedSystems}
          hasMessages={hasMessages} // Pass this to hide suggestions after first message
          messagesLength={messages.length} // Pass message count for context indicator
        />
      </div>
    </div>
  );
};

export default App;