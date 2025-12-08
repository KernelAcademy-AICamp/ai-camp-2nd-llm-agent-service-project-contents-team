import React, { useState, useEffect, useCallback } from 'react';
import { threadsAPI } from '../../../services/api';
import { useAuth } from '../../../contexts/AuthContext';
import './Threads.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Threads() {
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
      const data = await threadsAPI.getPosts(0, 50);
      setPosts(data || []);
    } catch (err) {
      console.error('Failed to fetch posts:', err);
    }
  }, []);

  // 연동 상태 확인
  const fetchStatus = useCallback(async () => {
    try {
      const data = await threadsAPI.getStatus();
      setConnection(data);
      if (data) {
        fetchPosts();
      }
    } catch (err) {
      console.error('Failed to fetch Threads status:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchPosts]);

  // 초기 로드 및 URL 파라미터 확인
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);

    if (params.get('connected') === 'true') {
      setError(null);
      window.history.replaceState({}, '', '/threads');
    }
    if (params.get('error')) {
      setError('Threads 연동에 실패했습니다. 다시 시도해주세요.');
      window.history.replaceState({}, '', '/threads');
    }

    // 상태 가져오기
    fetchStatus();
  }, [fetchStatus]);

  // Threads 연동 시작
  const handleConnect = () => {
    if (!user?.id) {
      setError('로그인이 필요합니다.');
      return;
    }
    window.location.href = `${API_URL}/api/threads/connect?user_id=${user.id}`;
  };

  // 연동 해제
  const handleDisconnect = async () => {
    if (!window.confirm('Threads 연동을 해제하시겠습니까?')) return;

    try {
      await threadsAPI.disconnect();
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
      const result = await threadsAPI.syncPosts();
      alert(`동기화 완료! ${result.synced_count || 0}개의 포스트를 가져왔습니다.`);
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
      <div className="threads-page">
        <div className="loading-spinner">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="threads-page">
      <div className="threads-header">
        <h2>Threads 관리</h2>
        <p>Threads 계정을 연동하고 포스트를 관리하세요</p>
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
              <svg viewBox="0 0 192 192" width="64" height="64">
                <path fill="currentColor" d="M141.537 88.9883C140.71 88.5919 139.87 88.2104 139.019 87.8451C137.537 60.5382 122.616 44.905 97.5619 44.745C97.4484 44.7443 97.3355 44.7443 97.222 44.7443C82.2364 44.7443 69.7731 51.1409 62.102 62.7807L75.881 72.2328C81.6116 63.5383 90.6052 61.6848 97.2266 61.6848C97.3051 61.6848 97.3827 61.6848 97.4594 61.6855C105.707 61.7381 111.932 64.1366 115.961 68.814C118.893 72.2193 120.854 76.925 121.825 82.8638C114.511 81.6207 106.601 81.2385 98.145 81.7233C74.3247 83.0954 59.0111 96.9879 60.0396 116.292C60.5615 126.084 65.4397 134.508 73.775 140.011C80.8224 144.663 89.899 146.938 99.3323 146.423C111.79 145.74 121.563 140.987 128.381 132.296C133.559 125.696 136.834 117.143 138.28 106.366C144.217 109.949 148.617 114.664 151.047 120.332C155.179 129.967 155.42 145.8 142.501 158.708C131.182 170.016 117.576 174.908 97.0135 175.059C74.2042 174.89 56.9538 167.575 45.7381 153.317C35.2355 139.966 29.8077 120.682 29.6052 96C29.8077 71.3175 35.2355 52.0337 45.7381 38.6827C56.9538 24.4249 74.2039 17.11 97.0132 16.9405C120.038 17.1113 137.536 24.4614 148.955 38.788C154.359 45.5687 158.402 53.8915 160.989 63.4962L176.96 59.6267C173.59 46.9666 168.25 36.1558 160.855 27.3569C146.115 9.61287 124.739 0.270049 97.0695 0.00146779C97.0426 0.001375 97.0159 0.00128174 96.9892 0.00128174C96.9614 0.00128174 96.9342 0.001375 96.9065 0.00146779C69.2347 0.270049 47.8581 9.61287 33.1182 27.3569C16.5697 48.3197 13.0458 71.6709 12.6655 96C13.0458 120.329 16.5697 143.68 33.1182 164.643C47.8581 182.387 69.2344 191.73 96.9065 191.999C96.9336 191.999 96.9614 191.999 96.9892 191.999C97.0159 191.999 97.0426 191.999 97.0695 191.999C124.695 191.731 146.023 182.386 160.855 164.643C180.362 140.992 179.938 110.571 169.286 94.0256C162.361 83.1122 150.883 74.7974 136.063 69.4857C136.683 75.6754 136.907 82.3196 136.644 89.3784C136.62 89.9666 136.583 90.5481 136.54 91.1236C137.593 91.5793 138.619 92.0609 139.614 92.5674C153.058 99.5416 161.09 109.995 162.105 122.266C163.133 134.702 157.016 146.606 145.161 153.885C135.088 159.955 121.39 163.06 105.099 162.863C93.2296 162.711 83.5974 159.714 77.0641 154.157C70.934 148.948 67.6479 141.631 67.3282 132.663C66.808 118.697 77.5965 107.861 95.6624 106.755C100.997 106.444 106.058 106.439 110.839 106.721C116.288 106.979 121.388 107.553 126.104 108.415C126.047 112.478 125.67 116.155 124.963 119.407C123.534 126.071 120.463 131.102 115.741 134.431C110.456 138.167 103.143 140.157 94.2509 140.402C88.4388 140.571 81.7814 139.344 76.2747 136.103C70.3506 132.616 66.9697 127.461 66.7063 121.032C66.2413 109.723 77.8048 100.468 95.0614 99.4978C102.169 99.0953 108.872 99.3934 115.033 100.391C115.003 100.133 114.976 99.8743 114.954 99.6146C114.627 95.7816 114.775 92.1063 115.402 88.6248C108.868 87.8135 101.943 87.5577 94.4795 87.9747C70.3699 89.4051 52.6773 105.013 53.6973 127.478C54.2084 137.903 59.2389 146.905 68.0619 152.914C77.0116 159.009 89.1052 161.829 102.629 161.429C118.785 160.965 133.054 156.639 143.836 148.831C155.954 139.994 162.587 127.274 161.544 113.36C160.671 101.698 154.232 92.0549 141.537 88.9883Z"/>
              </svg>
            </div>
            <h3>Threads 계정 연동</h3>
            <p>Threads 계정을 연동하여 포스트를 관리하고 콘텐츠를 게시하세요.</p>
            <ul className="feature-list">
              <li>포스트 목록 조회 및 관리</li>
              <li>새 포스트 작성 및 게시</li>
              <li>이미지/미디어 포스트 게시</li>
              <li>팔로워 및 참여도 통계 확인</li>
            </ul>
            <button className="btn-connect-threads" onClick={handleConnect}>
              <svg viewBox="0 0 192 192" width="20" height="20">
                <path fill="currentColor" d="M141.537 88.9883C140.71 88.5919 139.87 88.2104 139.019 87.8451C137.537 60.5382 122.616 44.905 97.5619 44.745C97.4484 44.7443 97.3355 44.7443 97.222 44.7443C82.2364 44.7443 69.7731 51.1409 62.102 62.7807L75.881 72.2328C81.6116 63.5383 90.6052 61.6848 97.2266 61.6848C97.3051 61.6848 97.3827 61.6848 97.4594 61.6855C105.707 61.7381 111.932 64.1366 115.961 68.814C118.893 72.2193 120.854 76.925 121.825 82.8638C114.511 81.6207 106.601 81.2385 98.145 81.7233C74.3247 83.0954 59.0111 96.9879 60.0396 116.292C60.5615 126.084 65.4397 134.508 73.775 140.011C80.8224 144.663 89.899 146.938 99.3323 146.423C111.79 145.74 121.563 140.987 128.381 132.296C133.559 125.696 136.834 117.143 138.28 106.366C144.217 109.949 148.617 114.664 151.047 120.332C155.179 129.967 155.42 145.8 142.501 158.708C131.182 170.016 117.576 174.908 97.0135 175.059C74.2042 174.89 56.9538 167.575 45.7381 153.317C35.2355 139.966 29.8077 120.682 29.6052 96C29.8077 71.3175 35.2355 52.0337 45.7381 38.6827C56.9538 24.4249 74.2039 17.11 97.0132 16.9405C120.038 17.1113 137.536 24.4614 148.955 38.788C154.359 45.5687 158.402 53.8915 160.989 63.4962L176.96 59.6267C173.59 46.9666 168.25 36.1558 160.855 27.3569C146.115 9.61287 124.739 0.270049 97.0695 0.00146779C97.0426 0.001375 97.0159 0.00128174 96.9892 0.00128174C96.9614 0.00128174 96.9342 0.001375 96.9065 0.00146779C69.2347 0.270049 47.8581 9.61287 33.1182 27.3569C16.5697 48.3197 13.0458 71.6709 12.6655 96C13.0458 120.329 16.5697 143.68 33.1182 164.643C47.8581 182.387 69.2344 191.73 96.9065 191.999C96.9336 191.999 96.9614 191.999 96.9892 191.999C97.0159 191.999 97.0426 191.999 97.0695 191.999C124.695 191.731 146.023 182.386 160.855 164.643C180.362 140.992 179.938 110.571 169.286 94.0256C162.361 83.1122 150.883 74.7974 136.063 69.4857C136.683 75.6754 136.907 82.3196 136.644 89.3784C136.62 89.9666 136.583 90.5481 136.54 91.1236C137.593 91.5793 138.619 92.0609 139.614 92.5674C153.058 99.5416 161.09 109.995 162.105 122.266C163.133 134.702 157.016 146.606 145.161 153.885C135.088 159.955 121.39 163.06 105.099 162.863C93.2296 162.711 83.5974 159.714 77.0641 154.157C70.934 148.948 67.6479 141.631 67.3282 132.663C66.808 118.697 77.5965 107.861 95.6624 106.755C100.997 106.444 106.058 106.439 110.839 106.721C116.288 106.979 121.388 107.553 126.104 108.415C126.047 112.478 125.67 116.155 124.963 119.407C123.534 126.071 120.463 131.102 115.741 134.431C110.456 138.167 103.143 140.157 94.2509 140.402C88.4388 140.571 81.7814 139.344 76.2747 136.103C70.3506 132.616 66.9697 127.461 66.7063 121.032C66.2413 109.723 77.8048 100.468 95.0614 99.4978C102.169 99.0953 108.872 99.3934 115.033 100.391C115.003 100.133 114.976 99.8743 114.954 99.6146C114.627 95.7816 114.775 92.1063 115.402 88.6248C108.868 87.8135 101.943 87.5577 94.4795 87.9747C70.3699 89.4051 52.6773 105.013 53.6973 127.478C54.2084 137.903 59.2389 146.905 68.0619 152.914C77.0116 159.009 89.1052 161.829 102.629 161.429C118.785 160.965 133.054 156.639 143.836 148.831C155.954 139.994 162.587 127.274 161.544 113.36C160.671 101.698 154.232 92.0549 141.537 88.9883Z"/>
              </svg>
              Threads 계정 연동하기
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
                src={connection.threads_profile_picture_url || '/default-avatar.png'}
                alt={connection.name}
                className="account-thumbnail"
              />
              <div className="account-details">
                <h3>{connection.name || connection.username}</h3>
                <a
                  href={`https://threads.net/@${connection.username}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="account-url"
                >
                  @{connection.username}
                </a>
                {connection.threads_biography && (
                  <p className="account-bio">{connection.threads_biography}</p>
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
                <span className="stat-value">{posts.length}</span>
                <span className="stat-label">동기화된 포스트</span>
              </div>
            </div>
          </div>

          {/* 탭 네비게이션 */}
          <div className="threads-tabs">
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
                    <p>포스트가 없습니다. 동기화 버튼을 클릭하여 Threads에서 포스트를 가져오세요.</p>
                  </div>
                ) : (
                  <div className="post-list">
                    {posts.map((post) => (
                      <div key={post.id} className="post-card">
                        <div className="post-content">
                          <p className="post-text">{post.text}</p>
                          {post.media_url && (
                            <div className="post-media">
                              {post.media_type === 'VIDEO' ? (
                                <video src={post.media_url} controls />
                              ) : (
                                <img src={post.media_url} alt="Post media" />
                              )}
                            </div>
                          )}
                        </div>
                        <div className="post-stats">
                          <span>❤️ {formatNumber(post.like_count)}</span>
                          <span>💬 {formatNumber(post.reply_count)}</span>
                          <span>🔁 {formatNumber(post.repost_count)}</span>
                          <span>👁️ {formatNumber(post.views_count)}</span>
                        </div>
                        <div className="post-footer">
                          <span className="post-date">{formatDate(post.timestamp)}</span>
                          {post.permalink && (
                            <a
                              href={post.permalink}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="view-on-threads"
                            >
                              Threads에서 보기
                            </a>
                          )}
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
  const [imageUrl, setImageUrl] = useState('');
  const [posting, setPosting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!text.trim() && !imageUrl.trim()) {
      alert('포스트 내용을 입력하거나 이미지 URL을 입력해주세요.');
      return;
    }

    if (text.length > 500) {
      alert('포스트는 500자를 초과할 수 없습니다.');
      return;
    }

    setPosting(true);

    try {
      await threadsAPI.createPost({
        text: text.trim() || null,
        image_url: imageUrl.trim() || null
      });

      alert('포스트가 게시되었습니다!');
      setText('');
      setImageUrl('');
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
            placeholder="무슨 생각을 하고 계신가요?"
            rows={4}
            maxLength={500}
            disabled={posting}
          />
          <div className="char-count">
            <span className={text.length > 450 ? 'warning' : ''}>
              {text.length}/500
            </span>
          </div>
        </div>

        <div className="form-group">
          <label>이미지 URL (선택사항)</label>
          <input
            type="url"
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            placeholder="https://example.com/image.jpg"
            disabled={posting}
          />
        </div>

        {imageUrl && (
          <div className="media-preview">
            <img src={imageUrl} alt="Preview" onError={(e) => e.target.style.display = 'none'} />
          </div>
        )}

        <div className="compose-actions">
          <button type="submit" className="btn-post" disabled={posting || (!text.trim() && !imageUrl.trim())}>
            {posting ? '게시 중...' : '포스트하기'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default Threads;
