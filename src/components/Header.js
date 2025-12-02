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


  const handleHomeClick = () => {
    navigate('/home');
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-logo" onClick={handleHomeClick} style={{ cursor: 'pointer' }}>
          <img src="/ddukddak_colored.png" alt="콘텐츠 크리에이터" />
        </div>
        <div className="header-actions">
          <div className="user-profile-wrapper" ref={dropdownRef}>
            <button
              className="user-profile"
              onClick={() => setShowDropdown(!showDropdown)}
            >
              <span className="user-name">{user?.username || 'User'}</span>
            </button>
            {showDropdown && (
              <div className="user-dropdown">
                <button
                  onClick={() => handleMenuClick('/mypage')}
                  className="user-info-button"
                >
                  <div className="user-info-text">
                    <p className="user-info-name">{user?.username || 'User'}</p>
                    <p className="user-info-link">마이페이지 보기</p>
                  </div>
                </button>
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
