import React, { useState, useEffect, useCallback } from 'react';
import { twitterAPI } from '../../../services/api';
import { useAuth } from '../../../contexts/AuthContext';
import './Twitter.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Twitter() {
  const { user } = useAuth();
  const [connection, setConnection] = useState(null);
  const [tweets, setTweets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState('tweets');
  const [error, setError] = useState(null);

  // URL 파라미터 확인 (연동 성공/실패)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('connected') === 'true') {
      setError(null);
      window.history.replaceState({}, '', '/twitter');
    }
    if (params.get('error')) {
      setError('Twitter 연동에 실패했습니다. 다시 시도해주세요.');
      window.history.replaceState({}, '', '/twitter');
    }
  }, []);

  // 연동 상태 확인
  const fetchStatus = useCallback(async () => {
    try {
      const data = await twitterAPI.getStatus();
      setConnection(data);
      if (data) {
        fetchTweets();
      }
    } catch (err) {
      console.error('Failed to fetch Twitter status:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 트윗 목록 조회
  const fetchTweets = async () => {
    try {
      const data = await twitterAPI.getTweets(0, 50);
      setTweets(data || []);
    } catch (err) {
      console.error('Failed to fetch tweets:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Twitter 연동 시작
  const handleConnect = () => {
    if (!user?.id) {
      setError('로그인이 필요합니다.');
      return;
    }
    window.location.href = `${API_URL}/api/twitter/connect?user_id=${user.id}`;
  };

  // 연동 해제
  const handleDisconnect = async () => {
    if (!window.confirm('Twitter 연동을 해제하시겠습니까?')) return;

    try {
      await twitterAPI.disconnect();
      setConnection(null);
      setTweets([]);
    } catch (err) {
      setError('연동 해제에 실패했습니다.');
    }
  };

  // 트윗 동기화
  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await twitterAPI.syncTweets();
      alert(`동기화 완료! ${result.synced_count || 0}개의 트윗을 가져왔습니다.`);
      fetchTweets();
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
      <div className="twitter-page">
        <div className="loading-spinner">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="twitter-page">
      <div className="twitter-header">
        <h2>Twitter(X) 관리</h2>
        <p>Twitter 계정을 연동하고 트윗을 관리하세요</p>
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
            <h3>Twitter(X) 계정 연동</h3>
            <p>Twitter 계정을 연동하여 트윗을 관리하고 콘텐츠를 게시하세요.</p>
            <ul className="feature-list">
              <li>트윗 목록 조회 및 관리</li>
              <li>새 트윗 작성 및 게시</li>
              <li>이미지/미디어 트윗 게시</li>
              <li>팔로워 및 참여도 통계 확인</li>
            </ul>
            <button className="btn-connect-twitter" onClick={handleConnect}>
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="currentColor" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
              Twitter 계정 연동하기
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
                  {syncing ? '동기화 중...' : '트윗 동기화'}
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
                <span className="stat-value">{formatNumber(connection.tweet_count)}</span>
                <span className="stat-label">트윗</span>
              </div>
            </div>
          </div>

          {/* 탭 네비게이션 */}
          <div className="twitter-tabs">
            <button
              className={`tab-btn ${activeTab === 'tweets' ? 'active' : ''}`}
              onClick={() => setActiveTab('tweets')}
            >
              트윗
            </button>
            <button
              className={`tab-btn ${activeTab === 'compose' ? 'active' : ''}`}
              onClick={() => setActiveTab('compose')}
            >
              새 트윗
            </button>
          </div>

          {/* 탭 콘텐츠 */}
          <div className="tab-content">
            {activeTab === 'tweets' && (
              <div className="tweets-section">
                <div className="section-header">
                  <h3>내 트윗 ({tweets.length}개)</h3>
                </div>
                {tweets.length === 0 ? (
                  <div className="empty-state">
                    <p>트윗이 없습니다. 동기화 버튼을 클릭하여 Twitter에서 트윗을 가져오세요.</p>
                  </div>
                ) : (
                  <div className="tweet-list">
                    {tweets.map((tweet) => (
                      <div key={tweet.id} className="tweet-card">
                        <div className="tweet-content">
                          <p className="tweet-text">{tweet.text}</p>
                          {tweet.media_url && (
                            <div className="tweet-media">
                              <img src={tweet.media_url} alt="Tweet media" />
                            </div>
                          )}
                        </div>
                        <div className="tweet-stats">
                          <span>❤️ {formatNumber(tweet.like_count)}</span>
                          <span>🔁 {formatNumber(tweet.retweet_count)}</span>
                          <span>💬 {formatNumber(tweet.reply_count)}</span>
                          <span>👁️ {formatNumber(tweet.impression_count)}</span>
                        </div>
                        <div className="tweet-date">
                          {formatDate(tweet.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'compose' && (
              <TweetComposeForm onSuccess={() => {
                fetchTweets();
                setActiveTab('tweets');
              }} />
            )}
          </div>
        </>
      )}
    </div>
  );
}

// 트윗 작성 폼 컴포넌트
function TweetComposeForm({ onSuccess }) {
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
      alert('트윗 내용을 입력하거나 미디어를 첨부해주세요.');
      return;
    }

    if (text.length > 280) {
      alert('트윗은 280자를 초과할 수 없습니다.');
      return;
    }

    setPosting(true);

    try {
      if (mediaFile) {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('media', mediaFile);
        await twitterAPI.createMediaTweet(formData);
      } else {
        await twitterAPI.createTweet({ text });
      }

      alert('트윗이 게시되었습니다!');
      setText('');
      setMediaFile(null);
      setMediaPreview(null);
      onSuccess();
    } catch (err) {
      console.error('Tweet failed:', err);
      alert('트윗 게시에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="compose-section">
      <h3>새 트윗 작성</h3>
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

          <button type="submit" className="btn-tweet" disabled={posting || (!text.trim() && !mediaFile)}>
            {posting ? '게시 중...' : '트윗하기'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default Twitter;
