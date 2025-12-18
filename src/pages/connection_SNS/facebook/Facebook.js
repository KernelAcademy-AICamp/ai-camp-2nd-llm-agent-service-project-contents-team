import { useState, useEffect, useCallback } from 'react';
import { facebookAPI } from '../../../services/api';
import { useAuth } from '../../../contexts/AuthContext';
import { FaFacebook } from 'react-icons/fa6';
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
  ChangeButton,
  SelectorCard
} from '../common/SNSComponents';
import { formatNumber, formatDateSimple, API_URL } from '../common/utils';
import '../common/SNSCommon.css';
import './Facebook.css';

// Facebook 탭 설정
const FACEBOOK_TABS = [
  { id: 'posts', label: '게시물' },
  { id: 'insights', label: '인사이트' },
  { id: 'create', label: '새 게시물' }
];

// Facebook 연동 기능 목록
const FACEBOOK_FEATURES = [
  '페이지 게시물 목록 조회 및 관리',
  '새 게시물 작성',
  '좋아요, 댓글, 공유 등 통계 확인',
  '페이지 인사이트 분석'
];

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
      // 연동 성공 시 페이지 새로고침하여 사이드바 업데이트
      window.location.replace('/facebook');
      return;
    }
    if (params.get('error')) {
      setError('Facebook 연동에 실패했습니다. 다시 시도해주세요.');
      window.history.replaceState({}, '', '/facebook');
    }
  }, []);

  // 관리하는 페이지 목록 조회
  const fetchPages = useCallback(async () => {
    try {
      const data = await facebookAPI.getPages();
      setPages(data || []);
    } catch (err) {
      console.error('Failed to fetch pages:', err);
    }
  }, []);

  // 게시물 목록 조회
  const fetchPosts = useCallback(async () => {
    try {
      const data = await facebookAPI.getPosts(0, 50);
      setPosts(data || []);
    } catch (err) {
      console.error('Failed to fetch posts:', err);
    }
  }, []);

  // 인사이트 조회
  const fetchInsights = useCallback(async () => {
    try {
      const data = await facebookAPI.getInsights();
      setInsights(data);
    } catch (err) {
      console.error('Failed to fetch insights:', err);
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
          fetchPages();
          setShowPageSelector(true);
        }
      }
    } catch (err) {
      console.error('Failed to fetch Facebook status:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchPages, fetchPosts, fetchInsights]);

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

  if (loading) {
    return <LoadingSpinner className="facebook" />;
  }

  // 페이지 통계 데이터
  const pageStats = connection ? [
    { value: connection.page_fan_count, label: '좋아요' },
    { value: connection.page_followers_count, label: '팔로워' },
    { value: posts.length, label: '게시물' }
  ] : [];

  return (
    <div className="facebook-page">
      <PageHeader
        title="Facebook 관리"
        description="Facebook 페이지를 연동하고 콘텐츠를 관리하세요"
      />

      <ErrorMessage error={error} onClose={() => setError(null)} />

      {!connection ? (
        <ConnectCard
          icon={<FaFacebook size={64} />}
          title="Facebook 페이지 연동"
          description="Facebook 페이지를 연동하여 게시물을 관리하고 인사이트를 확인하세요."
          features={FACEBOOK_FEATURES}
          button={
            <button className="btn-connect-facebook" onClick={handleConnect}>
              <FaFacebook size={20} />
              Facebook 페이지 연동하기
            </button>
          }
        />
      ) : showPageSelector ? (
        <PageSelector
          pages={pages}
          onSelect={handleSelectPage}
          onDisconnect={handleDisconnect}
        />
      ) : (
        <>
          <AccountInfoCard
            thumbnailUrl={connection.page_picture_url}
            name={connection.page_name}
            subInfo={
              connection.page_category && (
                <span className="account-category">{connection.page_category}</span>
              )
            }
            stats={pageStats}
            actions={
              <>
                <SyncButton syncing={syncing} onClick={handleSync} label="게시물 동기화" />
                <ChangeButton onClick={() => setShowPageSelector(true)} label="페이지 변경" />
                <DisconnectButton onClick={handleDisconnect} />
              </>
            }
          />

          <TabNavigation
            tabs={FACEBOOK_TABS}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            className="facebook"
          />

          <div className="tab-content">
            {activeTab === 'posts' && (
              <PostsTab posts={posts} />
            )}

            {activeTab === 'insights' && (
              <InsightsTab insights={insights} />
            )}

            {activeTab === 'create' && (
              <CreatePostTab />
            )}
          </div>
        </>
      )}
    </div>
  );
}

// 페이지 선택 컴포넌트
function PageSelector({ pages, onSelect, onDisconnect }) {
  return (
    <SelectorCard
      title="관리할 페이지 선택"
      description="연동할 Facebook 페이지를 선택해주세요."
      emptyMessage={
        <>
          <p>관리 중인 Facebook 페이지가 없습니다.</p>
          <p>먼저 Facebook에서 페이지를 생성해주세요.</p>
        </>
      }
      items={pages}
      renderItem={(page) => (
        <div
          key={page.id}
          className="page-item"
          onClick={() => onSelect(page.id)}
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
      )}
      onDisconnect={onDisconnect}
    />
  );
}

// 게시물 탭 컴포넌트
function PostsTab({ posts }) {
  return (
    <div className="posts-section">
      <SectionHeader title="페이지 게시물" count={posts.length} />
      {posts.length === 0 ? (
        <EmptyState message="게시물이 없습니다. 동기화 버튼을 클릭하여 Facebook에서 게시물을 가져오세요." />
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

// 게시물 카드 컴포넌트
function PostCard({ post }) {
  return (
    <div className="post-card">
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
        <div className="post-date">{formatDateSimple(post.created_time)}</div>
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
  );
}

// 인사이트 탭 컴포넌트
function InsightsTab({ insights }) {
  const hasData = insights?.data?.length > 0;

  return (
    <div className="insights-section">
      <h3>페이지 인사이트 (최근 30일)</h3>
      {hasData ? (
        <div className="insights-grid">
          {insights.data.map((metric, index) => (
            <div key={index} className="insight-card">
              <span className="insight-label">{metric.title || metric.name}</span>
              <span className="insight-value">
                {metric.values?.[0] ? formatNumber(metric.values[0].value) : 'N/A'}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState message="인사이트 데이터를 가져올 수 없습니다." />
      )}
    </div>
  );
}

// 새 게시물 탭 컴포넌트
function CreatePostTab() {
  return (
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
  );
}

export default Facebook;
