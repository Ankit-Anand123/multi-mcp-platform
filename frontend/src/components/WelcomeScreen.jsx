import React from 'react';

const WelcomeScreen = ({ onSendExample }) => {
  const examples = [
    {
      title: '🎫 Issue Tracking',
      description: 'I\'ll automatically check Jira for tickets and project status',
      prompt: 'Show me my high priority tickets for this sprint',
      systems: ['Jira'],
      gradient: 'from-blue-500 to-blue-600'
    },
    {
      title: '📚 Knowledge Search',
      description: 'I\'ll search Confluence for documentation and guides',
      prompt: 'Find documentation about our authentication process',
      systems: ['Confluence'],
      gradient: 'from-purple-500 to-purple-600'
    },
    {
      title: '🔧 Code Analysis',
      description: 'I\'ll examine Bitbucket for repository insights and PRs',
      prompt: 'What pull requests need my review?',
      systems: ['Bitbucket'],
      gradient: 'from-green-500 to-green-600'
    },
    {
      title: '🔄 Cross-System Insights',
      description: 'I\'ll connect data across multiple systems for deeper analysis',
      prompt: 'Find issues related to the user authentication feature and any related documentation',
      systems: ['Jira', 'Confluence', 'Bitbucket'],
      gradient: 'from-orange-500 to-pink-500'
    },
    {
      title: '📊 Project Overview',
      description: 'I\'ll gather comprehensive project status from all systems',
      prompt: 'Give me a complete overview of the mobile app project',
      systems: ['Jira', 'Confluence', 'Bitbucket'],
      gradient: 'from-indigo-500 to-blue-500'
    },
    {
      title: '🚀 Release Planning',
      description: 'I\'ll help plan releases by analyzing issues, docs, and code',
      prompt: 'What\'s ready for our next release and what might be missing?',
      systems: ['Jira', 'Confluence', 'Bitbucket'],
      gradient: 'from-red-500 to-orange-500'
    }
  ];

  return (
    <div className="welcome-screen">
      <div className="welcome-content">
        <h2 className="welcome-title">How can I help you today?</h2>
        <p className="welcome-subtitle">
          I automatically connect to the right systems based on your questions. 
          No need to select anything - just ask!
        </p>
        
        <div className="ai-features">
          <div className="feature-badge">
            <span className="feature-icon">🧠</span>
            <span>AI-Powered System Selection</span>
          </div>
          <div className="feature-badge">
            <span className="feature-icon">🔗</span>
            <span>Cross-System Intelligence</span>
          </div>
          <div className="feature-badge">
            <span className="feature-icon">⚡</span>
            <span>Instant Insights</span>
          </div>
        </div>
        
        <div className="welcome-examples">
          {examples.map((example, index) => (
            <div
              key={index}
              className="example-card"
              onClick={() => onSendExample(example.prompt)}
            >
              <div className="example-header">
                <div className="example-title">{example.title}</div>
                <div className="example-systems">
                  {example.systems.map((system, idx) => (
                    <span key={idx} className={`system-badge ${system.toLowerCase()}`}>
                      {system}
                    </span>
                  ))}
                </div>
              </div>
              <div className="example-description">{example.description}</div>
              <div className="example-prompt">"{example.prompt}"</div>
            </div>
          ))}
        </div>
        
        <div className="welcome-footer">
          <div className="intelligence-note">
            <div className="note-icon">🎯</div>
            <div className="note-content">
              <strong>Smart System Selection:</strong> I analyze your question and automatically 
              choose the best combination of Jira, Confluence, and Bitbucket to give you 
              comprehensive answers. Just ask naturally!
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen;