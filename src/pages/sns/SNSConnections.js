import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FiRefreshCw, FiUsers, FiEye, FiFileText } from 'react-icons/fi';
import { youtubeAPI, facebookAPI, instagramAPI, xAPI, threadsAPI } from '../../services/api';
import './SNSConnections.css';

// 플랫폼 설정
const PLATFORMS = [
  {
    id: 'youtube',
    name: 'YouTube',
    icon: '📺',
    api: youtubeAPI,
    path: '/youtube',
    getStatus: (data) => data ? data.channel_title : null,
    getStats: (data) => data ? [
      { label: '구독자', value: formatNumber(data.subscriber_count), icon: <FiUsers /> },
      { label: '조회수', value: formatNumber(data.view_count), icon: <FiEye /> },
      { label: '동영상', value: formatNumber(data.video_count), icon: <FiFileText /> },
    ] : [],
  },
  {
    id: 'facebook',
    name: 'Facebook',
    icon: '📘',
    api: facebookAPI,
    path: '/facebook',
    getStatus: (data) => data?.page_id ? data.page_name : null,
    getStats: (data) => data?.page_id ? [
      { label: '팔로워', value: formatNumber(data.page_followers_count), icon: <FiUsers /> },
    ] : [],
  },
  {
    id: 'instagram',
    name: 'Instagram',
    icon: '📷',
    api: instagramAPI,
    path: '/instagram',
    getStatus: (data) => data?.instagram_account_id ? `@${data.instagram_username}` : null,
    getStats: (data) => data?.instagram_account_id ? [
      { label: '팔로워', value: formatNumber(data.followers_count), icon: <FiUsers /> },
      { label: '게시물', value: formatNumber(data.media_count), icon: <FiFileText /> },
    ] : [],
  },
  {
    id: 'x',
    name: 'X (Twitter)',
    icon: '𝕏',
    api: xAPI,
    path: '/x',
    getStatus: (data) => data?.twitter_user_id ? `@${data.username}` : null,
    getStats: (data) => data?.twitter_user_id ? [
      { label: '팔로워', value: formatNumber(data.followers_count), icon: <FiUsers /> },
      { label: '팔로잉', value: formatNumber(data.following_count), icon: <FiUsers /> },
    ] : [],
  },
  {
    id: 'threads',
    name: 'Threads',
    icon: '🧵',
    api: threadsAPI,
    path: '/threads',
    getStatus: (data) => data?.threads_user_id ? `@${data.username}` : null,
    getStats: (data) => data?.threads_user_id ? [
      { label: '팔로워', value: formatNumber(data.followers_count), icon: <FiUsers /> },
    ] : [],
  },
];

// 숫자 포맷팅
function formatNumber(num) {
  if (!num) return '0';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toLocaleString();
}

