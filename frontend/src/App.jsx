import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatArea from './components/ChatArea';
import InputArea from './components/InputArea';
import WelcomeScreen from './components/WelcomeScreen';
import './styles/App.css';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [lastUsedSystems, setLastUsedSystems] = useState([]);

  const availableSystems = [
    { id: 'jira', name: 'Jira', icon: 'J', color: '#0052cc', description: 'Issues & Projects' },
    { id: 'confluence', name: 'Confluence', icon: 'C', color: '#0066cc', description: 'Documentation' },
    { id: 'bitbucket', name: 'Bitbucket', icon: 'B', color: '#2684ff', description: 'Repositories' }
  ];

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const startNewChat = () => {
    setMessages([]);
    setLastUsedSystems([]);
  };

  const sendMessage = async (messageText) => {
    if (!messageText.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: messageText,
      isUser: true,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      mcpsUsed: []
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Let the backend automatically determine which MCPs to use
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: messageText,
          // Don't send selected_mcps - let backend decide automatically
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json();

      // Update the systems that were used for this query
      if (data.mcps_used && data.mcps_used.length > 0) {
        setLastUsedSystems(data.mcps_used);
      }

      const assistantMessage = {
        id: Date.now() + 1,
        text: data.synthesis || "I'm here to help! However, I couldn't process that request right now.",
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mcpsUsed: data.mcps_used || []
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Log suggested MCPs for debugging
      if (data.suggested_mcps) {
        console.log('Backend suggested MCPs:', data.suggested_mcps);
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        text: `I apologize, but I'm having trouble connecting right now. Error: ${error.message}`,
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
          {messages.length === 0 ? (
            <WelcomeScreen onSendExample={sendExampleMessage} />
          ) : (
            <ChatArea 
              messages={messages} 
              isLoading={isLoading}
            />
          )}
          
          <InputArea 
            onSendMessage={sendMessage}
            isLoading={isLoading}
            onSendExample={sendExampleMessage}
            lastUsedSystems={lastUsedSystems}
          />
        </div>
      </div>
    </div>
  );
};

export default App;