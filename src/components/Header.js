import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './Header.css';

function Header() {
  const { user, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // 드롭다운 외부 클릭 시 닫기
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDropdown]);

  const handleLogout = async () => {
    await logout();
    setShowDropdown(false);
  };

  return (
    <header className="header">
      <div className="header-content">
        <h1 className="header-title">콘텐츠 크리에이터</h1>
        <div className="header-actions">
          <button className="btn-notification">
            <span className="notification-icon">🔔</span>
          </button>
          <div className="user-profile-wrapper" ref={dropdownRef}>
            <button
              className="user-profile"
              onClick={() => setShowDropdown(!showDropdown)}
            >
              <span className="user-avatar">👤</span>
              <span className="user-name">{user?.username || 'User'}</span>
            </button>
            {showDropdown && (
              <div className="user-dropdown">
                <div className="user-info">
                  <p className="user-email">{user?.email}</p>
                  {user?.full_name && (
                    <p className="user-fullname">{user.full_name}</p>
                  )}
                </div>
                <div className="dropdown-divider"></div>
                <button onClick={handleLogout} className="dropdown-item logout-btn">
                  로그아웃
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