function SNSConnections() {
  const [connections, setConnections] = useState({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(null);

  // 모든 플랫폼 상태 조회
  const fetchAllStatus = async () => {
    setLoading(true);
    const results = {};

    await Promise.all(
      PLATFORMS.map(async (platform) => {
        try {
          const data = await platform.api.getStatus();
          results[platform.id] = { data, error: null };
        } catch (err) {
          results[platform.id] = { data: null, error: err.message };
        }
      })
    );

    setConnections(results);
    setLoading(false);
  };

  // 개별 플랫폼 새로고침
  const refreshPlatform = async (platformId) => {
    setRefreshing(platformId);
    const platform = PLATFORMS.find(p => p.id === platformId);

    try {
      const data = await platform.api.getStatus();
      setConnections(prev => ({
        ...prev,
        [platformId]: { data, error: null },
      }));
    } catch (err) {
      setConnections(prev => ({
        ...prev,
        [platformId]: { data: null, error: err.message },
      }));
    } finally {
      setRefreshing(null);
    }
  };

  useEffect(() => {
    fetchAllStatus();
  }, []);

  // 연동된 플랫폼 수
  const connectedCount = PLATFORMS.filter(p => {
    const conn = connections[p.id];
    return conn?.data && p.getStatus(conn.data);
  }).length;

  // 총 팔로워 수 계산
  const totalFollowers = PLATFORMS.reduce((sum, p) => {
    const conn = connections[p.id];
    if (!conn?.data) return sum;

    if (p.id === 'youtube') return sum + (conn.data.subscriber_count || 0);
    if (p.id === 'facebook') return sum + (conn.data.page_followers_count || 0);
    if (p.id === 'instagram') return sum + (conn.data.followers_count || 0);
    if (p.id === 'x') return sum + (conn.data.followers_count || 0);
    if (p.id === 'threads') return sum + (conn.data.followers_count || 0);
    return sum;
  }, 0);

  return (
    <div className="sns-page">
      {/* 헤더 */}
      <div className="sns-page-header">
        <h2>SNS 연동 관리</h2>
        <p className="sns-page-subtitle">소셜 미디어 플랫폼을 연동하여 콘텐츠를 발행하세요</p>
      </div>

      {/* 통계 그리드 - Dashboard와 동일한 스타일 */}
      <div className="sns-stats-grid">
        <div className="sns-stat-card">
          <div className="sns-stat-content">
            <span className="sns-stat-label">연동된 플랫폼</span>
            {loading ? (
              <span className="sns-stat-loading"></span>
            ) : (
              <span className="sns-stat-value">{connectedCount}</span>
            )}
          </div>
        </div>
        <div className="sns-stat-card">
          <div className="sns-stat-content">
            <span className="sns-stat-label">미연동 플랫폼</span>
            {loading ? (
              <span className="sns-stat-loading"></span>
            ) : (
              <span className="sns-stat-value">{PLATFORMS.length - connectedCount}</span>
            )}
          </div>
        </div>
        <div className="sns-stat-card">
          <div className="sns-stat-content">
            <span className="sns-stat-label">총 팔로워</span>
            {loading ? (
              <span className="sns-stat-loading"></span>
            ) : (
              <span className="sns-stat-value">{formatNumber(totalFollowers)}</span>
            )}
          </div>
        </div>
        <div className="sns-stat-card">
          <div className="sns-stat-content">
            <span className="sns-stat-label">지원 플랫폼</span>
            <span className="sns-stat-value">{PLATFORMS.length}</span>
          </div>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      <div className="sns-content">
        {/* 플랫폼 리스트 섹션 */}
        <div className="sns-section">
          <div className="sns-section-title">
            <h3>플랫폼</h3>
            <button
              className="sns-refresh-btn"
              onClick={fetchAllStatus}
              disabled={loading}
            >
              <FiRefreshCw className={loading ? 'spinning' : ''} />
              새로고침
            </button>
          </div>

          <div className="sns-platform-list">
            {PLATFORMS.map((platform) => {
              const conn = connections[platform.id];
              const isConnected = conn?.data && platform.getStatus(conn.data);
              const stats = isConnected ? platform.getStats(conn.data) : [];
              const isRefreshing = refreshing === platform.id;

              return (
                <div
                  key={platform.id}
                  className={`sns-platform-item ${isConnected ? 'connected' : ''}`}
                >
                  <div className="sns-platform-main">
                    <span className="sns-platform-icon">{platform.icon}</span>
                    <div className="sns-platform-info">
                      <h4>{platform.name}</h4>
                      {loading ? (
                        <span className="sns-platform-status loading">확인 중...</span>
                      ) : isConnected ? (
                        <span className="sns-platform-status connected">
                          {platform.getStatus(conn.data)}
                        </span>
                      ) : (
                        <span className="sns-platform-status">미연동</span>
                      )}
                    </div>

                    {/* 통계 - 연동된 경우만 */}
                    {isConnected && stats.length > 0 && (
                      <div className="sns-platform-stats">
                        {stats.map((stat, idx) => (
                          <div key={idx} className="sns-mini-stat">
                            <span className="sns-mini-stat-value">{stat.value}</span>
                            <span className="sns-mini-stat-label">{stat.label}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="sns-platform-actions">
                      <button
                        className="sns-icon-btn"
                        onClick={() => refreshPlatform(platform.id)}
                        disabled={isRefreshing || loading}
                        title="새로고침"
                      >
                        <FiRefreshCw className={isRefreshing ? 'spinning' : ''} />
                      </button>
                      <Link to={platform.path} className="sns-action-btn">
                        {isConnected ? '관리' : '연동'}
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 안내 섹션 */}
        <div className="sns-section sns-info-section">
          <h3>안내</h3>
          <div className="sns-info-content">
            <div className="sns-info-item">
              <span className="sns-info-number">1</span>
              <div>
                <strong>연동하기</strong>
                <p>각 플랫폼의 연동 버튼을 클릭하면 OAuth 인증 페이지로 이동합니다.</p>
              </div>
            </div>
            <div className="sns-info-item">
              <span className="sns-info-number">2</span>
              <div>
                <strong>콘텐츠 발행</strong>
                <p>연동 후에는 해당 플랫폼에 직접 콘텐츠를 발행할 수 있습니다.</p>
              </div>
            </div>
            <div className="sns-info-item">
              <span className="sns-info-number">3</span>
              <div>
                <strong>Instagram 안내</strong>
                <p>Instagram은 Facebook 비즈니스 계정과 연결된 비즈니스/크리에이터 계정만 연동 가능합니다.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SNSConnections;
