import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { youtubeAPI, facebookAPI, instagramAPI, twitterAPI } from '../../services/api';
import './Dashboard.css';

function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [snsStatus, setSnsStatus] = useState({
    youtube: { loading: true, connected: false, data: null, videos: [], analytics: null },
    facebook: { loading: true, connected: false, data: null, posts: [] },
    instagram: { loading: true, connected: false, data: null, posts: [] },
    twitter: { loading: true, connected: false, data: null, tweets: [] },
  });
  const [statsLoading, setStatsLoading] = useState(true);

  const recentContents = [
    { id: 1, title: '신제품 런칭 홍보 콘텐츠', type: '소셜 미디어', status: '발행됨', date: '2025-11-10' },
    { id: 2, title: '할인 이벤트 안내', type: '블로그', status: '예약됨', date: '2025-11-15' },
    { id: 3, title: '고객 리뷰 소개 영상', type: '비디오', status: '작성 중', date: '2025-11-12' },
  ];

  const quickActions = [
    { label: '콘텐츠 생성', path: '/create', desc: 'AI로 블로그/SNS 콘텐츠 생성' },
    { label: '생성 내역', path: '/history', desc: '이전에 생성한 콘텐츠 보기' },
    { label: '편집 & 발행', path: '/editor', desc: '콘텐츠 수정 및 SNS 발행' },
    { label: 'SNS 연동', path: '/settings', desc: 'Facebook, YouTube 등 연결' },
  ];

  // SNS 연동 상태 및 데이터 조회
  useEffect(() => {
    const fetchSNSData = async () => {
      setStatsLoading(true);

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

      // Twitter 데이터 조회
      try {
        const twData = await twitterAPI.getStatus();
        let tweets = [];

        if (twData?.twitter_user_id) {
          try {
            tweets = await twitterAPI.getTweets(0, 100) || [];
          } catch (e) {
            console.error('Twitter tweets fetch error:', e);
          }
        }

        setSnsStatus(prev => ({
          ...prev,
          twitter: { loading: false, connected: !!twData?.twitter_user_id, data: twData, tweets }
        }));
      } catch {
        setSnsStatus(prev => ({
          ...prev,
          twitter: { loading: false, connected: false, data: null, tweets: [] }
        }));
      }

      setStatsLoading(false);
    };

    fetchSNSData();
  }, []);

  // 숫자 포맷팅
  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
  };

  // 통계 계산
  const calculateStats = () => {
    const { youtube, facebook, instagram, twitter } = snsStatus;

    // 총 콘텐츠 수 (YouTube 동영상 + Facebook 게시물 + Instagram 게시물 + X 트윗)
    const totalContents =
      (youtube.videos?.length || 0) +
      (facebook.posts?.length || 0) +
      (instagram.posts?.length || 0) +
      (twitter.tweets?.length || 0);

    // 이번 주 생성 콘텐츠 (최근 7일 내 생성된 콘텐츠)
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

    const thisWeekContents = [
      ...(youtube.videos || []).filter(v => new Date(v.published_at) >= oneWeekAgo),
      ...(facebook.posts || []).filter(p => new Date(p.created_time) >= oneWeekAgo),
      ...(instagram.posts || []).filter(p => new Date(p.timestamp) >= oneWeekAgo),
      ...(twitter.tweets || []).filter(t => new Date(t.created_at) >= oneWeekAgo),
    ].length;

    // 총 팔로워/구독자 수
    const totalFollowers =
      (youtube.data?.subscriber_count || 0) +
      (facebook.data?.page_followers_count || 0) +
      (instagram.data?.followers_count || 0) +
      (twitter.data?.followers_count || 0);

    // 총 조회수/노출수
    const totalViews = youtube.data?.view_count || 0;

    // 연동된 SNS 수
    const connectedCount = [youtube, facebook, instagram, twitter].filter(s => s.connected).length;

    return {
      totalContents,
      thisWeekContents,
      totalFollowers,
      totalViews,
      connectedCount,
    };
  };

  const calculatedStats = calculateStats();

  const stats = [
    {
      label: '총 콘텐츠',
      value: statsLoading ? '-' : formatNumber(calculatedStats.totalContents),
      subLabel: 'YouTube + Facebook + Instagram + X'
    },
    {
      label: '이번 주 생성',
      value: statsLoading ? '-' : formatNumber(calculatedStats.thisWeekContents),
      subLabel: '최근 7일'
    },
    {
      label: '총 팔로워',
      value: statsLoading ? '-' : formatNumber(calculatedStats.totalFollowers),
      subLabel: '전체 채널 합계'
    },
    {
      label: '총 조회수',
      value: statsLoading ? '-' : formatNumber(calculatedStats.totalViews),
      subLabel: 'YouTube 채널'
    },
  ];

  // 연동된 SNS가 없는 경우 안내 메시지
  const hasNoConnections = !statsLoading && calculatedStats.connectedCount === 0;

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
        <h2>Dashboard</h2>
        <p className="dashboard-greeting">{getGreeting()}, {user?.username || 'User'}님!</p>
      </div>

      <div className="stats-grid">
        {stats.map((stat, index) => (
          <div key={index} className="stat-card">
            <div className="stat-content">
              <div className="stat-label">{stat.label}</div>
              <div className="stat-value">
                {statsLoading ? (
                  <span className="stat-loading"></span>
                ) : (
                  stat.value
                )}
              </div>
              {stat.subLabel && (
                <div className="stat-sub-label">{stat.subLabel}</div>
              )}
            </div>
          </div>
        ))}
      </div>

      {hasNoConnections && (
        <div className="no-connection-notice">
          <p>SNS 계정을 연동하면 실제 통계를 확인할 수 있습니다.</p>
        </div>
      )}

      <div className="dashboard-content">
        <div className="content-section">
          <div className="section-title">
            <h3>최근 콘텐츠</h3>
            <button className="view-all-btn" onClick={() => navigate('/content/list')}>
              전체보기 →
            </button>
          </div>
          <div className="content-list">
            {recentContents.map((content) => (
              <div key={content.id} className="content-item">
                <div className="content-info">
                  <h4>{content.title}</h4>
                  <div className="content-meta">
                    <span className="content-type">{content.type}</span>
                    <span className="meta-divider">•</span>
                    <span className="content-date">{content.date}</span>
                  </div>
                </div>
                <span className={`content-status status-${content.status}`}>
                  {content.status}
                </span>
              </div>
            ))}
          </div>
          {recentContents.length === 0 && (
            <div className="empty-state">
              <p>아직 생성된 콘텐츠가 없어요</p>
              <button className="create-first-btn" onClick={() => navigate('/content/ai-generator')}>
                첫 콘텐츠 만들기
              </button>
            </div>
          )}
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
