import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { dashboardAPI, youtubeAPI, facebookAPI, instagramAPI, twitterAPI, threadsAPI, tiktokAPI, wordpressAPI } from '../../services/api';
import { FaYoutube, FaFacebookF, FaInstagram, FaThreads, FaTiktok, FaWordpress } from 'react-icons/fa6';
import { RiTwitterXFill } from 'react-icons/ri';
import { FiCheck } from 'react-icons/fi';
import './Dashboard.css';

// 플랫폼 설정 (상수)
const PLATFORM_CONFIG = {
  youtube: {
    key: 'youtube',
    name: 'YouTube',
    icon: FaYoutube,
    color: '#FF0000',
    bgGradient: 'linear-gradient(135deg, #FF0000 0%, #CC0000 100%)',
    path: '/youtube',
    getConnected: (data) => !!data,
    getFollowers: (data) => data?.subscriber_count || 0,
    getViews: (data) => data?.view_count || 0,
  },
  instagram: {
    key: 'instagram',
    name: 'Instagram',
    icon: FaInstagram,
    color: '#E4405F',
    bgGradient: 'linear-gradient(135deg, #E4405F 0%, #FFDC80 100%)',
    path: '/instagram',
    getConnected: (data) => !!data?.instagram_account_id,
    getFollowers: (data) => data?.followers_count || 0,
    getViews: (data) => data?.impressions || 0,
  },
  facebook: {
    key: 'facebook',
    name: 'Facebook',
    icon: FaFacebookF,
    color: '#1877F2',
    bgGradient: 'linear-gradient(135deg, #1877F2 0%, #0D5BC4 100%)',
    path: '/facebook',
    getConnected: (data) => !!data?.page_id,
    getFollowers: (data) => data?.page_followers_count || 0,
    getViews: (data) => data?.page_views || 0,
  },
  threads: {
    key: 'threads',
    name: 'Threads',
    icon: FaThreads,
    color: '#000000',
    bgGradient: 'linear-gradient(135deg, #000000 0%, #333333 100%)',
    path: '/threads',
    getConnected: (data) => !!data,
    getFollowers: (data) => data?.followers_count || 0,
    getViews: (data) => data?.views || 0,
  },
  x: {
    key: 'x',
    name: 'X',
    icon: RiTwitterXFill,
    color: '#000000',
    bgGradient: 'linear-gradient(135deg, #000000 0%, #333333 100%)',
    path: '/x',
    getConnected: (data) => !!data?.x_user_id,
    getFollowers: (data) => data?.followers_count || 0,
    getViews: (data) => data?.impression_count || 0,
  },
  tiktok: {
    key: 'tiktok',
    name: 'TikTok',
    icon: FaTiktok,
    color: '#000000',
    bgGradient: 'linear-gradient(135deg, #25F4EE 0%, #FE2C55 100%)',
    path: '/tiktok',
    getConnected: (data) => !!data,
    getFollowers: (data) => data?.follower_count || 0,
    getViews: (data) => data?.likes_count || 0,
  },
  wordpress: {
    key: 'wordpress',
    name: 'WordPress',
    icon: FaWordpress,
    color: '#21759B',
    bgGradient: 'linear-gradient(135deg, #21759B 0%, #1A5F7A 100%)',
    path: '/wordpress',
    getConnected: (data) => !!data,
    getFollowers: (data) => 0,
    getViews: (data) => data?.total_views || 0,
  },
};

const PLATFORM_ORDER = ['youtube', 'instagram', 'facebook', 'threads', 'x', 'tiktok', 'wordpress'];

// 숫자 포맷팅 유틸
const formatNumber = (num) => {
  if (!num) return '0';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toLocaleString();
};

// 시간대별 인사말
const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return '좋은 아침이에요';
  if (hour < 18) return '좋은 오후예요';
  return '좋은 저녁이에요';
};

// 통계 바 컴포넌트
const StatBar = ({ platform, value, total }) => {
  const config = PLATFORM_CONFIG[platform.id];
  const Icon = config.icon;
  const percentage = total > 0 ? (value / total) * 100 : 0;

  return (
    <div className="reach-bar-row">
      <div className="reach-bar-info">
        <span className="reach-bar-icon" style={{ color: config.color }}><Icon /></span>
        <span className="reach-bar-name">{config.name}</span>
        <span className="reach-bar-count">{formatNumber(value)}</span>
      </div>
      <div className="reach-bar-track">
        <div
          className="reach-bar-fill"
          style={{ width: `${percentage}%`, background: config.bgGradient }}
        />
      </div>
    </div>
  );
};

