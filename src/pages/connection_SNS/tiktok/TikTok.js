import { useState, useEffect, useCallback } from 'react';
import { tiktokAPI } from '../../../services/api';
import { useAuth } from '../../../contexts/AuthContext';
import { FaTiktok } from 'react-icons/fa6';
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
import { formatNumber, formatDate, formatDuration, API_URL } from '../common/utils';
import '../common/SNSCommon.css';
import './TikTok.css';

// TikTok 탭 설정
const TIKTOK_TABS = [
  { id: 'videos', label: '동영상' },
  { id: 'upload', label: '업로드' }
];

// TikTok 연동 기능 목록
const TIKTOK_FEATURES = [
  '동영상 목록 조회 및 관리',
  '새 동영상 업로드 (URL 방식)',
  '팔로워 및 좋아요 통계 확인',
  '동영상 조회수 및 참여도 분석'
];

function TikTok() {
  const { user } = useAuth();
  const [connection, setConnection] = useState(null);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState('videos');
  const [error, setError] = useState(null);

  // 동영상 목록 조회
  const fetchVideos = useCallback(async () => {
    try {
      const data = await tiktokAPI.getVideos(0, 50);
      setVideos(data || []);
    } catch (err) {
      console.error('Failed to fetch videos:', err);
    }
  }, []);

  // 연동 상태 확인
  const fetchStatus = useCallback(async () => {
    try {
      const data = await tiktokAPI.getStatus();
      setConnection(data);
      if (data) {
        fetchVideos();
      }
    } catch (err) {
      console.error('Failed to fetch TikTok status:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchVideos]);

  // 초기 로드 및 URL 파라미터 확인
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('connected') === 'true') {
      setError(null);
      // 연동 성공 시 페이지 새로고침하여 사이드바 업데이트
      window.location.replace('/tiktok');
      return;
    }
    if (params.get('error')) {
      setError('TikTok 연동에 실패했습니다. 다시 시도해주세요.');
      window.history.replaceState({}, '', '/tiktok');
    }
    fetchStatus();
  }, [fetchStatus]);

  // TikTok 연동 시작
  const handleConnect = () => {
    if (!user?.id) {
      setError('로그인이 필요합니다.');
      return;
    }
    window.location.href = `${API_URL}/api/tiktok/connect?user_id=${user.id}`;
  };

  // 연동 해제
  const handleDisconnect = async () => {
    if (!window.confirm('TikTok 연동을 해제하시겠습니까?')) return;
    try {
      await tiktokAPI.disconnect();
      setConnection(null);
      setVideos([]);
    } catch (err) {
      setError('연동 해제에 실패했습니다.');
    }
  };

  // 동영상 동기화
  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await tiktokAPI.syncVideos();
      alert(`동기화 완료! ${result.synced_count || 0}개의 동영상을 가져왔습니다.`);
      fetchVideos();
      fetchStatus();
    } catch (err) {
      setError('동기화에 실패했습니다.');
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return <LoadingSpinner className="tiktok" />;
  }

  // 계정 통계 데이터
  const accountStats = connection ? [
    { value: connection.follower_count, label: '팔로워' },
    { value: connection.following_count, label: '팔로잉' },
    { value: connection.likes_count, label: '좋아요' },
    { value: connection.video_count, label: '동영상' }
  ] : [];

  return (
    <div className="tiktok-page">
      <PageHeader
        title="TikTok 관리"
        description="TikTok 계정을 연동하고 동영상을 관리하세요"
      />

      <ErrorMessage error={error} onClose={() => setError(null)} />

      {!connection ? (
        <ConnectCard
          icon={<FaTiktok size={64} />}
          title="TikTok 계정 연동"
          description="TikTok 계정을 연동하여 동영상을 관리하고 콘텐츠를 업로드하세요."
          features={TIKTOK_FEATURES}
          button={
            <button className="btn-connect-tiktok" onClick={handleConnect}>
              <FaTiktok size={20} />
              TikTok 계정 연동하기
            </button>
          }
        />
      ) : (
        <>
          <AccountInfoCard
            thumbnailUrl={connection.avatar_url}
            name={connection.display_name || connection.username}
            subInfo={
              <a
                href={`https://tiktok.com/@${connection.username}`}
                target="_blank"
                rel="noopener noreferrer"
                className="account-url"
              >
                @{connection.username}
              </a>
            }
            bio={connection.bio}
            stats={accountStats}
            actions={
              <>
                <SyncButton syncing={syncing} onClick={handleSync} label="동영상 동기화" />
                <DisconnectButton onClick={handleDisconnect} />
              </>
            }
          />

          <TabNavigation
            tabs={TIKTOK_TABS}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            className="tiktok"
          />

          <div className="tab-content">
            {activeTab === 'videos' && (
              <VideosTab videos={videos} />
            )}

            {activeTab === 'upload' && (
              <VideoUploadForm onSuccess={() => {
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
        <EmptyState message="동영상이 없습니다. 동기화 버튼을 클릭하여 TikTok에서 동영상을 가져오세요." />
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
        {video.cover_image_url ? (
          <img src={video.cover_image_url} alt={video.title || '동영상'} />
        ) : (
          <div className="video-placeholder">
            <FaTiktok size={32} />
          </div>
        )}
        <div className="video-duration">{formatDuration(video.duration)}</div>
      </div>
      <div className="video-info">
        <h4 className="video-title">{video.title || '제목 없음'}</h4>
        {video.description && (
          <p className="video-description">{video.description}</p>
        )}
        <div className="video-stats">
          <span>👁️ {formatNumber(video.view_count)}</span>
          <span>❤️ {formatNumber(video.like_count)}</span>
          <span>💬 {formatNumber(video.comment_count)}</span>
          <span>🔄 {formatNumber(video.share_count)}</span>
        </div>
        <div className="video-footer">
          <span className="video-date">{formatDate(video.created_at)}</span>
          {video.share_url && (
            <a
              href={video.share_url}
              target="_blank"
              rel="noopener noreferrer"
              className="view-on-tiktok"
            >
              TikTok에서 보기
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

// 동영상 업로드 폼 컴포넌트
function VideoUploadForm({ onSuccess }) {
  const [videoUrl, setVideoUrl] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!videoUrl.trim()) {
      alert('동영상 URL을 입력해주세요.');
      return;
    }

    setUploading(true);

    try {
      await tiktokAPI.uploadVideo({
        video_url: videoUrl.trim(),
        title: title.trim() || null,
        description: description.trim() || null
      });

      alert('동영상 업로드가 요청되었습니다! TikTok에서 처리 후 게시됩니다.');
      setVideoUrl('');
      setTitle('');
      setDescription('');
      onSuccess();
    } catch (err) {
      console.error('Upload failed:', err);
      alert('동영상 업로드에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-section">
      <h3>동영상 업로드</h3>
      <p className="upload-notice">
        TikTok API는 URL을 통한 동영상 업로드를 지원합니다.
        공개적으로 접근 가능한 동영상 URL을 입력해주세요.
      </p>
      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-group">
          <label>동영상 URL *</label>
          <input
            type="url"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            placeholder="https://example.com/video.mp4"
            required
            disabled={uploading}
          />
        </div>

        <div className="form-group">
          <label>제목 (선택사항)</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="동영상 제목"
            maxLength={150}
            disabled={uploading}
          />
        </div>

        <div className="form-group">
          <label>설명 (선택사항)</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="동영상에 대한 설명을 입력하세요"
            rows={3}
            maxLength={2200}
            disabled={uploading}
          />
        </div>

        <div className="upload-actions">
          <button
            type="submit"
            className="btn-upload"
            disabled={uploading || !videoUrl.trim()}
          >
            {uploading ? '업로드 중...' : '업로드하기'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default TikTok;
