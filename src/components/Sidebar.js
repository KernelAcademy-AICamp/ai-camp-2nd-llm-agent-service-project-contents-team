import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

function Sidebar() {
  const location = useLocation();

  const menuItems = [
    { path: '/', icon: '📊', label: '대시보드' },
    { path: '/create', icon: '✨', label: '콘텐츠 생성' },
    { path: '/cardnews', icon: '📰', label: '카드뉴스' },
    { path: '/video', icon: '🎬', label: 'AI 동영상' },
    { path: '/contents', icon: '📝', label: '콘텐츠 관리' },
    { path: '/templates', icon: '📋', label: '템플릿' },
    { path: '/analytics', icon: '📈', label: '분석' },
    { path: '/mypage', icon: '👤', label: '마이페이지' },
    { path: '/settings', icon: '⚙️', label: '설정' },
  ];

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`sidebar-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <span className="sidebar-icon">{item.icon}</span>
            <span className="sidebar-label">{item.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;
