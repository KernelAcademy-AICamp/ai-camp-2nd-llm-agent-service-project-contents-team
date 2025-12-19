import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { MdDashboard, MdAdd, MdFolder, MdStyle, MdSettings, MdHome } from 'react-icons/md';
import { FiCreditCard } from 'react-icons/fi';
import { creditsAPI } from '../services/api';
import './Sidebar.css';

// 메뉴 아이템 렌더링 컴포넌트
const MenuItem = ({ item, isActive }) => (
  <Link to={item.path} className={`sidebar-item ${isActive ? 'active' : ''}`}>
    <item.icon className="sidebar-icon" />
    <span className="sidebar-label">{item.label}</span>
  </Link>
);

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
  const [creditBalance, setCreditBalance] = useState(0);

  const handleSidebarHover = (hovered) => {
    setIsSidebarHovered(hovered);
    onHoverChange?.(hovered);
  };

  // 크레딧 조회
  useEffect(() => {
    const fetchCreditBalance = async () => {
      try {
        const data = await creditsAPI.getBalance();
        setCreditBalance(data.balance);
      } catch (error) {
        console.error('Failed to fetch credit balance:', error);
      }
    };

    fetchCreditBalance();
  }, []);

  const isActive = (path) => location.pathname === path;
  const isContentActive = CONTENT_PATHS.includes(location.pathname);

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
      </nav>

      {/* 하단 메뉴 */}
      <div className="sidebar-bottom">
        {/* 크레딧 표시 */}
        <Link to="/credits" className={`sidebar-credit ${isActive('/credits') ? 'active' : ''}`}>
          <FiCreditCard className="sidebar-icon" />
          <span className="sidebar-label">{creditBalance.toLocaleString()} 크레딧</span>
        </Link>

        <div className="sidebar-divider" />
        {BOTTOM_MENU.map(item => (
          <MenuItem key={item.path} item={item} isActive={isActive(item.path)} />
        ))}
      </div>
    </aside>
  );
}

export default Sidebar;
