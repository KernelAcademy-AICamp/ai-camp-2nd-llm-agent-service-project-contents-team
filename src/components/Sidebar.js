import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  MdDashboard,
  MdAdd,
  MdVideoLibrary,
  MdFolder,
  MdStyle,
  MdSettings,
  MdHome,
  MdEdit
} from 'react-icons/md';
import {
  FaYoutube,
  FaFacebook,
  FaInstagram,
  FaXTwitter
} from 'react-icons/fa6';
import { SiThreads } from 'react-icons/si';
import { youtubeAPI, facebookAPI, instagramAPI, twitterAPI, threadsAPI } from '../services/api';
import './Sidebar.css';

function Sidebar({ onHoverChange }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [isContentMenuOpen, setIsContentMenuOpen] = useState(false);
  const [isSidebarHovered, setIsSidebarHovered] = useState(false);

  // 부모 컴포넌트에 호버 상태 전달
  const handleSidebarHover = (hovered) => {
    setIsSidebarHovered(hovered);
    if (onHoverChange) {
      onHoverChange(hovered);
    }
  };
  const [connectedPlatforms, setConnectedPlatforms] = useState({
    youtube: false,
    facebook: false,
    instagram: false,
    threads: false,
    x: false
  });

  // 플랫폼 연동 상태 조회
  useEffect(() => {
    const fetchPlatformStatus = async () => {
      try {
        const [youtube, facebook, instagram, threads, x] = await Promise.all([
          youtubeAPI.getStatus().catch(() => null),
          facebookAPI.getStatus().catch(() => null),
          instagramAPI.getStatus().catch(() => null),
          threadsAPI.getStatus().catch(() => null),
          twitterAPI.getStatus().catch(() => null)
        ]);

        // API가 연결 객체를 반환하면 연동됨, null이면 미연동
        setConnectedPlatforms({
          youtube: !!youtube,
          facebook: !!(facebook && facebook.page_id),  // 페이지 선택까지 완료해야 연동
          instagram: !!(instagram && instagram.instagram_account_id),  // 계정 선택까지 완료해야 연동
          threads: !!threads,
          x: !!x
        });
      } catch (error) {
        console.error('Failed to fetch platform status:', error);
      }
    };

    fetchPlatformStatus();
  }, []);

  const menuItems = [
    { path: '/dashboard', label: '대시보드', icon: MdDashboard },
  ];

  const contentMenuItems = [
    { path: '/create', label: '글 + 이미지 생성', icon: MdEdit },
    { path: '/ai-video', label: 'AI 동영상 생성', icon: MdVideoLibrary },
  ];

  const contentManagementItems = [
    { path: '/contents', label: '콘텐츠 관리', icon: MdFolder },
    { path: '/templates', label: '템플릿', icon: MdStyle },
  ];

  const allPlatformMenuItems = [
    { path: '/youtube', label: 'YouTube', icon: FaYoutube, key: 'youtube' },
    { path: '/facebook', label: 'Facebook', icon: FaFacebook, key: 'facebook' },
    { path: '/instagram', label: 'Instagram', icon: FaInstagram, key: 'instagram' },
    { path: '/threads', label: 'Threads', icon: SiThreads, key: 'threads' },
    { path: '/x', label: 'X', icon: FaXTwitter, key: 'x' },
  ];

  // 연동된 플랫폼만 필터링
  const platformMenuItems = allPlatformMenuItems.filter(
    item => connectedPlatforms[item.key]
  );

  const managementMenuItems = [
    { path: '/home', label: '뚝딱 도우미', icon: MdHome },
    { path: '/settings', label: '설정', icon: MdSettings },
  ];

  const isContentMenuActive = location.pathname === '/content' || contentMenuItems.some(item =>
    location.pathname === item.path
  );

  // 콘텐츠 생성 관련 페이지에 있을 때 드롭다운 자동으로 열기
  useEffect(() => {
    if (isContentMenuActive) {
      setIsContentMenuOpen(true);
    }
  }, [isContentMenuActive]);

  const handleContentMenuEnter = () => {
    setIsContentMenuOpen(true);
  };

  const handleContentMenuLeave = () => {
    if (!isContentMenuActive) {
      setIsContentMenuOpen(false);
    }
  };

  const handleContentItemClick = (path) => {
    navigate(path);
  };

  const handleLogoClick = () => {
    navigate('/home');
  };

  return (
    <aside
      className="sidebar"
      onMouseEnter={() => handleSidebarHover(true)}
      onMouseLeave={() => handleSidebarHover(false)}
    >
      {/* 로고 */}
      <div className="sidebar-logo" onClick={handleLogoClick}>
        <img
          src={isSidebarHovered ? "/ddukddak_white.png" : "/ddukddak_white_text.png"}
          alt="콘텐츠 크리에이터"
        />
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`sidebar-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <item.icon className="sidebar-icon" />
            <span className="sidebar-label">{item.label}</span>
          </Link>
        ))}

        {/* 콘텐츠 생성 드롭다운 */}
        <div
          className="sidebar-dropdown"
          onMouseEnter={handleContentMenuEnter}
          onMouseLeave={handleContentMenuLeave}
        >
          <button
            className={`sidebar-item sidebar-dropdown-trigger ${isContentMenuActive ? 'active' : ''}`}
            onClick={() => navigate('/content')}
          >
            <MdAdd className="sidebar-icon" />
            <span className="sidebar-label">콘텐츠 생성</span>
          </button>

          <div className={`sidebar-dropdown-menu ${isContentMenuOpen ? 'open' : ''}`}>
            {contentMenuItems.map((item) => (
              <button
                key={item.path}
                onClick={() => handleContentItemClick(item.path)}
                className={`sidebar-dropdown-item ${location.pathname === item.path ? 'active' : ''}`}
              >
                <item.icon className="sidebar-icon" />
                <span className="sidebar-label">{item.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 콘텐츠 관리 메뉴 */}
        {contentManagementItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`sidebar-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <item.icon className="sidebar-icon" />
            <span className="sidebar-label">{item.label}</span>
          </Link>
        ))}

        {/* 플랫폼 연동 메뉴 (연동된 플랫폼만 표시) */}
        {platformMenuItems.length > 0 && (
          <>
            <div className="sidebar-divider"></div>
            {platformMenuItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`sidebar-item ${location.pathname === item.path ? 'active' : ''}`}
              >
                <item.icon className="sidebar-icon" />
                <span className="sidebar-label">{item.label}</span>
              </Link>
            ))}
          </>
        )}
      </nav>

      {/* 하단 메뉴 */}
      <div className="sidebar-bottom">
        <div className="sidebar-divider"></div>
        {managementMenuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`sidebar-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <item.icon className="sidebar-icon" />
            <span className="sidebar-label">{item.label}</span>
          </Link>
        ))}
      </div>
    </aside>
  );
}

export default Sidebar;
