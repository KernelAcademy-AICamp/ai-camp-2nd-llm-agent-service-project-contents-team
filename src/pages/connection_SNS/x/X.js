import { useState, useEffect, useCallback } from 'react';
import { xAPI } from '../../../services/api';
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
  DisconnectButton,
  CharCounter,
  MediaPreview
} from '../common/SNSComponents';
import { formatNumber, formatDate, API_URL } from '../common/utils';
import '../common/SNSCommon.css';
import './X.css';

// X 아이콘 SVG path
const X_ICON_PATH = "M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z";

// X 탭 설정
const X_TABS = [
  { id: 'posts', label: '포스트' },
  { id: 'compose', label: '새 포스트' }
];

// X 연동 기능 목록
const X_FEATURES = [
  '포스트 목록 조회 및 관리',
  '새 포스트 작성 및 게시',
  '이미지/미디어 포스트 게시',
  '팔로워 및 참여도 통계 확인'
];

// X 아이콘 컴포넌트
const XIcon = ({ size = 64 }) => (
  <svg viewBox="0 0 24 24" width={size} height={size}>
    <path fill="currentColor" d={X_ICON_PATH} />
  </svg>
);

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
      // 연동 성공 시 페이지 새로고침하여 사이드바 업데이트
      window.location.replace('/x');
      return;
    }
    if (params.get('error')) {
      setError('X 연동에 실패했습니다. 다시 시도해주세요.');
      window.history.replaceState({}, '', '/x');
    }
    fetchStatus();
  }, [fetchStatus]);

  // X 연동 시작
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

  if (loading) {
    return <LoadingSpinner className="x" />;
  }

  // 계정 통계 데이터
  const accountStats = connection ? [
    { value: connection.followers_count, label: '팔로워' },
    { value: connection.following_count, label: '팔로잉' },
    { value: connection.post_count, label: '포스트' }
  ] : [];

  return (
    <div className="x-page">
      <PageHeader
        title="X 관리"
        description="X 계정을 연동하고 포스트를 관리하세요"
      />

      <ErrorMessage error={error} onClose={() => setError(null)} />

      {!connection ? (
        <ConnectCard
          icon={<XIcon />}
          title="X 계정 연동"
          description="X 계정을 연동하여 포스트를 관리하고 콘텐츠를 게시하세요."
          features={X_FEATURES}
          button={
            <button className="btn-connect-x" onClick={handleConnect}>
              <XIcon size={20} />
              X 계정 연동하기
            </button>
          }
        />
      ) : (
        <>
          <AccountInfoCard
            thumbnailUrl={connection.profile_image_url}
            name={connection.name}
            subInfo={
              <a
                href={`https://twitter.com/${connection.username}`}
                target="_blank"
                rel="noopener noreferrer"
                className="account-url"
              >
                @{connection.username}
              </a>
            }
            bio={connection.description}
            stats={accountStats}
            actions={
              <>
                <SyncButton syncing={syncing} onClick={handleSync} label="포스트 동기화" />
                <DisconnectButton onClick={handleDisconnect} />
              </>
            }
          />

          <TabNavigation
            tabs={X_TABS}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            className="x"
          />

          <div className="tab-content">
            {activeTab === 'posts' && (
              <PostsTab posts={posts} />
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

// 포스트 탭 컴포넌트
function PostsTab({ posts }) {
  return (
    <div className="posts-section">
      <SectionHeader title="내 포스트" count={posts.length} />
      {posts.length === 0 ? (
        <EmptyState message="포스트가 없습니다. 동기화 버튼을 클릭하여 X에서 포스트를 가져오세요." />
      ) : (
        <div className="post-list">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}
    </div>
  );
}

// 포스트 카드 컴포넌트
function PostCard({ post }) {
  return (
    <div className="post-card">
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
      <div className="post-date">{formatDate(post.created_at)}</div>
    </div>
  );
}

// 포스트 작성 폼 컴포넌트
function PostComposeForm({ onSuccess }) {
  const [text, setText] = useState('');
  const [mediaFile, setMediaFile] = useState(null);
  const [mediaPreview, setMediaPreview] = useState(null);
  const [posting, setPosting] = useState(false);

  const MAX_LENGTH = 280;
  const WARNING_THRESHOLD = 260;

  const handleMediaChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setMediaFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setMediaPreview(reader.result);
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

    if (text.length > MAX_LENGTH) {
      alert(`포스트는 ${MAX_LENGTH}자를 초과할 수 없습니다.`);
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
      removeMedia();
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
            maxLength={MAX_LENGTH}
            disabled={posting}
          />
          <CharCounter
            current={text.length}
            max={MAX_LENGTH}
            warningThreshold={WARNING_THRESHOLD}
          />
        </div>

        {mediaPreview && (
          <MediaPreview src={mediaPreview} onRemove={removeMedia} />
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

          <button
            type="submit"
            className="btn-post"
            disabled={posting || (!text.trim() && !mediaFile)}
          >
            {posting ? '게시 중...' : '포스트하기'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default X;
