import React from 'react';

const WelcomeScreen = ({ onSendExample }) => {
  // Reduced to only 3 key examples instead of 6
  const examples = [
    {
      title: '🎫 Issue Management',
      description: 'Get tickets, project status, and sprint insights',
      prompt: 'Show me my high priority tickets for this sprint',
      systems: ['Jira'],
      gradient: 'from-blue-500 to-blue-600'
    },
    {
      title: '📚 Documentation',
      description: 'Search knowledge base and technical docs',
      prompt: 'Find documentation about our authentication process',
      systems: ['Confluence'],
      gradient: 'from-purple-500 to-purple-600'
    },
    {
      title: '🔧 Code & Reviews',
      description: 'Analyze repositories and pull requests',
      prompt: 'What pull requests need my review?',
      systems: ['Bitbucket'],
      gradient: 'from-green-500 to-green-600'
    }
  ];

  return (
    <div className="welcome-screen">
      <div className="welcome-content">
        <h2 className="welcome-title">How can I help you today?</h2>
        <p className="welcome-subtitle">
          I automatically connect to Jira, Confluence, and Bitbucket based on your questions. Just ask naturally!
        </p>
        
        <div className="ai-features">
          <div className="feature-badge">
            <span className="feature-icon">🧠</span>
            <span>Smart System Selection</span>
          </div>
          <div className="feature-badge">
            <span className="feature-icon">🔗</span>
            <span>Cross-Platform Insights</span>
          </div>
          <div className="feature-badge">
            <span className="feature-icon">⚡</span>
            <span>Instant Results</span>
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
              <strong>Smart Integration:</strong> I analyze your questions and automatically choose the right systems to give you comprehensive answers.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen;