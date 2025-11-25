import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Header.css';

function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
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

  const handleMenuClick = (path) => {
    navigate(path);
    setShowDropdown(false);
  };

  const menuItems = [
    { path: '/contents', icon: '📝', label: '콘텐츠 관리' },
    { path: '/templates', icon: '📋', label: '템플릿' },
    { path: '/analytics', icon: '📈', label: '분석' },
    { path: '/mypage', icon: '👤', label: '마이페이지' },
    { path: '/settings', icon: '⚙️', label: '설정' },
  ];

  const handleHomeClick = () => {
    navigate('/home');
  };

  return (
    <header className="header">
      <div className="header-content">
        <h1 className="header-title" onClick={handleHomeClick} style={{ cursor: 'pointer' }}>
          콘텐츠 크리에이터
        </h1>
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
                <button
                  onClick={() => handleMenuClick('/mypage')}
                  className="user-info-button"
                >
                  <span className="user-info-avatar">👤</span>
                  <div className="user-info-text">
                    <p className="user-info-name">{user?.username || 'User'}</p>
                    <p className="user-info-link">마이페이지 보기</p>
                  </div>
                </button>
                <div className="dropdown-divider"></div>
                {menuItems.filter(item => item.path !== '/mypage').map((item) => (
                  <button
                    key={item.path}
                    onClick={() => handleMenuClick(item.path)}
                    className="dropdown-item menu-item"
                  >
                    <span className="dropdown-icon">{item.icon}</span>
                    <span>{item.label}</span>
                  </button>
                ))}
                <div className="dropdown-divider"></div>
                <button onClick={handleLogout} className="dropdown-item logout-btn">
                  <span className="dropdown-icon">🚪</span>
                  <span>로그아웃</span>
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