// 통계 카드 컴포넌트
const StatsCard = ({ title, subtitle, data, total, valueKey }) => {
  if (data.length === 0) return null;

  return (
    <div className="reach-dashboard">
      <div className="reach-dashboard-header">
        <div className="reach-title-section">
          <h3>{title}</h3>
          <span className="reach-total-value">{formatNumber(total)}</span>
        </div>
        <span className="reach-subtitle">{subtitle}</span>
      </div>
      <div className="reach-bars-container">
        {data.map((p) => (
          <StatBar key={p.id} platform={p} value={p[valueKey]} total={total} valueKey={valueKey} />
        ))}
      </div>
    </div>
  );
};

// 플랫폼 카드 컴포넌트
const PlatformCard = ({ platform, status }) => {
  const Icon = platform.icon;
  const { connected } = status;

  return (
    <Link to={platform.path} className={`sns-platform-card ${connected ? 'connected' : 'disconnected'}`}>
      <div className="platform-icon-wrapper">
        <div className="platform-icon" style={{ color: platform.color }}>
          <Icon />
        </div>
        {connected && (
          <div className="connected-badge"><FiCheck /></div>
        )}
      </div>
    </Link>
  );
};

function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [snsStatus, setSnsStatus] = useState(
    Object.fromEntries(PLATFORM_ORDER.map(key => [
      key === 'x' ? 'twitter' : key,
      { loading: true, connected: false, data: null, posts: [], videos: [], analytics: null }
    ]))
  );
  const quickActions = [
    { label: '콘텐츠 생성', path: '/create', desc: 'AI로 블로그/SNS 콘텐츠 생성' },
    { label: '생성 내역', path: '/history', desc: '이전에 생성한 콘텐츠 보기' },
    { label: '콘텐츠 관리', path: '/contents', desc: '임시저장/발행 콘텐츠 관리' },
    { label: '템플릿 갤러리', path: '/templates', desc: '다양한 콘텐츠 템플릿 보기' },
  ];

  // 1단계: 통합 API로 모든 플랫폼 상태를 한 번에 조회
  const fetchConnectionStatus = useCallback(async () => {
    try {
      // 통합 API로 한 번에 모든 상태 조회 (7번 호출 → 1번 호출)
      const allStatus = await dashboardAPI.getAllStatus();

      const { youtube, facebook, instagram, x: twitter, threads, tiktok, wordpress } = allStatus;

      setSnsStatus(prev => ({
        youtube: { ...prev.youtube, loading: false, connected: !!youtube, data: youtube },
        facebook: { ...prev.facebook, loading: false, connected: !!facebook?.page_id, data: facebook },
        instagram: { ...prev.instagram, loading: false, connected: !!instagram?.instagram_account_id, data: instagram },
        twitter: { ...prev.twitter, loading: false, connected: !!twitter?.x_user_id, data: twitter },
        threads: { ...prev.threads, loading: false, connected: !!threads, data: threads },
        tiktok: { ...prev.tiktok, loading: false, connected: !!tiktok, data: tiktok },
        wordpress: { ...prev.wordpress, loading: false, connected: !!wordpress, data: wordpress },
      }));

      // 2단계: 연동된 플랫폼의 추가 데이터를 백그라운드에서 조회
      const connectedPlatforms = {
        youtube: !!youtube,
        facebook: !!facebook?.page_id,
        instagram: !!instagram?.instagram_account_id,
        twitter: !!twitter?.x_user_id,
        threads: !!threads,
        tiktok: !!tiktok,
        wordpress: !!wordpress,
      };

    // 백그라운드에서 콘텐츠 개수 조회 (10개만 가져와서 개수 파악)
    if (connectedPlatforms.youtube) {
      Promise.all([
        youtubeAPI.getVideos(0, 10).catch(() => []),
        youtubeAPI.getAnalyticsSummary().catch(() => null),
      ]).then(([videos, analytics]) => {
        setSnsStatus(prev => ({ ...prev, youtube: { ...prev.youtube, videos, analytics } }));
      });
    }

    if (connectedPlatforms.facebook) {
      facebookAPI.getPosts(0, 10).catch(() => []).then(posts => {
        setSnsStatus(prev => ({ ...prev, facebook: { ...prev.facebook, posts } }));
      });
    }

    if (connectedPlatforms.instagram) {
      instagramAPI.getPosts(0, 10).catch(() => []).then(posts => {
        setSnsStatus(prev => ({ ...prev, instagram: { ...prev.instagram, posts } }));
      });
    }

    if (connectedPlatforms.twitter) {
      twitterAPI.getPosts(0, 10).catch(() => []).then(posts => {
        setSnsStatus(prev => ({ ...prev, twitter: { ...prev.twitter, posts } }));
      });
    }

    if (connectedPlatforms.threads) {
      threadsAPI.getPosts(0, 10).catch(() => []).then(posts => {
        setSnsStatus(prev => ({ ...prev, threads: { ...prev.threads, posts } }));
      });
    }

    if (connectedPlatforms.tiktok) {
      tiktokAPI.getVideos(0, 10).catch(() => []).then(videos => {
        setSnsStatus(prev => ({ ...prev, tiktok: { ...prev.tiktok, videos } }));
      });
    }

    if (connectedPlatforms.wordpress) {
      wordpressAPI.getPosts(0, 10).catch(() => []).then(posts => {
        setSnsStatus(prev => ({ ...prev, wordpress: { ...prev.wordpress, posts } }));
      });
    }
    } catch (error) {
      console.error('Failed to fetch platform status:', error);
    }
  }, []);

  useEffect(() => {
    fetchConnectionStatus();
  }, [fetchConnectionStatus]);

  // 통계 데이터 계산
  const getStatsData = (valueGetter, valueKey) => {
    return PLATFORM_ORDER
      .map(key => {
        const stateKey = key === 'x' ? 'twitter' : key;
        const status = snsStatus[stateKey];
        const config = PLATFORM_CONFIG[key];
        return {
          id: key,
          [valueKey]: valueGetter(config, status),
          connected: status.connected,
        };
      })
      .filter(p => p.connected);
  };

  const platformFollowers = getStatsData((config, status) => config.getFollowers(status.data), 'followers');
  const platformContents = getStatsData((config) => {
    const stateKey = config.key === 'x' ? 'twitter' : config.key;
    return (config.key === 'youtube' || config.key === 'tiktok')
      ? snsStatus[stateKey].videos?.length || 0
      : snsStatus[stateKey].posts?.length || 0;
  }, 'contents');
  const platformViews = getStatsData((config, status) => config.getViews(status.data), 'views');

  const totalFollowers = platformFollowers.reduce((sum, p) => sum + p.followers, 0);
  const totalContents = platformContents.reduce((sum, p) => sum + p.contents, 0);
  const totalViews = platformViews.reduce((sum, p) => sum + p.views, 0);

  // 플랫폼 목록 (카드용)
  const platforms = PLATFORM_ORDER.map(key => ({
    ...PLATFORM_CONFIG[key],
    status: snsStatus[key === 'x' ? 'twitter' : key],
  }));

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="header-left">
          <h2>대시보드</h2>
          <p className="header-subtitle">{getGreeting()}, {user?.username || 'User'}님! 오늘의 콘텐츠 현황을 확인하세요.</p>
        </div>
      </div>

      {/* 메인 콘텐츠 영역 */}
      <div className="dashboard-main">
        {/* 왼쪽 콘텐츠 */}
        <div className="dashboard-left">
          {/* 빠른 작업 */}
          <div className="quick-actions">
            <div className="action-buttons">
              {quickActions.map((action, index) => (
                <button key={index} className="action-btn" onClick={() => navigate(action.path)}>
                  <div className="action-text">
                    <span className="action-label">{action.label}</span>
                    <span className="action-desc">{action.desc}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* 플랫폼별 통계 그래프 */}
          <div className="dashboard-charts">
            <StatsCard
              title="총 팔로워"
              subtitle="연동된 플랫폼의 총 팔로워"
              data={platformFollowers}
              total={totalFollowers}
              valueKey="followers"
            />
            <StatsCard
              title="총 콘텐츠"
              subtitle="연동된 플랫폼의 총 콘텐츠"
              data={platformContents}
              total={totalContents}
              valueKey="contents"
            />
            <StatsCard
              title="총 조회수"
              subtitle="연동된 플랫폼의 총 조회/노출"
              data={platformViews}
              total={totalViews}
              valueKey="views"
            />
          </div>
        </div>

        {/* SNS 플랫폼 카드 (오른쪽 세로) */}
        <div className="sns-platform-grid">
          {platforms.map((platform) => (
            <PlatformCard key={platform.key} platform={platform} status={platform.status} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
