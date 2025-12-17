import React, { useState, useEffect, useCallback } from 'react';
import { youtubeAPI } from '../../../services/api';
import { useAuth } from '../../../contexts/AuthContext';
import {
  LoadingSpinner,
  ErrorMessage,
  PageHeader,
  ConnectCard,
  AccountInfoCard,
  TabNavigation,
  EmptyState,
  SectionHeader,
  SyncButton,
  DisconnectButton
} from '../common/SNSComponents';
import { formatNumber, formatDuration, formatDateSimple, API_URL } from '../common/utils';
import '../common/SNSCommon.css';
import './YouTube.css';

// YouTube 탭 설정
const YOUTUBE_TABS = [
  { id: 'videos', label: '동영상' },
  { id: 'analytics', label: '분석' },
  { id: 'upload', label: '업로드' }
];

// YouTube 연동 기능 목록
const YOUTUBE_FEATURES = [
  '채널 동영상 목록 조회 및 관리',
  '동영상 직접 업로드',
  '조회수, 좋아요, 댓글 등 통계 확인',
  '트래픽 소스 및 시청자 분석'
];

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
      // 연동 성공 시 페이지 새로고침하여 사이드바 업데이트
      window.location.replace('/youtube');
      return;
    }
    if (params.get('error')) {
      setError('YouTube 연동에 실패했습니다. 다시 시도해주세요.');
      window.history.replaceState({}, '', '/youtube');
    }
  }, []);

  // 동영상 목록 조회
  const fetchVideos = useCallback(async () => {
    try {
      const data = await youtubeAPI.getVideos(0, 50);
      setVideos(data || []);
    } catch (err) {
      console.error('Failed to fetch videos:', err);
    }
  }, []);

  // 분석 데이터 조회
  const fetchAnalytics = useCallback(async () => {
    try {
      const data = await youtubeAPI.getAnalyticsSummary();
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
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
  }, [fetchVideos, fetchAnalytics]);

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

  if (loading) {
    return <LoadingSpinner className="youtube" />;
  }

  // 채널 통계 데이터
  const channelStats = connection ? [
    { value: connection.subscriber_count, label: '구독자' },
    { value: connection.video_count, label: '동영상' },
    { value: connection.view_count, label: '총 조회수' }
  ] : [];

  return (
    <div className="youtube-page">
      <PageHeader
        title="YouTube 관리"
        description="YouTube 채널을 연동하고 콘텐츠를 관리하세요"
      />

      <ErrorMessage error={error} onClose={() => setError(null)} />

      {!connection ? (
        <ConnectCard
          icon="🎬"
          title="YouTube 채널 연동"
          description="YouTube 채널을 연동하여 동영상을 관리하고 분석 데이터를 확인하세요."
          features={YOUTUBE_FEATURES}
          button={
            <button className="btn-connect-youtube" onClick={handleConnect}>
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
              </svg>
              YouTube 채널 연동하기
            </button>
          }
        />
      ) : (
        <>
          <AccountInfoCard
            thumbnailUrl={connection.channel_thumbnail_url}
            name={connection.channel_title}
            subInfo={
              connection.channel_custom_url && (
                <a
                  href={`https://youtube.com/${connection.channel_custom_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="account-url"
                >
                  {connection.channel_custom_url}
                </a>
              )
            }
            stats={channelStats}
            actions={
              <>
                <SyncButton syncing={syncing} onClick={handleSync} label="동영상 동기화" />
                <DisconnectButton onClick={handleDisconnect} />
              </>
            }
          />

          <TabNavigation
            tabs={YOUTUBE_TABS}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            className="youtube"
          />

          <div className="tab-content">
            {activeTab === 'videos' && (
              <VideosTab videos={videos} />
            )}

            {activeTab === 'analytics' && (
              <AnalyticsTab analytics={analytics} videos={videos} />
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

// 동영상 탭 컴포넌트
function VideosTab({ videos }) {
  return (
    <div className="videos-section">
      <SectionHeader title="내 동영상" count={videos.length} />
      {videos.length === 0 ? (
        <EmptyState message="동영상이 없습니다. 동기화 버튼을 클릭하여 YouTube에서 동영상을 가져오세요." />
      ) : (
        <div className="video-grid">
          {videos.map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>
      )}
    </div>
  );
}

// 동영상 카드 컴포넌트
function VideoCard({ video }) {
  return (
    <div className="video-card">
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
        <div className="video-date">{formatDateSimple(video.published_at)}</div>
      </div>
    </div>
  );
}

// 분석 탭 컴포넌트
function AnalyticsTab({ analytics, videos }) {
  if (!analytics) {
    return <EmptyState message="분석 데이터를 불러오는 중..." />;
  }

  const rows = analytics.analytics?.rows;
  const hasData = rows && rows.length > 0;

  return (
    <div className="analytics-section">
      <div className="analytics-header">
        <h3>채널 분석 (최근 30일)</h3>
        <p>{analytics.period?.start_date} ~ {analytics.period?.end_date}</p>
      </div>

      {hasData ? (
        <div className="analytics-grid">
          <AnalyticsCard label="조회수" value={formatNumber(rows[0][0])} />
          <AnalyticsCard label="시청 시간 (분)" value={formatNumber(Math.round(rows[0][1]))} />
          <AnalyticsCard label="평균 시청 시간" value={formatDuration(Math.round(rows[0][2]))} />
          <AnalyticsCard label="좋아요" value={formatNumber(rows[0][3])} />
          <AnalyticsCard label="댓글" value={formatNumber(rows[0][5])} />
          <AnalyticsCard label="공유" value={formatNumber(rows[0][6])} />
          <AnalyticsCard label="신규 구독자" value={`+${formatNumber(rows[0][7])}`} className="positive" />
          <AnalyticsCard label="구독 취소" value={`-${formatNumber(rows[0][8])}`} className="negative" />
        </div>
      ) : (
        <EmptyState message="분석 데이터를 가져올 수 없습니다." />
      )}

      {analytics.top_videos?.rows && (
        <TopVideosSection topVideos={analytics.top_videos.rows} videos={videos} />
      )}
    </div>
  );
}

// 분석 카드 컴포넌트
function AnalyticsCard({ label, value, className = '' }) {
  return (
    <div className={`analytics-card ${className}`}>
      <span className="analytics-label">{label}</span>
      <span className="analytics-value">{value}</span>
    </div>
  );
}

// 인기 동영상 섹션
function TopVideosSection({ topVideos, videos }) {
  return (
    <div className="top-videos-section">
      <h4>인기 동영상 Top 5</h4>
      <div className="top-videos-list">
        {topVideos.slice(0, 5).map((row, index) => {
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

  const handleChange = (field) => (e) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
  };

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
          {videoFile && <p className="file-name">선택됨: {videoFile.name}</p>}
        </div>

        <div className="form-group">
          <label>제목 *</label>
          <input
            type="text"
            value={formData.title}
            onChange={handleChange('title')}
            placeholder="동영상 제목"
            required
            disabled={uploading}
          />
        </div>

        <div className="form-group">
          <label>설명</label>
          <textarea
            value={formData.description}
            onChange={handleChange('description')}
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
            onChange={handleChange('tags')}
            placeholder="태그1, 태그2, 태그3"
            disabled={uploading}
          />
        </div>

        <div className="form-group">
          <label>공개 설정</label>
          <select
            value={formData.privacy_status}
            onChange={handleChange('privacy_status')}
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
