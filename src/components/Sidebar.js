import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

function Sidebar() {
  const location = useLocation();

  const menuItems = [
    { path: '/', icon: '📊', label: '대시보드' },
    { path: '/create', icon: '✨', label: '콘텐츠 생성' },
    { path: '/contents', icon: '📝', label: '콘텐츠 관리' },
    { path: '/templates', icon: '📋', label: '템플릿' },
    { path: '/schedule', icon: '📅', label: '스케줄' },
    { path: '/publish-history', icon: '📷', label: '발행 이력' },
    { path: '/analytics', icon: '📈', label: '분석' },
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
