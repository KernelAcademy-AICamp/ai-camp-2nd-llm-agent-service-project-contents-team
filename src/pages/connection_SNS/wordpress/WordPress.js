import { useState, useEffect, useCallback } from 'react';
import { wordpressAPI } from '../../../services/api';
import { FaWordpress } from 'react-icons/fa6';
import {
  LoadingSpinner,
  ErrorMessage,
  PageHeader,
  AccountInfoCard,
  TabNavigation,
  EmptyState,
  SectionHeader,
  SyncButton,
  DisconnectButton
} from '../common/SNSComponents';
import { formatNumber, formatDate } from '../common/utils';
import '../common/SNSCommon.css';
import './WordPress.css';

// WordPress 탭 설정
const WORDPRESS_TABS = [
  { id: 'posts', label: '글 목록' },
  { id: 'stats', label: '통계' },
  { id: 'compose', label: '새 글 작성' }
];

// WordPress 연동 기능 목록
const WORDPRESS_FEATURES = [
  '글 목록 조회 및 관리',
  '새 글 작성 및 발행',
  '임시 저장 및 예약 발행',
  '카테고리 및 태그 관리',
  '미디어 업로드'
];

function WordPress() {
  const [connection, setConnection] = useState(null);
  const [posts, setPosts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState('posts');
  const [error, setError] = useState(null);

  // 글 목록 조회
  const fetchPosts = useCallback(async () => {
    try {
      const data = await wordpressAPI.getPosts(0, 50);
      setPosts(data || []);
    } catch (err) {
      console.error('Failed to fetch posts:', err);
    }
  }, []);

  // 카테고리 목록 조회
  const fetchCategories = useCallback(async () => {
    try {
      const data = await wordpressAPI.getCategories();
      setCategories(data || []);
    } catch (err) {
      console.error('Failed to fetch categories:', err);
    }
  }, []);

  // 연동 상태 확인
  const fetchStatus = useCallback(async () => {
    try {
      const data = await wordpressAPI.getStatus();
      setConnection(data);
      if (data) {
        fetchPosts();
        fetchCategories();
      }
    } catch (err) {
      console.error('Failed to fetch WordPress status:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchPosts, fetchCategories]);

  // 초기 로드
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // 연동 해제
  const handleDisconnect = async () => {
    if (!window.confirm('WordPress 연동을 해제하시겠습니까?')) return;
    try {
      await wordpressAPI.disconnect();
      setConnection(null);
      setPosts([]);
      setCategories([]);
    } catch (err) {
      setError('연동 해제에 실패했습니다.');
    }
  };

  // 글 동기화
  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await wordpressAPI.syncPosts();
      alert(`동기화 완료! ${result.synced_count || 0}개의 글을 가져왔습니다.`);
      fetchPosts();
      fetchStatus();
    } catch (err) {
      setError('동기화에 실패했습니다.');
    } finally {
      setSyncing(false);
    }
  };

  // 글 삭제
  const handleDeletePost = async (postId) => {
    if (!window.confirm('이 글을 삭제하시겠습니까?')) return;
    try {
      await wordpressAPI.deletePost(postId);
      fetchPosts();
    } catch (err) {
      setError('글 삭제에 실패했습니다.');
    }
  };

  if (loading) {
    return <LoadingSpinner className="wordpress" />;
  }

  // 계정 통계 데이터
  const accountStats = connection ? [
    { value: connection.total_posts || posts.length, label: '글' },
    { value: connection.total_pages || 0, label: '페이지' },
    { value: connection.total_comments || 0, label: '댓글' }
  ] : [];

  return (
    <div className="wordpress-page">
      <PageHeader
        title="WordPress 관리"
        description="WordPress 사이트를 연동하고 글을 관리하세요"
      />

      <ErrorMessage error={error} onClose={() => setError(null)} />

      {!connection ? (
        <WordPressConnectForm onConnect={fetchStatus} onError={setError} />
      ) : (
        <>
          <AccountInfoCard
            thumbnailUrl={connection.site_icon_url}
            name={connection.site_name || connection.site_url}
            subInfo={
              <a
                href={connection.site_url}
                target="_blank"
                rel="noopener noreferrer"
                className="account-url"
              >
                {connection.site_url}
              </a>
            }
            bio={connection.site_description}
            stats={accountStats}
            actions={
              <>
                <SyncButton syncing={syncing} onClick={handleSync} label="글 동기화" />
                <DisconnectButton onClick={handleDisconnect} />
              </>
            }
          />

          <TabNavigation
            tabs={WORDPRESS_TABS}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            className="wordpress"
          />

          <div className="tab-content">
            {activeTab === 'posts' && (
              <PostsTab posts={posts} onDelete={handleDeletePost} />
            )}

            {activeTab === 'stats' && (
              <StatsTab />
            )}

            {activeTab === 'compose' && (
              <PostComposeForm
                categories={categories}
                onSuccess={() => {
                  fetchPosts();
                  setActiveTab('posts');
                }}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}

// WordPress 연동 폼
function WordPressConnectForm({ onConnect, onError }) {
  const [siteUrl, setSiteUrl] = useState('');
  const [username, setUsername] = useState('');
  const [appPassword, setAppPassword] = useState('');
  const [connecting, setConnecting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!siteUrl.trim() || !username.trim() || !appPassword.trim()) {
      onError('모든 필드를 입력해주세요.');
      return;
    }

    setConnecting(true);
    try {
      await wordpressAPI.connect({
        site_url: siteUrl.trim(),
        username: username.trim(),
        app_password: appPassword.trim()
      });
      // 연동 성공 시 페이지 새로고침하여 사이드바 업데이트
      window.location.reload();
    } catch (err) {
      console.error('Connection failed:', err);
      const errorMessage = err.response?.data?.detail || '연동에 실패했습니다. 사이트 URL, 사용자명, 애플리케이션 비밀번호를 확인해주세요.';
      onError(errorMessage);
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="connect-card">
      <div className="connect-icon wordpress">
        <FaWordpress size={64} />
      </div>
      <h2>WordPress 사이트 연동</h2>
      <p className="connect-description">
        WordPress 사이트를 연동하여 글을 관리하고 콘텐츠를 발행하세요.
      </p>

      <div className="connect-features">
        <h4>연동 시 가능한 기능</h4>
        <ul>
          {WORDPRESS_FEATURES.map((feature, idx) => (
            <li key={idx}>{feature}</li>
          ))}
        </ul>
      </div>

      <form onSubmit={handleSubmit} className="connect-form">
        <div className="form-group">
          <label>WordPress 사이트 URL *</label>
          <input
            type="url"
            value={siteUrl}
            onChange={(e) => setSiteUrl(e.target.value)}
            placeholder="https://your-site.com"
            required
            disabled={connecting}
          />
        </div>

        <div className="form-group">
          <label>사용자명 *</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="WordPress 사용자명"
            required
            disabled={connecting}
          />
        </div>

        <div className="form-group">
          <label>애플리케이션 비밀번호 *</label>
          <input
            type="password"
            value={appPassword}
            onChange={(e) => setAppPassword(e.target.value)}
            placeholder="WordPress 애플리케이션 비밀번호"
            required
            disabled={connecting}
          />
          <small className="form-help">
            WordPress 관리자 &gt; 사용자 &gt; 프로필 &gt; 애플리케이션 비밀번호에서 생성할 수 있습니다.
          </small>
        </div>

        <button
          type="submit"
          className="btn-connect-wordpress"
          disabled={connecting}
        >
          <FaWordpress size={20} />
          {connecting ? '연동 중...' : 'WordPress 연동하기'}
        </button>
      </form>
    </div>
  );
}

// 통계 탭 컴포넌트
function StatsTab() {
  const [statsAvailable, setStatsAvailable] = useState(null);
  const [statsType, setStatsType] = useState(null);
  const [stats, setStats] = useState(null);
  const [topPosts, setTopPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('week');
  const [error, setError] = useState(null);

  // 통계 가용 여부 확인 및 데이터 로드
  useEffect(() => {
    const loadStats = async () => {
      setLoading(true);
      setError(null);

      try {
        // 먼저 통계 API 가용 여부 확인
        const availability = await wordpressAPI.checkStatsAvailability();
        setStatsAvailable(availability.stats_available);
        setStatsType(availability.stats_type);

        if (availability.stats_available) {
          // 통계 데이터 로드
          const [statsData, postsData] = await Promise.all([
            wordpressAPI.getStats(period),
            wordpressAPI.getPostStats(10)
          ]);

          setStats(statsData);
          if (postsData.top_posts) {
            setTopPosts(postsData.top_posts);
          }
        } else {
          setError(availability.error);
        }
      } catch (err) {
        console.error('Failed to load stats:', err);
        setError('통계 데이터를 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, [period]);

  // 기간 변경 핸들러
  const handlePeriodChange = (newPeriod) => {
    setPeriod(newPeriod);
  };

  if (loading) {
    return (
      <div className="stats-section">
        <div className="stats-loading">
          <div className="spinner"></div>
          <p>통계 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (!statsAvailable) {
    return (
      <div className="stats-section">
        <div className="stats-unavailable">
          <h3>📊 통계 기능 사용 불가</h3>
          <p>{error || '통계 플러그인이 설치되어 있지 않습니다.'}</p>
          <div className="stats-help">
            <h4>통계 기능을 사용하려면:</h4>
            <ul>
              <li>
                <strong>Jetpack</strong> 플러그인을 설치하고 활성화하세요.
                <br />
                <small>WordPress.com 계정과 연결이 필요합니다.</small>
              </li>
              <li>
                또는 <strong>WP Statistics</strong> 플러그인을 설치하세요.
                <br />
                <small>무료이며 별도의 계정 연결이 필요하지 않습니다.</small>
              </li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="stats-section">
      <div className="stats-header">
        <h3>📊 사이트 통계</h3>
        <div className="stats-period-selector">
          {[
            { value: 'day', label: '오늘' },
            { value: 'week', label: '이번 주' },
            { value: 'month', label: '이번 달' },
            { value: 'year', label: '올해' }
          ].map((p) => (
            <button
              key={p.value}
              className={`period-btn ${period === p.value ? 'active' : ''}`}
              onClick={() => handlePeriodChange(p.value)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {stats?.summary && (
        <div className="stats-summary">
          <div className="stat-card">
            <span className="stat-icon">👁️</span>
            <span className="stat-value">{formatNumber(stats.summary.views || 0)}</span>
            <span className="stat-label">조회수</span>
          </div>
          <div className="stat-card">
            <span className="stat-icon">👤</span>
            <span className="stat-value">{formatNumber(stats.summary.visitors || 0)}</span>
            <span className="stat-label">방문자</span>
          </div>
          <div className="stat-card">
            <span className="stat-icon">❤️</span>
            <span className="stat-value">{formatNumber(stats.summary.likes || 0)}</span>
            <span className="stat-label">좋아요</span>
          </div>
          <div className="stat-card">
            <span className="stat-icon">💬</span>
            <span className="stat-value">{formatNumber(stats.summary.comments || 0)}</span>
            <span className="stat-label">댓글</span>
          </div>
        </div>
      )}

      {stats?.source && (
        <p className="stats-source">
          데이터 출처: {stats.source === 'jetpack' ? 'Jetpack' : stats.source === 'wp_statistics' ? 'WP Statistics' : stats.source}
        </p>
      )}

      {topPosts.length > 0 && (
        <div className="top-posts-section">
          <h4>🏆 인기 게시물</h4>
          <div className="top-posts-list">
            {topPosts.map((post, index) => (
              <div key={post.id || index} className="top-post-item">
                <span className="top-post-rank">#{index + 1}</span>
                <div className="top-post-info">
                  <span className="top-post-title">{post.title}</span>
                  <span className="top-post-views">👁️ {formatNumber(post.views || post.view_count || 0)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {stats?.error && (
        <div className="stats-error">
          <p>{stats.error}</p>
        </div>
      )}
    </div>
  );
}

// 글 목록 탭 컴포넌트
function PostsTab({ posts, onDelete }) {
  return (
    <div className="posts-section">
      <SectionHeader title="내 글" count={posts.length} />
      {posts.length === 0 ? (
        <EmptyState message="글이 없습니다. 동기화 버튼을 클릭하여 WordPress에서 글을 가져오거나 새 글을 작성하세요." />
      ) : (
        <div className="post-list">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} onDelete={onDelete} />
          ))}
        </div>
      )}
    </div>
  );
}

// 글 카드 컴포넌트
function PostCard({ post, onDelete }) {
  const statusLabels = {
    publish: '발행됨',
    draft: '임시저장',
    pending: '검토 대기',
    private: '비공개',
    future: '예약됨'
  };

  return (
    <div className="post-card">
      <div className="post-header">
        <span className={`post-status status-${post.status}`}>
          {statusLabels[post.status] || post.status}
        </span>
        {post.categories && post.categories.length > 0 && (
          <span className="post-categories">
            {post.categories.slice(0, 2).join(', ')}
          </span>
        )}
      </div>
      <h3 className="post-title">{post.title || '제목 없음'}</h3>
      {post.excerpt && (
        <p className="post-excerpt">{post.excerpt}</p>
      )}
      <div className="post-meta">
        <span className="post-date">{formatDate(post.created_at || post.wp_created_at)}</span>
        {post.view_count > 0 && (
          <span className="post-views">👁️ {formatNumber(post.view_count)}</span>
        )}
        {post.comment_count > 0 && (
          <span className="post-comments">💬 {formatNumber(post.comment_count)}</span>
        )}
      </div>
      <div className="post-actions">
        {post.url && (
          <a
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-view"
          >
            보기
          </a>
        )}
        <button
          className="btn-delete"
          onClick={() => onDelete(post.id)}
        >
          삭제
        </button>
      </div>
    </div>
  );
}

// 글 작성 폼 컴포넌트
function PostComposeForm({ categories, onSuccess }) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [tags, setTags] = useState('');
  const [status, setStatus] = useState('draft');
  const [posting, setPosting] = useState(false);

  const handleCategoryChange = (categoryId) => {
    setSelectedCategories(prev =>
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!title.trim()) {
      alert('제목을 입력해주세요.');
      return;
    }

    if (!content.trim()) {
      alert('내용을 입력해주세요.');
      return;
    }

    setPosting(true);

    try {
      await wordpressAPI.createPost({
        title: title.trim(),
        content: content.trim(),
        status,
        categories: selectedCategories,
        tags: tags.split(',').map(t => t.trim()).filter(t => t)
      });

      const statusMessages = {
        publish: '글이 발행되었습니다!',
        draft: '임시 저장되었습니다!',
        pending: '검토 대기 상태로 저장되었습니다!',
        private: '비공개 글로 발행되었습니다!'
      };

      alert(statusMessages[status] || '글이 저장되었습니다!');
      setTitle('');
      setContent('');
      setSelectedCategories([]);
      setTags('');
      setStatus('draft');
      onSuccess();
    } catch (err) {
      console.error('Post failed:', err);
      alert('글 저장에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="compose-section">
      <h3>새 글 작성</h3>
      <form onSubmit={handleSubmit} className="compose-form">
        <div className="form-group">
          <label>제목 *</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="글 제목을 입력하세요"
            required
            disabled={posting}
          />
        </div>

        <div className="form-group">
          <label>내용 *</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="글 내용을 입력하세요 (HTML 지원)"
            rows={12}
            required
            disabled={posting}
          />
        </div>

        {categories.length > 0 && (
          <div className="form-group">
            <label>카테고리</label>
            <div className="category-list">
              {categories.map((cat) => (
                <label key={cat.id} className="category-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedCategories.includes(cat.id)}
                    onChange={() => handleCategoryChange(cat.id)}
                    disabled={posting}
                  />
                  {cat.name}
                </label>
              ))}
            </div>
          </div>
        )}

        <div className="form-group">
          <label>태그 (쉼표로 구분)</label>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="태그1, 태그2, 태그3"
            disabled={posting}
          />
        </div>

        <div className="form-group">
          <label>상태</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            disabled={posting}
          >
            <option value="draft">임시 저장</option>
            <option value="publish">즉시 발행</option>
            <option value="pending">검토 대기</option>
            <option value="private">비공개</option>
          </select>
        </div>

        <div className="compose-actions">
          <button
            type="submit"
            className="btn-publish"
            disabled={posting || !title.trim() || !content.trim()}
          >
            {posting ? '저장 중...' : status === 'publish' ? '발행하기' : '저장하기'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default WordPress;
