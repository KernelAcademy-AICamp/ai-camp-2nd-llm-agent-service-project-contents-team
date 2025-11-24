import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

function Sidebar() {
  const location = useLocation();

  const menuItems = [
    { path: '/home', icon: '🏠', label: '홈' },
    { path: '/', icon: '📊', label: '대시보드' },
    { path: '/create', icon: '✨', label: '콘텐츠 생성' },
    { path: '/cardnews', icon: '📰', label: '카드뉴스' },
    { path: '/video', icon: '🎬', label: 'AI 동영상' },
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
