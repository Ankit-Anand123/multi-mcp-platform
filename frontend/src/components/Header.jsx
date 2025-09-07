import React from 'react';

const Header = ({ onToggleSidebar, sidebarCollapsed }) => {
  return (
    <div className="header">
      <div className="header-left">
        {/* This button will show on mobile AND when sidebar is collapsed */}
        <button 
          className="mobile-menu-btn" 
          onClick={onToggleSidebar}
          style={{ 
            display: sidebarCollapsed ? 'flex' : window.innerWidth <= 768 ? 'flex' : 'none' 
          }}
        >
          ☰
        </button>
        <h1 className="header-title">Enterprise Assistant</h1>
      </div>
      
      <div className="header-right">
        <select className="model-selector">
          <option value="claude-sonnet-4">Claude Sonnet 4</option>
          <option value="claude-opus-4">Claude Opus 4</option>
        </select>
        
        <div className="user-menu">
          <div className="user-avatar">
            <span>U</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;