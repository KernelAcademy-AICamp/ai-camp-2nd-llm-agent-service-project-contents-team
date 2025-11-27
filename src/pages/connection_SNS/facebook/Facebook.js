import React, { useState, useEffect, useCallback } from 'react';
import { facebookAPI } from '../../../services/api';
import { useAuth } from '../../../contexts/AuthContext';
import './Facebook.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Facebook() {
  const { user } = useAuth();
  const [connection, setConnection] = useState(null);
  const [posts, setPosts] = useState([]);
  const [insights, setInsights] = useState(null);
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState('posts');
  const [error, setError] = useState(null);
  const [showPageSelector, setShowPageSelector] = useState(false);

  // URL 파라미터 확인 (연동 성공/실패)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('connected') === 'true') {
      setError(null);
      window.history.replaceState({}, '', '/facebook');
    }
    if (params.get('error')) {
      setError('Facebook 연동에 실패했습니다. 다시 시도해주세요.');
      window.history.replaceState({}, '', '/facebook');
    }
  }, []);

  // 연동 상태 확인
  const fetchStatus = useCallback(async () => {
    try {
      const data = await facebookAPI.getStatus();
      setConnection(data);
      if (data) {
        if (data.page_id) {
          fetchPosts();
          fetchInsights();
        } else {
          // 페이지가 선택되지 않은 경우 페이지 목록 조회
          fetchPages();
          setShowPageSelector(true);
        }
      }
    } catch (err) {
      console.error('Failed to fetch Facebook status:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 관리하는 페이지 목록 조회
  const fetchPages = async () => {
    try {
      const data = await facebookAPI.getPages();
      setPages(data || []);
    } catch (err) {
      console.error('Failed to fetch pages:', err);
    }
  };

  // 게시물 목록 조회
  const fetchPosts = async () => {
    try {
      const data = await facebookAPI.getPosts(0, 50);
      setPosts(data || []);
    } catch (err) {
      console.error('Failed to fetch posts:', err);
    }
  };

  // 인사이트 조회
  const fetchInsights = async () => {
    try {
      const data = await facebookAPI.getInsights();
      setInsights(data);
    } catch (err) {
      console.error('Failed to fetch insights:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Facebook 연동 시작
  const handleConnect = () => {
    if (!user?.id) {
      setError('로그인이 필요합니다.');
      return;
    }
    window.location.href = `${API_URL}/api/facebook/connect?user_id=${user.id}`;
  };

  // 연동 해제
  const handleDisconnect = async () => {
    if (!window.confirm('Facebook 연동을 해제하시겠습니까?')) return;

    try {
      await facebookAPI.disconnect();
      setConnection(null);
      setPosts([]);
      setInsights(null);
      setPages([]);
    } catch (err) {
      setError('연동 해제에 실패했습니다.');
    }
  };

  // 페이지 선택
  const handleSelectPage = async (pageId) => {
    try {
      await facebookAPI.selectPage(pageId);
      setShowPageSelector(false);
      fetchStatus();
    } catch (err) {
      setError('페이지 선택에 실패했습니다.');
    }
  };

  // 게시물 동기화
  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await facebookAPI.syncPosts();
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
      <div className="facebook-page">
        <div className="loading-spinner">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="facebook-page">
      <div className="facebook-header">
        <h2>Facebook 관리</h2>
        <p>Facebook 페이지를 연동하고 콘텐츠를 관리하세요</p>
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
            <div className="connect-icon">📘</div>
            <h3>Facebook 페이지 연동</h3>
            <p>Facebook 페이지를 연동하여 게시물을 관리하고 인사이트를 확인하세요.</p>
            <ul className="feature-list">
              <li>페이지 게시물 목록 조회 및 관리</li>
              <li>새 게시물 작성</li>
              <li>좋아요, 댓글, 공유 등 통계 확인</li>
              <li>페이지 인사이트 분석</li>
            </ul>
            <button className="btn-connect-facebook" onClick={handleConnect}>
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
              </svg>
              Facebook 페이지 연동하기
            </button>
          </div>
        </div>
      ) : showPageSelector ? (
        // 페이지 선택 화면
        <div className="page-selector-section">
          <div className="page-selector-card">
            <h3>관리할 페이지 선택</h3>
            <p>연동할 Facebook 페이지를 선택해주세요.</p>
            {pages.length === 0 ? (
              <div className="no-pages">
                <p>관리 중인 Facebook 페이지가 없습니다.</p>
                <p>먼저 Facebook에서 페이지를 생성해주세요.</p>
              </div>
            ) : (
              <div className="page-list">
                {pages.map((page) => (
                  <div
                    key={page.id}
                    className="page-item"
                    onClick={() => handleSelectPage(page.id)}
                  >
                    <img
                      src={page.picture_url || '/default-avatar.png'}
                      alt={page.name}
                      className="page-picture"
                    />
                    <div className="page-info">
                      <h4>{page.name}</h4>
                      <p>{page.category}</p>
                      <div className="page-stats">
                        <span>{formatNumber(page.fan_count)} 좋아요</span>
                        <span>{formatNumber(page.followers_count)} 팔로워</span>
                      </div>
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
          {/* 페이지 정보 */}
          <div className="page-info-card">
            <div className="page-header">
              <img
                src={connection.page_picture_url || '/default-avatar.png'}
                alt={connection.page_name}
                className="page-thumbnail"
              />
              <div className="page-details">
                <h3>{connection.page_name}</h3>
                {connection.page_category && (
                  <span className="page-category">{connection.page_category}</span>
                )}
              </div>
              <div className="page-actions">
                <button className="btn-secondary" onClick={handleSync} disabled={syncing}>
                  {syncing ? '동기화 중...' : '게시물 동기화'}
                </button>
                <button className="btn-secondary" onClick={() => setShowPageSelector(true)}>
                  페이지 변경
                </button>
                <button className="btn-danger" onClick={handleDisconnect}>
                  연동 해제
                </button>
              </div>
            </div>
            <div className="page-stats-bar">
              <div className="stat-item">
                <span className="stat-value">{formatNumber(connection.page_fan_count)}</span>
                <span className="stat-label">좋아요</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{formatNumber(connection.page_followers_count)}</span>
                <span className="stat-label">팔로워</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{posts.length}</span>
                <span className="stat-label">게시물</span>
              </div>
            </div>
          </div>

          {/* 탭 네비게이션 */}
          <div className="facebook-tabs">
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
            <button
              className={`tab-btn ${activeTab === 'create' ? 'active' : ''}`}
              onClick={() => setActiveTab('create')}
            >
              새 게시물
            </button>
          </div>

          {/* 탭 콘텐츠 */}
          <div className="tab-content">
            {activeTab === 'posts' && (
              <div className="posts-section">
                <div className="section-header">
                  <h3>페이지 게시물 ({posts.length}개)</h3>
                </div>
                {posts.length === 0 ? (
                  <div className="empty-state">
                    <p>게시물이 없습니다. 동기화 버튼을 클릭하여 Facebook에서 게시물을 가져오세요.</p>
                  </div>
                ) : (
                  <div className="post-list">
                    {posts.map((post) => (
                      <div key={post.id} className="post-card">
                        {post.full_picture && (
                          <div className="post-image">
                            <img src={post.full_picture} alt="" />
                          </div>
                        )}
                        <div className="post-content">
                          <p className="post-message">
                            {post.message || post.story || '(내용 없음)'}
                          </p>
                          <div className="post-stats">
                            <span>👍 {formatNumber(post.likes_count)}</span>
                            <span>💬 {formatNumber(post.comments_count)}</span>
                            <span>🔄 {formatNumber(post.shares_count)}</span>
                          </div>
                          <div className="post-date">
                            {post.created_time && new Date(post.created_time).toLocaleDateString('ko-KR')}
                          </div>
                        </div>
                        {post.permalink_url && (
                          <a
                            href={post.permalink_url}
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
                <h3>페이지 인사이트 (최근 30일)</h3>
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
                  </div>
                )}
              </div>
            )}

            {activeTab === 'create' && (
              <div className="create-post-section">
                <h3>새 게시물 작성</h3>
                <div className="permission-notice">
                  <p>게시물 작성 기능은 Facebook 앱 검토가 필요합니다.</p>
                  <p>현재 개발 모드에서는 페이지 조회 및 인사이트 기능만 사용 가능합니다.</p>
                  <ul>
                    <li>pages_manage_posts - 페이지 게시물 작성/수정/삭제</li>
                    <li>pages_read_user_content - 사용자 콘텐츠 읽기</li>
                  </ul>
                  <p>앱 검토를 완료하면 이 기능을 사용할 수 있습니다.</p>
                  <a
                    href="https://developers.facebook.com/docs/app-review"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary"
                  >
                    Facebook 앱 검토 문서 보기
                  </a>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default Facebook;
