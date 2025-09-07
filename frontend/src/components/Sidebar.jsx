import React from 'react';

const Sidebar = ({ 
  collapsed, 
  onToggle, 
  onNewChat, 
  systems, 
  lastUsedSystems = []
}) => {
  return (
    <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewChat}>
          + New Chat
        </button>
        <button className="sidebar-toggle" onClick={onToggle}>
          ×
        </button>
      </div>

      <div className="systems-section">
        <div className="systems-header">Connected Systems</div>
        <div className="systems-subtitle">
          Automatically selected based on your queries
        </div>
        
        {systems.map(system => {
          const isRecentlyUsed = lastUsedSystems.includes(system.id);
          const isActive = isRecentlyUsed;
          
          return (
            <div 
              key={system.id}
              className={`system-item ${isActive ? 'active' : ''} ${isRecentlyUsed ? 'recently-used' : ''}`}
            >
              <div className="system-info">
                <div 
                  className={`system-icon ${system.id}`}
                  style={{ backgroundColor: system.color }}
                >
                  {system.icon}
                </div>
                <div className="system-details">
                  <div className="system-name">{system.name}</div>
                  <div className="system-description">{system.description}</div>
                </div>
              </div>
              
              <div className="system-status">
                {isRecentlyUsed ? (
                  <div className="status-badge active">
                    <div className="status-dot"></div>
                    <span>Used</span>
                  </div>
                ) : (
                  <div className="status-badge available">
                    <div className="status-dot"></div>
                    <span>Ready</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="ai-insights">
        <div className="insights-header">🧠 AI Insights</div>
        <div className="insights-content">
          <p>I automatically choose the best systems for each question:</p>
          <ul>
            <li><strong>Jira</strong> - for issues, tickets, sprints</li>
            <li><strong>Confluence</strong> - for docs, guides</li>
            <li><strong>Bitbucket</strong> - for code, repos, PRs</li>
          </ul>
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="connection-status">
          <div className="status-indicator online" />
          <span>All systems connected</span>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;