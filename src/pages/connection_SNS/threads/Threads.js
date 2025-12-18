import { useState, useEffect, useCallback } from 'react';
import { threadsAPI } from '../../../services/api';
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
  MediaPreview,
  ThreadsIcon
} from '../common/SNSComponents';
import { formatNumber, formatDate, API_URL } from '../common/utils';
import '../common/SNSCommon.css';
import './Threads.css';

// Threads 탭 설정
const THREADS_TABS = [
  { id: 'posts', label: '포스트' },
  { id: 'compose', label: '새 포스트' }
];

// Threads 연동 기능 목록
const THREADS_FEATURES = [
  '포스트 목록 조회 및 관리',
  '새 포스트 작성 및 게시',
  '이미지/미디어 포스트 게시',
  '팔로워 및 참여도 통계 확인'
];

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
      // 연동 성공 시 페이지 새로고침하여 사이드바 업데이트
      window.location.replace('/threads');
      return;
    }
    if (params.get('error')) {
      setError('Threads 연동에 실패했습니다. 다시 시도해주세요.');
      window.history.replaceState({}, '', '/threads');
    }
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

  if (loading) {
    return <LoadingSpinner className="threads" />;
  }

  // 계정 통계 데이터
  const accountStats = connection ? [
    { value: connection.followers_count, label: '팔로워' },
    { value: posts.length, label: '동기화된 포스트' }
  ] : [];

  return (
    <div className="threads-page">
      <PageHeader
        title="Threads 관리"
        description="Threads 계정을 연동하고 포스트를 관리하세요"
      />

      <ErrorMessage error={error} onClose={() => setError(null)} />

      {!connection ? (
        <ConnectCard
          icon={<ThreadsIcon />}
          title="Threads 계정 연동"
          description="Threads 계정을 연동하여 포스트를 관리하고 콘텐츠를 게시하세요."
          features={THREADS_FEATURES}
          button={
            <button className="btn-connect-threads" onClick={handleConnect}>
              <ThreadsIcon size={20} />
              Threads 계정 연동하기
            </button>
          }
        />
      ) : (
        <>
          <AccountInfoCard
            thumbnailUrl={connection.threads_profile_picture_url}
            name={connection.name || connection.username}
            subInfo={
              <a
                href={`https://threads.net/@${connection.username}`}
                target="_blank"
                rel="noopener noreferrer"
                className="account-url"
              >
                @{connection.username}
              </a>
            }
            bio={connection.threads_biography}
            stats={accountStats}
            actions={
              <>
                <SyncButton syncing={syncing} onClick={handleSync} label="포스트 동기화" />
                <DisconnectButton onClick={handleDisconnect} />
              </>
            }
          />

          <TabNavigation
            tabs={THREADS_TABS}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            className="threads"
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
        <EmptyState message="포스트가 없습니다. 동기화 버튼을 클릭하여 Threads에서 포스트를 가져오세요." />
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
  );
}

// 포스트 작성 폼 컴포넌트
function PostComposeForm({ onSuccess }) {
  const [text, setText] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [posting, setPosting] = useState(false);

  const MAX_LENGTH = 500;
  const WARNING_THRESHOLD = 450;

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!text.trim() && !imageUrl.trim()) {
      alert('포스트 내용을 입력하거나 이미지 URL을 입력해주세요.');
      return;
    }

    if (text.length > MAX_LENGTH) {
      alert(`포스트는 ${MAX_LENGTH}자를 초과할 수 없습니다.`);
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
            maxLength={MAX_LENGTH}
            disabled={posting}
          />
          <CharCounter
            current={text.length}
            max={MAX_LENGTH}
            warningThreshold={WARNING_THRESHOLD}
          />
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
          <MediaPreview src={imageUrl} onRemove={() => setImageUrl('')} />
        )}

        <div className="compose-actions">
          <button
            type="submit"
            className="btn-post"
            disabled={posting || (!text.trim() && !imageUrl.trim())}
          >
            {posting ? '게시 중...' : '포스트하기'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default Threads;
