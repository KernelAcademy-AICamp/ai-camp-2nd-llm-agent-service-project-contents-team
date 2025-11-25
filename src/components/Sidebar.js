import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import './Sidebar.css';

function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [isContentMenuOpen, setIsContentMenuOpen] = useState(false);

  const menuItems = [
    { path: '/home', icon: '🏠', label: '홈' },
    { path: '/', icon: '📊', label: '대시보드' },
  ];

  const contentMenuItems = [
    { path: '/ai-content', icon: '🤖', label: 'AI 글 생성' },
    { path: '/video-script', icon: '🎥', label: '비디오 스크립트' },
    { path: '/image', icon: '🎨', label: 'AI 이미지 생성' },
    { path: '/cardnews', icon: '📰', label: '카드뉴스 생성' },
    { path: '/video', icon: '🎬', label: 'AI 동영상 생성' },
  ];

  const isContentMenuActive = contentMenuItems.some(item =>
    location.pathname === item.path
  );

  // 콘텐츠 생성 관련 페이지에 있을 때 드롭다운 자동으로 열기
  useEffect(() => {
    if (isContentMenuActive) {
      setIsContentMenuOpen(true);
    }
  }, [isContentMenuActive]);

  const toggleContentMenu = () => {
    setIsContentMenuOpen(!isContentMenuOpen);
  };

  const handleContentItemClick = (path) => {
    navigate(path);
    // 드롭다운을 열린 상태로 유지 (setIsContentMenuOpen(false) 제거)
  };

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

        {/* 콘텐츠 생성 드롭다운 */}
        <div className="sidebar-dropdown">
          <button
            className={`sidebar-item sidebar-dropdown-trigger ${isContentMenuActive ? 'active' : ''}`}
            onClick={toggleContentMenu}
          >
            <span className="sidebar-icon">✨</span>
            <span className="sidebar-label">콘텐츠 생성</span>
            <span className={`sidebar-dropdown-arrow ${isContentMenuOpen ? 'open' : ''}`}>▼</span>
          </button>

          {isContentMenuOpen && (
            <div className="sidebar-dropdown-menu">
              {contentMenuItems.map((item) => (
                <button
                  key={item.path}
                  onClick={() => handleContentItemClick(item.path)}
                  className={`sidebar-dropdown-item ${location.pathname === item.path ? 'active' : ''}`}
                >
                  <span className="sidebar-icon">{item.icon}</span>
                  <span className="sidebar-label">{item.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </nav>
    </aside>
  );
}

export default Sidebar;
