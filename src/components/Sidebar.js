import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { MdDashboard, MdAdd, MdFolder, MdStyle, MdSettings, MdHome } from 'react-icons/md';
import { FaYoutube, FaFacebook, FaInstagram, FaXTwitter, FaTiktok, FaWordpress } from 'react-icons/fa6';
import { SiThreads } from 'react-icons/si';
import { youtubeAPI, facebookAPI, instagramAPI, twitterAPI, threadsAPI, tiktokAPI, wordpressAPI } from '../services/api';
import './Sidebar.css';

// 메뉴 아이템 렌더링 컴포넌트
const MenuItem = ({ item, isActive }) => (
  <Link to={item.path} className={`sidebar-item ${isActive ? 'active' : ''}`}>
    <item.icon className="sidebar-icon" />
    <span className="sidebar-label">{item.label}</span>
  </Link>
);

// 플랫폼 설정
const PLATFORMS = [
  { key: 'youtube', path: '/youtube', label: 'YouTube', icon: FaYoutube },
  { key: 'facebook', path: '/facebook', label: 'Facebook', icon: FaFacebook },
  { key: 'instagram', path: '/instagram', label: 'Instagram', icon: FaInstagram },
  { key: 'threads', path: '/threads', label: 'Threads', icon: SiThreads },
  { key: 'x', path: '/x', label: 'X', icon: FaXTwitter },
  { key: 'tiktok', path: '/tiktok', label: 'TikTok', icon: FaTiktok },
  { key: 'wordpress', path: '/wordpress', label: 'WordPress', icon: FaWordpress },
];

// 메뉴 설정
const MAIN_MENU = [
  { path: '/dashboard', label: '대시보드', icon: MdDashboard },
  { path: '/contents', label: '콘텐츠 관리', icon: MdFolder },
  { path: '/templates', label: '템플릿', icon: MdStyle },
];

const BOTTOM_MENU = [
  { path: '/home', label: '뚝딱 도우미', icon: MdHome },
  { path: '/settings', label: '설정', icon: MdSettings },
];

// 콘텐츠 생성 관련 경로
const CONTENT_PATHS = ['/content', '/create'];

function Sidebar({ onHoverChange }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [isSidebarHovered, setIsSidebarHovered] = useState(false);
  const [connectedPlatforms, setConnectedPlatforms] = useState({});

  const handleSidebarHover = (hovered) => {
    setIsSidebarHovered(hovered);
    onHoverChange?.(hovered);
  };

  // 플랫폼 연동 상태 조회
  useEffect(() => {
    const fetchPlatformStatus = async () => {
      try {
        const [youtube, facebook, instagram, threads, x, tiktok, wordpress] = await Promise.all([
          youtubeAPI.getStatus().catch(() => null),
          facebookAPI.getStatus().catch(() => null),
          instagramAPI.getStatus().catch(() => null),
          threadsAPI.getStatus().catch(() => null),
          twitterAPI.getStatus().catch(() => null),
          tiktokAPI.getStatus().catch(() => null),
          wordpressAPI.getStatus().catch(() => null),
        ]);

        setConnectedPlatforms({
          youtube: !!youtube,
          facebook: !!(facebook?.page_id),
          instagram: !!(instagram?.instagram_account_id),
          threads: !!threads,
          x: !!x,
          tiktok: !!tiktok,
          wordpress: !!wordpress,
        });
      } catch (error) {
        console.error('Failed to fetch platform status:', error);
      }
    };

    fetchPlatformStatus();
  }, []);

  const isActive = (path) => location.pathname === path;
  const isContentActive = CONTENT_PATHS.includes(location.pathname);
  const connectedPlatformItems = PLATFORMS.filter(p => connectedPlatforms[p.key]);

  return (
    <aside
      className="sidebar"
      onMouseEnter={() => handleSidebarHover(true)}
      onMouseLeave={() => handleSidebarHover(false)}
    >
      <div className="sidebar-logo" onClick={() => navigate('/home')}>
        <img
          src={isSidebarHovered ? "/ddukddak_white.png" : "/ddukddak_white_text.png"}
          alt="콘텐츠 크리에이터"
        />
      </div>

      <nav className="sidebar-nav">
        {/* 콘텐츠 생성 */}
        <Link to="/content" className={`sidebar-item ${isContentActive ? 'active' : ''}`}>
          <MdAdd className="sidebar-icon" />
          <span className="sidebar-label">콘텐츠 생성</span>
        </Link>

        {/* 메인 메뉴 */}
        {MAIN_MENU.map(item => (
          <MenuItem key={item.path} item={item} isActive={isActive(item.path)} />
        ))}

        {/* 연동된 플랫폼 메뉴 */}
        {connectedPlatformItems.length > 0 && (
          <>
            <div className="sidebar-divider" />
            {connectedPlatformItems.map(item => (
              <MenuItem key={item.path} item={item} isActive={isActive(item.path)} />
            ))}
          </>
        )}
      </nav>

      {/* 하단 메뉴 */}
      <div className="sidebar-bottom">
        <div className="sidebar-divider" />
        {BOTTOM_MENU.map(item => (
          <MenuItem key={item.path} item={item} isActive={isActive(item.path)} />
        ))}
      </div>
    </aside>
  );
}

export default Sidebar;
