import React from 'react';
import './Header.css';

function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <h1 className="header-title">콘텐츠 크리에이터</h1>
        <div className="header-actions">
          <button className="btn-notification">
            <span className="notification-icon">🔔</span>
          </button>
          <div className="user-profile">
            <span className="user-avatar">👤</span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
