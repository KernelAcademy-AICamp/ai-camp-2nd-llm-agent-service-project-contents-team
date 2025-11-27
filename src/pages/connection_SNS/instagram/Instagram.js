import React, { useState, useEffect, useCallback } from 'react';
import { instagramAPI } from '../../../services/api';
import { useAuth } from '../../../contexts/AuthContext';
import './Instagram.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Instagram() {
  const { user } = useAuth();
  const [connection, setConnection] = useState(null);
  const [posts, setPosts] = useState([]);
  const [insights, setInsights] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState('posts');
  const [error, setError] = useState(null);
  const [showAccountSelector, setShowAccountSelector] = useState(false);

  // URL 파라미터 확인 (연동 성공/실패)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('connected') === 'true') {
      setError(null);
      window.history.replaceState({}, '', '/instagram');
    }
    if (params.get('error')) {
      const errorType = params.get('error');
      if (errorType === 'no_pages') {
        setError('연결된 Facebook 페이지가 없습니다. 먼저 Facebook 페이지를 생성하세요.');
      } else if (errorType === 'no_instagram_account') {
        setError('Facebook 페이지에 연결된 Instagram 비즈니스 계정이 없습니다.');
      } else {
        setError('Instagram 연동에 실패했습니다. 다시 시도해주세요.');
      }
      window.history.replaceState({}, '', '/instagram');
    }
  }, []);

  // 연동 상태 확인
  const fetchStatus = useCallback(async () => {
    try {
      const data = await instagramAPI.getStatus();
      setConnection(data);
      if (data) {
        if (data.instagram_account_id) {
          fetchPosts();
          fetchInsights();
        } else {
          fetchAccounts();
          setShowAccountSelector(true);
        }
      }
    } catch (err) {
      console.error('Failed to fetch Instagram status:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 연결 가능한 Instagram 계정 목록 조회
  const fetchAccounts = async () => {
    try {
      const data = await instagramAPI.getAccounts();
      setAccounts(data || []);
    } catch (err) {
      console.error('Failed to fetch accounts:', err);
    }
  };

  // 게시물 목록 조회
  const fetchPosts = async () => {
    try {
      const data = await instagramAPI.getPosts(0, 50);
      setPosts(data || []);
    } catch (err) {
      console.error('Failed to fetch posts:', err);
    }
  };

  // 인사이트 조회
  const fetchInsights = async () => {
    try {
      const data = await instagramAPI.getInsights();
      setInsights(data);
    } catch (err) {
      console.error('Failed to fetch insights:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Instagram 연동 시작
  const handleConnect = () => {
    if (!user?.id) {
      setError('로그인이 필요합니다.');
      return;
    }
    window.location.href = `${API_URL}/api/instagram/connect?user_id=${user.id}`;
  };

  // 연동 해제
  const handleDisconnect = async () => {
    if (!window.confirm('Instagram 연동을 해제하시겠습니까?')) return;

    try {
      await instagramAPI.disconnect();
      setConnection(null);
      setPosts([]);
      setInsights(null);
      setAccounts([]);
    } catch (err) {
      setError('연동 해제에 실패했습니다.');
    }
  };

  // 계정 선택
  const handleSelectAccount = async (instagramUserId) => {
    try {
      await instagramAPI.selectAccount(instagramUserId);
      setShowAccountSelector(false);
      fetchStatus();
    } catch (err) {
      setError('계정 선택에 실패했습니다.');
    }
  };

  // 게시물 동기화
  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await instagramAPI.syncPosts();
      alert(`동기화 완료! ${result.synced_count}개의 새 게시물을 가져왔습니다.`);
      fetchPosts();
      fetchStatus();
    } catch (err) {
      setError('동기화에 실패했습니다.');
    } finally {
      setSyncing(false);
    }
  };

  // 숫자 포맷팅
  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
  };

  if (loading) {
    return (
      <div className="instagram-page">
        <div className="loading-spinner">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="instagram-page">
      <div className="instagram-header">
        <h2>Instagram 관리</h2>
        <p>Instagram 비즈니스 계정을 연동하고 콘텐츠를 관리하세요</p>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)}>닫기</button>
        </div>
      )}

      {!connection ? (
        // 연동 안됨 상태
        <div className="connect-section">
          <div className="connect-card">
            <div className="connect-icon">📸</div>
            <h3>Instagram 비즈니스 계정 연동</h3>
            <p>Instagram 비즈니스 계정을 연동하여 게시물을 관리하고 인사이트를 확인하세요.</p>
            <ul className="feature-list">
              <li>게시물 목록 조회 및 관리</li>
              <li>좋아요, 댓글 등 통계 확인</li>
              <li>계정 인사이트 분석</li>
              <li>새 게시물 발행</li>
            </ul>
            <div className="requirement-notice">
              <strong>연동 요구사항:</strong>
              <ul>
                <li>Instagram 비즈니스 또는 크리에이터 계정</li>
                <li>Facebook 페이지와 연결된 계정</li>
              </ul>
            </div>
            <button className="btn-connect-instagram" onClick={handleConnect}>
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>
              </svg>
              Instagram 계정 연동하기
            </button>
          </div>
        </div>
      ) : showAccountSelector ? (
        // 계정 선택 화면
        <div className="account-selector-section">
          <div className="account-selector-card">
            <h3>Instagram 계정 선택</h3>
            <p>연동할 Instagram 비즈니스 계정을 선택해주세요.</p>
            {accounts.length === 0 ? (
              <div className="no-accounts">
                <p>연결된 Instagram 비즈니스 계정이 없습니다.</p>
                <p>Instagram에서 비즈니스 계정으로 전환하고 Facebook 페이지와 연결해주세요.</p>
              </div>
            ) : (
              <div className="account-list">
                {accounts.map((account) => (
                  <div
                    key={account.id}
                    className="account-item"
                    onClick={() => handleSelectAccount(account.id)}
                  >
                    <img
                      src={account.profile_picture_url || '/default-avatar.png'}
                      alt={account.username}
                      className="account-picture"
                    />
                    <div className="account-info">
                      <h4>@{account.username}</h4>
                      <p>{account.name}</p>
                      <div className="account-stats">
                        <span>{formatNumber(account.followers_count)} 팔로워</span>
                        <span>{formatNumber(account.media_count)} 게시물</span>
                      </div>
                      <p className="linked-page">연결된 페이지: {account.facebook_page_name}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <button className="btn-secondary" onClick={handleDisconnect}>
              연동 해제
            </button>
          </div>
        </div>
      ) : (
        // 연동됨 상태
        <>
          {/* 계정 정보 */}
          <div className="account-info-card">
            <div className="account-header">
              <img
                src={connection.instagram_profile_picture_url || '/default-avatar.png'}
                alt={connection.instagram_username}
                className="account-thumbnail"
              />
              <div className="account-details">
                <h3>@{connection.instagram_username}</h3>
                {connection.instagram_name && (
                  <span className="account-name">{connection.instagram_name}</span>
                )}
                {connection.instagram_biography && (
                  <p className="account-bio">{connection.instagram_biography}</p>
                )}
              </div>
              <div className="account-actions">
                <button className="btn-secondary" onClick={handleSync} disabled={syncing}>
                  {syncing ? '동기화 중...' : '게시물 동기화'}
                </button>
                <button className="btn-secondary" onClick={() => setShowAccountSelector(true)}>
                  계정 변경
                </button>
                <button className="btn-danger" onClick={handleDisconnect}>
                  연동 해제
                </button>
              </div>
            </div>
            <div className="account-stats-bar">
              <div className="stat-item">
                <span className="stat-value">{formatNumber(connection.followers_count)}</span>
                <span className="stat-label">팔로워</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{formatNumber(connection.follows_count)}</span>
                <span className="stat-label">팔로잉</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{formatNumber(connection.media_count)}</span>
                <span className="stat-label">게시물</span>
              </div>
            </div>
          </div>

          {/* 탭 네비게이션 */}
          <div className="instagram-tabs">
            <button
              className={`tab-btn ${activeTab === 'posts' ? 'active' : ''}`}
              onClick={() => setActiveTab('posts')}
            >
              게시물
            </button>
            <button
              className={`tab-btn ${activeTab === 'insights' ? 'active' : ''}`}
              onClick={() => setActiveTab('insights')}
            >
              인사이트
            </button>
          </div>

          {/* 탭 콘텐츠 */}
          <div className="tab-content">
            {activeTab === 'posts' && (
              <div className="posts-section">
                <div className="section-header">
                  <h3>게시물 ({posts.length}개)</h3>
                </div>
                {posts.length === 0 ? (
                  <div className="empty-state">
                    <p>게시물이 없습니다. 동기화 버튼을 클릭하여 Instagram에서 게시물을 가져오세요.</p>
                  </div>
                ) : (
                  <div className="post-grid">
                    {posts.map((post) => (
                      <div key={post.id} className="post-card">
                        <div className="post-image">
                          {post.media_type === 'VIDEO' ? (
                            <img src={post.thumbnail_url || post.media_url} alt="" />
                          ) : (
                            <img src={post.media_url} alt="" />
                          )}
                          {post.media_type === 'VIDEO' && (
                            <span className="media-type-badge">동영상</span>
                          )}
                          {post.media_type === 'CAROUSEL_ALBUM' && (
                            <span className="media-type-badge">캐러셀</span>
                          )}
                        </div>
                        <div className="post-content">
                          <p className="post-caption">
                            {post.caption ? post.caption.substring(0, 100) + (post.caption.length > 100 ? '...' : '') : '(캡션 없음)'}
                          </p>
                          <div className="post-stats">
                            <span>❤️ {formatNumber(post.like_count)}</span>
                            <span>💬 {formatNumber(post.comments_count)}</span>
                          </div>
                          <div className="post-date">
                            {post.timestamp && new Date(post.timestamp).toLocaleDateString('ko-KR')}
                          </div>
                        </div>
                        {post.permalink && (
                          <a
                            href={post.permalink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="post-link"
                          >
                            보기
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'insights' && (
              <div className="insights-section">
                <h3>계정 인사이트</h3>
                {insights && insights.data && insights.data.length > 0 ? (
                  <div className="insights-grid">
                    {insights.data.map((metric, index) => (
                      <div key={index} className="insight-card">
                        <span className="insight-label">{metric.title || metric.name}</span>
                        <span className="insight-value">
                          {metric.values && metric.values[0]
                            ? formatNumber(metric.values[0].value)
                            : 'N/A'}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <p>인사이트 데이터를 가져올 수 없습니다.</p>
                    <p>비즈니스 계정에서만 인사이트를 확인할 수 있습니다.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default Instagram;
