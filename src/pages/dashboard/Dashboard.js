import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { youtubeAPI, facebookAPI, instagramAPI, twitterAPI, threadsAPI } from '../../services/api';
import { FaYoutube, FaFacebookF, FaInstagram, FaThreads } from 'react-icons/fa6';
import { RiTwitterXFill } from 'react-icons/ri';
import { FiCheck, FiPlus, FiRefreshCw } from 'react-icons/fi';
import './Dashboard.css';

function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [snsStatus, setSnsStatus] = useState({
    youtube: { loading: true, connected: false, data: null, videos: [], analytics: null },
    facebook: { loading: true, connected: false, data: null, posts: [] },
    instagram: { loading: true, connected: false, data: null, posts: [] },
    twitter: { loading: true, connected: false, data: null, posts: [] },
    threads: { loading: true, connected: false, data: null, posts: [] },
  });
  const [refreshing, setRefreshing] = useState(false);

  const quickActions = [
    { label: '콘텐츠 생성', path: '/create', desc: 'AI로 블로그/SNS 콘텐츠 생성' },
    { label: '생성 내역', path: '/history', desc: '이전에 생성한 콘텐츠 보기' },
    { label: '콘텐츠 관리', path: '/contents', desc: '임시저장/발행 콘텐츠 관리' },
  ];

  // SNS 플랫폼 설정
  const getSNSPlatforms = () => [
    { key: 'youtube', name: 'YouTube', icon: FaYoutube, color: '#FF0000', path: '/youtube', status: snsStatus.youtube },
    { key: 'instagram', name: 'Instagram', icon: FaInstagram, color: '#E4405F', path: '/instagram', status: snsStatus.instagram },
    { key: 'facebook', name: 'Facebook', icon: FaFacebookF, color: '#1877F2', path: '/facebook', status: snsStatus.facebook },
    { key: 'threads', name: 'Threads', icon: FaThreads, color: '#000000', path: '/threads', status: snsStatus.threads },
    { key: 'x', name: 'X', icon: RiTwitterXFill, color: '#000000', path: '/x', status: snsStatus.twitter },
  ];

  // SNS 연동 상태 및 데이터 조회
  const fetchSNSData = useCallback(async () => {
    setRefreshing(true);

    // YouTube 데이터 조회
    try {
      const ytData = await youtubeAPI.getStatus();
      let videos = [];
      let analytics = null;

      if (ytData) {
        try {
          videos = await youtubeAPI.getVideos(0, 100) || [];
        } catch (e) {
          console.error('YouTube videos fetch error:', e);
        }
        try {
          analytics = await youtubeAPI.getAnalyticsSummary();
        } catch (e) {
          console.error('YouTube analytics fetch error:', e);
        }
      }

      setSnsStatus(prev => ({
        ...prev,
        youtube: { loading: false, connected: !!ytData, data: ytData, videos, analytics }
      }));
    } catch {
      setSnsStatus(prev => ({
        ...prev,
        youtube: { loading: false, connected: false, data: null, videos: [], analytics: null }
      }));
    }

    // Facebook 데이터 조회
    try {
      const fbData = await facebookAPI.getStatus();
      let posts = [];

      if (fbData?.page_id) {
        try {
          posts = await facebookAPI.getPosts(0, 100) || [];
        } catch (e) {
          console.error('Facebook posts fetch error:', e);
        }
      }

      setSnsStatus(prev => ({
        ...prev,
        facebook: { loading: false, connected: !!fbData?.page_id, data: fbData, posts }
      }));
    } catch {
      setSnsStatus(prev => ({
        ...prev,
        facebook: { loading: false, connected: false, data: null, posts: [] }
      }));
    }

    // Instagram 데이터 조회
    try {
      const igData = await instagramAPI.getStatus();
      let posts = [];

      if (igData?.instagram_account_id) {
        try {
          posts = await instagramAPI.getPosts(0, 100) || [];
        } catch (e) {
          console.error('Instagram posts fetch error:', e);
        }
      }

      setSnsStatus(prev => ({
        ...prev,
        instagram: { loading: false, connected: !!igData?.instagram_account_id, data: igData, posts }
      }));
    } catch {
      setSnsStatus(prev => ({
        ...prev,
        instagram: { loading: false, connected: false, data: null, posts: [] }
      }));
    }

    // X(Twitter) 데이터 조회
    try {
      const xData = await twitterAPI.getStatus();
      let posts = [];

      if (xData?.x_user_id) {
        try {
          posts = await twitterAPI.getPosts(0, 100) || [];
        } catch (e) {
          console.error('X posts fetch error:', e);
        }
      }

      setSnsStatus(prev => ({
        ...prev,
        twitter: { loading: false, connected: !!xData?.x_user_id, data: xData, posts }
      }));
    } catch {
      setSnsStatus(prev => ({
        ...prev,
        twitter: { loading: false, connected: false, data: null, posts: [] }
      }));
    }

    // Threads 데이터 조회
    try {
      const thData = await threadsAPI.getStatus();
      let posts = [];

      if (thData) {
        try {
          posts = await threadsAPI.getPosts(0, 100) || [];
        } catch (e) {
          console.error('Threads posts fetch error:', e);
        }
      }

      setSnsStatus(prev => ({
        ...prev,
        threads: { loading: false, connected: !!thData, data: thData, posts }
      }));
    } catch {
      setSnsStatus(prev => ({
        ...prev,
        threads: { loading: false, connected: false, data: null, posts: [] }
      }));
    }

    setRefreshing(false);
  }, []);

  useEffect(() => {
    fetchSNSData();
  }, [fetchSNSData]);

  // 숫자 포맷팅
  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
  };

  // 플랫폼별 팔로워 계산 (연동된 플랫폼만)
  const calculatePlatformFollowers = () => {
    const { youtube, facebook, instagram, twitter, threads } = snsStatus;
    const platforms = [
      { id: 'youtube', name: 'YouTube', icon: <FaYoutube />, brandColor: '#FF0000', bgGradient: 'linear-gradient(135deg, #FF0000 0%, #CC0000 100%)', followers: youtube.data?.subscriber_count || 0, connected: youtube.connected },
      { id: 'instagram', name: 'Instagram', icon: <FaInstagram />, brandColor: '#E4405F', bgGradient: 'linear-gradient(135deg, #E4405F 0%, #FFDC80 100%)', followers: instagram.data?.followers_count || 0, connected: instagram.connected },
      { id: 'facebook', name: 'Facebook', icon: <FaFacebookF />, brandColor: '#1877F2', bgGradient: 'linear-gradient(135deg, #1877F2 0%, #0D5BC4 100%)', followers: facebook.data?.page_followers_count || 0, connected: facebook.connected },
      { id: 'threads', name: 'Threads', icon: <FaThreads />, brandColor: '#000000', bgGradient: 'linear-gradient(135deg, #000000 0%, #333333 100%)', followers: threads.data?.followers_count || 0, connected: threads.connected },
      { id: 'x', name: 'X', icon: <RiTwitterXFill />, brandColor: '#000000', bgGradient: 'linear-gradient(135deg, #000000 0%, #333333 100%)', followers: twitter.data?.followers_count || 0, connected: twitter.connected },
    ];
    return platforms.filter(p => p.connected);
  };

  // 플랫폼별 콘텐츠 수 계산 (연동된 플랫폼만)
  const calculatePlatformContents = () => {
    const { youtube, facebook, instagram, twitter, threads } = snsStatus;
    const platforms = [
      { id: 'youtube', name: 'YouTube', icon: <FaYoutube />, brandColor: '#FF0000', bgGradient: 'linear-gradient(135deg, #FF0000 0%, #CC0000 100%)', contents: youtube.videos?.length || 0, connected: youtube.connected },
      { id: 'instagram', name: 'Instagram', icon: <FaInstagram />, brandColor: '#E4405F', bgGradient: 'linear-gradient(135deg, #E4405F 0%, #FFDC80 100%)', contents: instagram.posts?.length || 0, connected: instagram.connected },
      { id: 'facebook', name: 'Facebook', icon: <FaFacebookF />, brandColor: '#1877F2', bgGradient: 'linear-gradient(135deg, #1877F2 0%, #0D5BC4 100%)', contents: facebook.posts?.length || 0, connected: facebook.connected },
      { id: 'threads', name: 'Threads', icon: <FaThreads />, brandColor: '#000000', bgGradient: 'linear-gradient(135deg, #000000 0%, #333333 100%)', contents: threads.posts?.length || 0, connected: threads.connected },
      { id: 'x', name: 'X', icon: <RiTwitterXFill />, brandColor: '#000000', bgGradient: 'linear-gradient(135deg, #000000 0%, #333333 100%)', contents: twitter.posts?.length || 0, connected: twitter.connected },
    ];
    return platforms.filter(p => p.connected);
  };

  // 플랫폼별 조회수 계산 (연동된 플랫폼만)
  const calculatePlatformViews = () => {
    const { youtube, facebook, instagram, twitter, threads } = snsStatus;
    const platforms = [
      { id: 'youtube', name: 'YouTube', icon: <FaYoutube />, brandColor: '#FF0000', bgGradient: 'linear-gradient(135deg, #FF0000 0%, #CC0000 100%)', views: youtube.data?.view_count || 0, connected: youtube.connected },
      { id: 'instagram', name: 'Instagram', icon: <FaInstagram />, brandColor: '#E4405F', bgGradient: 'linear-gradient(135deg, #E4405F 0%, #FFDC80 100%)', views: instagram.data?.impressions || 0, connected: instagram.connected },
      { id: 'facebook', name: 'Facebook', icon: <FaFacebookF />, brandColor: '#1877F2', bgGradient: 'linear-gradient(135deg, #1877F2 0%, #0D5BC4 100%)', views: facebook.data?.page_views || 0, connected: facebook.connected },
      { id: 'threads', name: 'Threads', icon: <FaThreads />, brandColor: '#000000', bgGradient: 'linear-gradient(135deg, #000000 0%, #333333 100%)', views: threads.data?.views || 0, connected: threads.connected },
      { id: 'x', name: 'X', icon: <RiTwitterXFill />, brandColor: '#000000', bgGradient: 'linear-gradient(135deg, #000000 0%, #333333 100%)', views: twitter.data?.impression_count || 0, connected: twitter.connected },
    ];
    return platforms.filter(p => p.connected);
  };

  const platformFollowers = calculatePlatformFollowers();
  const platformContents = calculatePlatformContents();
  const platformViews = calculatePlatformViews();

  // 총합 계산
  const platformTotalFollowers = platformFollowers.reduce((sum, p) => sum + p.followers, 0);
  const platformTotalContents = platformContents.reduce((sum, p) => sum + p.contents, 0);
  const platformTotalViews = platformViews.reduce((sum, p) => sum + p.views, 0);

  // 시간대별 인사말
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return '좋은 아침이에요';
    if (hour < 18) return '좋은 오후예요';
    return '좋은 저녁이에요';
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="header-left">
          <h2>대시보드</h2>
          <p className="header-subtitle">{getGreeting()}, {user?.username || 'User'}님! 오늘의 콘텐츠 현황을 확인하세요.</p>
        </div>
      </div>

      {/* 플랫폼별 통계 그래프 */}
      <div className="dashboard-charts">
        {/* 팔로워 그래프 */}
        {platformFollowers.length > 0 && (
          <div className="reach-dashboard">
            <div className="reach-dashboard-header">
              <div className="reach-title-section">
                <h3>총 팔로워</h3>
                <span className="reach-total-value">{formatNumber(platformTotalFollowers)}</span>
              </div>
              <span className="reach-subtitle">연동된 플랫폼의 총 팔로워</span>
            </div>
            <div className="reach-bars-container">
              {platformFollowers.map((p) => {
                const percentage = platformTotalFollowers > 0 ? (p.followers / platformTotalFollowers) * 100 : 0;
                return (
                  <div key={p.id} className="reach-bar-row">
                    <div className="reach-bar-info">
                      <span className="reach-bar-icon" style={{ color: p.brandColor }}>{p.icon}</span>
                      <span className="reach-bar-name">{p.name}</span>
                      <span className="reach-bar-count">{formatNumber(p.followers)}</span>
                    </div>
                    <div className="reach-bar-track">
                      <div
                        className="reach-bar-fill"
                        style={{
                          width: `${percentage}%`,
                          background: p.bgGradient
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 콘텐츠 그래프 */}
        {platformContents.length > 0 && (
          <div className="reach-dashboard">
            <div className="reach-dashboard-header">
              <div className="reach-title-section">
                <h3>총 콘텐츠</h3>
                <span className="reach-total-value">{formatNumber(platformTotalContents)}</span>
              </div>
              <span className="reach-subtitle">연동된 플랫폼의 총 콘텐츠</span>
            </div>
            <div className="reach-bars-container">
              {platformContents.map((p) => {
                const percentage = platformTotalContents > 0 ? (p.contents / platformTotalContents) * 100 : 0;
                return (
                  <div key={p.id} className="reach-bar-row">
                    <div className="reach-bar-info">
                      <span className="reach-bar-icon" style={{ color: p.brandColor }}>{p.icon}</span>
                      <span className="reach-bar-name">{p.name}</span>
                      <span className="reach-bar-count">{formatNumber(p.contents)}</span>
                    </div>
                    <div className="reach-bar-track">
                      <div
                        className="reach-bar-fill"
                        style={{
                          width: `${percentage}%`,
                          background: p.bgGradient
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 조회수 그래프 */}
        {platformViews.length > 0 && (
          <div className="reach-dashboard">
            <div className="reach-dashboard-header">
              <div className="reach-title-section">
                <h3>총 조회수</h3>
                <span className="reach-total-value">{formatNumber(platformTotalViews)}</span>
              </div>
              <span className="reach-subtitle">연동된 플랫폼의 총 조회/노출</span>
            </div>
            <div className="reach-bars-container">
              {platformViews.map((p) => {
                const percentage = platformTotalViews > 0 ? (p.views / platformTotalViews) * 100 : 0;
                return (
                  <div key={p.id} className="reach-bar-row">
                    <div className="reach-bar-info">
                      <span className="reach-bar-icon" style={{ color: p.brandColor }}>{p.icon}</span>
                      <span className="reach-bar-name">{p.name}</span>
                      <span className="reach-bar-count">{formatNumber(p.views)}</span>
                    </div>
                    <div className="reach-bar-track">
                      <div
                        className="reach-bar-fill"
                        style={{
                          width: `${percentage}%`,
                          background: p.bgGradient
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div className="dashboard-content">
        {/* SNS 연동 상태 섹션 */}
        <div className="sns-connection-section">
          <div className="section-title">
            <div className="section-title-left">
              <h3>SNS 연동 상태</h3>
              <p className="section-description">각 플랫폼을 클릭하여 상세 정보를 확인하거나 연동하세요</p>
            </div>
            <button
              className={`sns-refresh-btn ${refreshing ? 'spinning' : ''}`}
              onClick={fetchSNSData}
              disabled={refreshing}
            >
              <FiRefreshCw />
            </button>
          </div>
          <div className="sns-platform-grid">
            {getSNSPlatforms().map((platform) => {
              const Icon = platform.icon;
              const isConnected = platform.status.connected;
              const isLoading = platform.status.loading;

              return (
                <div
                  key={platform.key}
                  className={`sns-platform-card ${isConnected ? 'connected' : 'disconnected'}`}
                >
                  <div className="platform-card-header">
                    <div className="platform-icon-wrapper">
                      <div className="platform-icon" style={{ color: platform.color }}>
                        <Icon />
                      </div>
                      {isConnected && (
                        <div className="connected-badge">
                          <FiCheck />
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="platform-card-body">
                    <h4 className="platform-name">{platform.name}</h4>
                    {isLoading ? (
                      <span className="platform-status loading">확인 중...</span>
                    ) : isConnected ? (
                      <span className="platform-status connected">연동됨</span>
                    ) : (
                      <span className="platform-status disconnected">미연동</span>
                    )}
                  </div>
                  <div className="platform-card-footer">
                    {isConnected ? (
                      <Link to={platform.path} className="platform-btn secondary">
                        관리
                      </Link>
                    ) : (
                      <Link to={platform.path} className="platform-btn connect">
                        <FiPlus /> 연동하기
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="quick-actions">
          <h3>빠른 작업</h3>
          <div className="action-buttons">
            {quickActions.map((action, index) => (
              <button
                key={index}
                className="action-btn"
                onClick={() => navigate(action.path)}
              >
                <div className="action-text">
                  <span className="action-label">{action.label}</span>
                  <span className="action-desc">{action.desc}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
