import React, { useState, useEffect, useCallback } from 'react';
import { xAPI } from '../../../services/api';
import { useAuth } from '../../../contexts/AuthContext';
import './X.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function X() {
  const { user } = useAuth();
  const [connection, setConnection] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState('posts');
  const [error, setError] = useState(null);

  // 포스트 목록 조회
  const fetchPosts = useCallback(async () => {
    try {
      const data = await xAPI.getPosts(0, 50);
      setPosts(data || []);
    } catch (err) {
      console.error('Failed to fetch posts:', err);
    }
  }, []);

  // 연동 상태 확인
  const fetchStatus = useCallback(async () => {
    try {
      const data = await xAPI.getStatus();
      setConnection(data);
      if (data) {
        fetchPosts();
      }
    } catch (err) {
      console.error('Failed to fetch X status:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchPosts]);

  // 초기 로드 및 URL 파라미터 확인
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);

    if (params.get('connected') === 'true') {
      setError(null);
      window.history.replaceState({}, '', '/x');
    }
    if (params.get('error')) {
      setError('X 연동에 실패했습니다. 다시 시도해주세요.');
      window.history.replaceState({}, '', '/x');
    }

    // 상태 가져오기
    fetchStatus();
  }, [fetchStatus]);

  // Twitter 연동 시작
  const handleConnect = () => {
    if (!user?.id) {
      setError('로그인이 필요합니다.');
      return;
    }
    window.location.href = `${API_URL}/api/x/connect?user_id=${user.id}`;
  };

  // 연동 해제
  const handleDisconnect = async () => {
    if (!window.confirm('X 연동을 해제하시겠습니까?')) return;

    try {
      await xAPI.disconnect();
      setConnection(null);
      setPosts([]);
    } catch (err) {
      setError('연동 해제에 실패했습니다.');
    }
  };

  // 포스트 동기화
  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await xAPI.syncPosts();
      alert(`동기화 완료! ${result.synced_count || 0}개의 포스트를 가져왔습니다.`);
      fetchPosts();
      fetchStatus();
    } catch (err) {
      // 401 에러 시 토큰 만료로 자동 연동 해제됨
      if (err.response?.status === 401) {
        setError('X 토큰이 만료되어 연동이 해제되었습니다. 다시 연동해주세요.');
        setConnection(null);
        setPosts([]);
      } else {
        setError('동기화에 실패했습니다.');
      }
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

  // 날짜 포맷팅
  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="x-page">
        <div className="loading-spinner">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="x-page">
      <div className="x-header">
        <h2>X 관리</h2>
        <p>X 계정을 연동하고 포스트를 관리하세요</p>
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
            <div className="connect-icon">
              <svg viewBox="0 0 24 24" width="64" height="64">
                <path fill="currentColor" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
            </div>
            <h3>X 계정 연동</h3>
            <p>X 계정을 연동하여 포스트를 관리하고 콘텐츠를 게시하세요.</p>
            <ul className="feature-list">
              <li>포스트 목록 조회 및 관리</li>
              <li>새 포스트 작성 및 게시</li>
              <li>이미지/미디어 포스트 게시</li>
              <li>팔로워 및 참여도 통계 확인</li>
            </ul>
            <button className="btn-connect-x" onClick={handleConnect}>
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="currentColor" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
              X 계정 연동하기
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
                src={connection.profile_image_url || '/default-avatar.png'}
                alt={connection.name}
                className="account-thumbnail"
              />
              <div className="account-details">
                <h3>{connection.name}</h3>
                <a
                  href={`https://twitter.com/${connection.username}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="account-url"
                >
                  @{connection.username}
                </a>
                {connection.description && (
                  <p className="account-bio">{connection.description}</p>
                )}
              </div>
              <div className="account-actions">
                <button className="btn-secondary" onClick={handleSync} disabled={syncing}>
                  {syncing ? '동기화 중...' : '포스트 동기화'}
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
                <span className="stat-value">{formatNumber(connection.following_count)}</span>
                <span className="stat-label">팔로잉</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{formatNumber(connection.post_count)}</span>
                <span className="stat-label">포스트</span>
              </div>
            </div>
          </div>

          {/* 탭 네비게이션 */}
          <div className="x-tabs">
            <button
              className={`tab-btn ${activeTab === 'posts' ? 'active' : ''}`}
              onClick={() => setActiveTab('posts')}
            >
              포스트
            </button>
            <button
              className={`tab-btn ${activeTab === 'compose' ? 'active' : ''}`}
              onClick={() => setActiveTab('compose')}
            >
              새 포스트
            </button>
          </div>

          {/* 탭 콘텐츠 */}
          <div className="tab-content">
            {activeTab === 'posts' && (
              <div className="posts-section">
                <div className="section-header">
                  <h3>내 포스트 ({posts.length}개)</h3>
                </div>
                {posts.length === 0 ? (
                  <div className="empty-state">
                    <p>포스트가 없습니다. 동기화 버튼을 클릭하여 X에서 포스트를 가져오세요.</p>
                  </div>
                ) : (
                  <div className="post-list">
                    {posts.map((post) => (
                      <div key={post.id} className="post-card">
                        <div className="post-content">
                          <p className="post-text">{post.text}</p>
                          {post.media_url && (
                            <div className="post-media">
                              <img src={post.media_url} alt="Post media" />
                            </div>
                          )}
                        </div>
                        <div className="post-stats">
                          <span>❤️ {formatNumber(post.like_count)}</span>
                          <span>🔁 {formatNumber(post.repost_count)}</span>
                          <span>💬 {formatNumber(post.reply_count)}</span>
                          <span>👁️ {formatNumber(post.impression_count)}</span>
                        </div>
                        <div className="post-date">
                          {formatDate(post.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'compose' && (
              <PostComposeForm onSuccess={() => {
                fetchPosts();
                setActiveTab('posts');
              }} />
            )}
          </div>
        </>
      )}
    </div>
  );
}

// 포스트 작성 폼 컴포넌트
function PostComposeForm({ onSuccess }) {
  const [text, setText] = useState('');
  const [mediaFile, setMediaFile] = useState(null);
  const [mediaPreview, setMediaPreview] = useState(null);
  const [posting, setPosting] = useState(false);

  const handleMediaChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setMediaFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setMediaPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeMedia = () => {
    setMediaFile(null);
    setMediaPreview(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!text.trim() && !mediaFile) {
      alert('포스트 내용을 입력하거나 미디어를 첨부해주세요.');
      return;
    }

    if (text.length > 280) {
      alert('포스트는 280자를 초과할 수 없습니다.');
      return;
    }

    setPosting(true);

    try {
      if (mediaFile) {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('media', mediaFile);
        await xAPI.createMediaPost(formData);
      } else {
        await xAPI.createPost({ text });
      }

      alert('포스트가 게시되었습니다!');
      setText('');
      setMediaFile(null);
      setMediaPreview(null);
      onSuccess();
    } catch (err) {
      console.error('Post failed:', err);
      alert('포스트 게시에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="compose-section">
      <h3>새 포스트 작성</h3>
      <form onSubmit={handleSubmit} className="compose-form">
        <div className="form-group">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="무슨 일이 일어나고 있나요?"
            rows={4}
            maxLength={280}
            disabled={posting}
          />
          <div className="char-count">
            <span className={text.length > 260 ? 'warning' : ''}>
              {text.length}/280
            </span>
          </div>
        </div>

        {mediaPreview && (
          <div className="media-preview">
            <img src={mediaPreview} alt="Preview" />
            <button type="button" className="remove-media" onClick={removeMedia}>
              ✕
            </button>
          </div>
        )}

        <div className="compose-actions">
          <label className="media-upload-btn">
            <input
              type="file"
              accept="image/*,video/*"
              onChange={handleMediaChange}
              disabled={posting}
              hidden
            />
            📷 미디어 추가
          </label>

          <button type="submit" className="btn-post" disabled={posting || (!text.trim() && !mediaFile)}>
            {posting ? '게시 중...' : '포스트하기'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default X;
