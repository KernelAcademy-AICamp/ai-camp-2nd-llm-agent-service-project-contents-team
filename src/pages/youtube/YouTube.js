import React, { useState, useEffect, useCallback } from 'react';
import { youtubeAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import './YouTube.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function YouTube() {
  const { user } = useAuth();
  const [connection, setConnection] = useState(null);
  const [videos, setVideos] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState('videos');
  const [error, setError] = useState(null);

  // URL 파라미터 확인 (연동 성공/실패)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('connected') === 'true') {
      setError(null);
      // URL 파라미터 제거
      window.history.replaceState({}, '', '/youtube');
    }
    if (params.get('error')) {
      setError('YouTube 연동에 실패했습니다. 다시 시도해주세요.');
      window.history.replaceState({}, '', '/youtube');
    }
  }, []);

  // 연동 상태 확인
  const fetchStatus = useCallback(async () => {
    try {
      const data = await youtubeAPI.getStatus();
      setConnection(data);
      if (data) {
        fetchVideos();
        fetchAnalytics();
      }
    } catch (err) {
      console.error('Failed to fetch YouTube status:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 동영상 목록 조회
  const fetchVideos = async () => {
    try {
      const data = await youtubeAPI.getVideos(0, 50);
      setVideos(data || []);
    } catch (err) {
      console.error('Failed to fetch videos:', err);
    }
  };

  // 분석 데이터 조회
  const fetchAnalytics = async () => {
    try {
      const data = await youtubeAPI.getAnalyticsSummary();
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // YouTube 연동 시작
  const handleConnect = () => {
    if (!user?.id) {
      setError('로그인이 필요합니다.');
      return;
    }
    window.location.href = `${API_URL}/api/youtube/connect?user_id=${user.id}`;
  };

  // 연동 해제
  const handleDisconnect = async () => {
    if (!window.confirm('YouTube 연동을 해제하시겠습니까?')) return;

    try {
      await youtubeAPI.disconnect();
      setConnection(null);
      setVideos([]);
      setAnalytics(null);
    } catch (err) {
      setError('연동 해제에 실패했습니다.');
    }
  };

  // 동영상 동기화
  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await youtubeAPI.syncVideos();
      alert(`동기화 완료! ${result.synced_count}개의 새 동영상을 가져왔습니다.`);
      fetchVideos();
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

  // 시간 포맷팅 (PT4M13S -> 4:13)
  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="youtube-page">
        <div className="loading-spinner">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="youtube-page">
      <div className="youtube-header">
        <h2>YouTube 관리</h2>
        <p>YouTube 채널을 연동하고 콘텐츠를 관리하세요</p>
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
            <div className="connect-icon">🎬</div>
            <h3>YouTube 채널 연동</h3>
            <p>YouTube 채널을 연동하여 동영상을 관리하고 분석 데이터를 확인하세요.</p>
            <ul className="feature-list">
              <li>채널 동영상 목록 조회 및 관리</li>
              <li>동영상 직접 업로드</li>
              <li>조회수, 좋아요, 댓글 등 통계 확인</li>
              <li>트래픽 소스 및 시청자 분석</li>
            </ul>
            <button className="btn-connect-youtube" onClick={handleConnect}>
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
              </svg>
              YouTube 채널 연동하기
            </button>
          </div>
        </div>
      ) : (
        // 연동됨 상태
        <>
          {/* 채널 정보 */}
          <div className="channel-info-card">
            <div className="channel-header">
              <img
                src={connection.channel_thumbnail_url || '/default-avatar.png'}
                alt={connection.channel_title}
                className="channel-thumbnail"
              />
              <div className="channel-details">
                <h3>{connection.channel_title}</h3>
                {connection.channel_custom_url && (
                  <a
                    href={`https://youtube.com/${connection.channel_custom_url}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="channel-url"
                  >
                    {connection.channel_custom_url}
                  </a>
                )}
              </div>
              <div className="channel-actions">
                <button className="btn-secondary" onClick={handleSync} disabled={syncing}>
                  {syncing ? '동기화 중...' : '동영상 동기화'}
                </button>
                <button className="btn-danger" onClick={handleDisconnect}>
                  연동 해제
                </button>
              </div>
            </div>
            <div className="channel-stats">
              <div className="stat-item">
                <span className="stat-value">{formatNumber(connection.subscriber_count)}</span>
                <span className="stat-label">구독자</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{formatNumber(connection.video_count)}</span>
                <span className="stat-label">동영상</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{formatNumber(connection.view_count)}</span>
                <span className="stat-label">총 조회수</span>
              </div>
            </div>
          </div>

          {/* 탭 네비게이션 */}
          <div className="youtube-tabs">
            <button
              className={`tab-btn ${activeTab === 'videos' ? 'active' : ''}`}
              onClick={() => setActiveTab('videos')}
            >
              동영상
            </button>
            <button
              className={`tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
              onClick={() => setActiveTab('analytics')}
            >
              분석
            </button>
            <button
              className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
              onClick={() => setActiveTab('upload')}
            >
              업로드
            </button>
          </div>

          {/* 탭 콘텐츠 */}
          <div className="tab-content">
            {activeTab === 'videos' && (
              <div className="videos-section">
                <div className="section-header">
                  <h3>내 동영상 ({videos.length}개)</h3>
                </div>
                {videos.length === 0 ? (
                  <div className="empty-state">
                    <p>동영상이 없습니다. 동기화 버튼을 클릭하여 YouTube에서 동영상을 가져오세요.</p>
                  </div>
                ) : (
                  <div className="video-grid">
                    {videos.map((video) => (
                      <div key={video.id} className="video-card">
                        <div className="video-thumbnail">
                          <img src={video.thumbnail_url || '/default-thumbnail.png'} alt={video.title} />
                          <span className="video-duration">{formatDuration(video.duration_seconds)}</span>
                          {video.privacy_status !== 'public' && (
                            <span className={`privacy-badge ${video.privacy_status}`}>
                              {video.privacy_status === 'private' ? '비공개' : '일부공개'}
                            </span>
                          )}
                        </div>
                        <div className="video-info">
                          <h4 className="video-title">{video.title}</h4>
                          <div className="video-stats">
                            <span>조회수 {formatNumber(video.view_count)}</span>
                            <span>좋아요 {formatNumber(video.like_count)}</span>
                            <span>댓글 {formatNumber(video.comment_count)}</span>
                          </div>
                          <div className="video-date">
                            {video.published_at && new Date(video.published_at).toLocaleDateString('ko-KR')}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'analytics' && (
              <div className="analytics-section">
                {analytics ? (
                  <>
                    <div className="analytics-header">
                      <h3>채널 분석 (최근 30일)</h3>
                      <p>{analytics.period?.start_date} ~ {analytics.period?.end_date}</p>
                    </div>

                    {analytics.analytics?.rows && analytics.analytics.rows.length > 0 ? (
                      <div className="analytics-grid">
                        <div className="analytics-card">
                          <span className="analytics-label">조회수</span>
                          <span className="analytics-value">
                            {formatNumber(analytics.analytics.rows[0][0])}
                          </span>
                        </div>
                        <div className="analytics-card">
                          <span className="analytics-label">시청 시간 (분)</span>
                          <span className="analytics-value">
                            {formatNumber(Math.round(analytics.analytics.rows[0][1]))}
                          </span>
                        </div>
                        <div className="analytics-card">
                          <span className="analytics-label">평균 시청 시간</span>
                          <span className="analytics-value">
                            {formatDuration(Math.round(analytics.analytics.rows[0][2]))}
                          </span>
                        </div>
                        <div className="analytics-card">
                          <span className="analytics-label">좋아요</span>
                          <span className="analytics-value">
                            {formatNumber(analytics.analytics.rows[0][3])}
                          </span>
                        </div>
                        <div className="analytics-card">
                          <span className="analytics-label">댓글</span>
                          <span className="analytics-value">
                            {formatNumber(analytics.analytics.rows[0][5])}
                          </span>
                        </div>
                        <div className="analytics-card">
                          <span className="analytics-label">공유</span>
                          <span className="analytics-value">
                            {formatNumber(analytics.analytics.rows[0][6])}
                          </span>
                        </div>
                        <div className="analytics-card positive">
                          <span className="analytics-label">신규 구독자</span>
                          <span className="analytics-value">
                            +{formatNumber(analytics.analytics.rows[0][7])}
                          </span>
                        </div>
                        <div className="analytics-card negative">
                          <span className="analytics-label">구독 취소</span>
                          <span className="analytics-value">
                            -{formatNumber(analytics.analytics.rows[0][8])}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="empty-state">
                        <p>분석 데이터를 가져올 수 없습니다.</p>
                      </div>
                    )}

                    {/* 인기 동영상 */}
                    {analytics.top_videos?.rows && (
                      <div className="top-videos-section">
                        <h4>인기 동영상 Top 5</h4>
                        <div className="top-videos-list">
                          {analytics.top_videos.rows.slice(0, 5).map((row, index) => {
                            const video = videos.find(v => v.video_id === row[0]);
                            return (
                              <div key={index} className="top-video-item">
                                <span className="rank">{index + 1}</span>
                                <span className="title">{video?.title || row[0]}</span>
                                <span className="views">{formatNumber(row[1])} 조회</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="empty-state">
                    <p>분석 데이터를 불러오는 중...</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'upload' && (
              <VideoUploadForm onUploadSuccess={() => {
                fetchVideos();
                setActiveTab('videos');
              }} />
            )}
          </div>
        </>
      )}
    </div>
  );
}

// 동영상 업로드 폼 컴포넌트
function VideoUploadForm({ onUploadSuccess }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    tags: '',
    privacy_status: 'private',
  });
  const [videoFile, setVideoFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!videoFile) {
      alert('동영상 파일을 선택해주세요.');
      return;
    }

    setUploading(true);
    setProgress(10);

    try {
      const data = new FormData();
      data.append('video_file', videoFile);
      data.append('title', formData.title);
      data.append('description', formData.description);
      data.append('tags', formData.tags);
      data.append('privacy_status', formData.privacy_status);

      setProgress(30);

      await youtubeAPI.uploadVideo(data);

      setProgress(100);
      alert('동영상이 업로드되었습니다!');

      // 폼 초기화
      setFormData({ title: '', description: '', tags: '', privacy_status: 'private' });
      setVideoFile(null);

      onUploadSuccess();
    } catch (err) {
      console.error('Upload failed:', err);
      alert('업로드에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <div className="upload-section">
      <h3>동영상 업로드</h3>
      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-group">
          <label>동영상 파일 *</label>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setVideoFile(e.target.files[0])}
            disabled={uploading}
          />
          {videoFile && (
            <p className="file-name">선택됨: {videoFile.name}</p>
          )}
        </div>

        <div className="form-group">
          <label>제목 *</label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="동영상 제목"
            required
            disabled={uploading}
          />
        </div>

        <div className="form-group">
          <label>설명</label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="동영상 설명"
            rows={4}
            disabled={uploading}
          />
        </div>

        <div className="form-group">
          <label>태그 (쉼표로 구분)</label>
          <input
            type="text"
            value={formData.tags}
            onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
            placeholder="태그1, 태그2, 태그3"
            disabled={uploading}
          />
        </div>

        <div className="form-group">
          <label>공개 설정</label>
          <select
            value={formData.privacy_status}
            onChange={(e) => setFormData({ ...formData, privacy_status: e.target.value })}
            disabled={uploading}
          >
            <option value="private">비공개</option>
            <option value="unlisted">일부 공개</option>
            <option value="public">공개</option>
          </select>
        </div>

        {uploading && (
          <div className="upload-progress">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <span>{progress}%</span>
          </div>
        )}

        <button type="submit" className="btn-upload" disabled={uploading || !videoFile}>
          {uploading ? '업로드 중...' : '업로드'}
        </button>
      </form>
    </div>
  );
}

export default YouTube;
