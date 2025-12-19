import { useState, useEffect, useCallback } from 'react';
import { instagramAPI } from '../../../services/api';
import { useAuth } from '../../../contexts/AuthContext';
import { FaInstagram } from 'react-icons/fa6';
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
import './Instagram.css';

// Instagram 탭 설정
const INSTAGRAM_TABS = [
  { id: 'posts', label: '게시물' },
  { id: 'insights', label: '인사이트' }
];

// Instagram 연동 기능 목록
const INSTAGRAM_FEATURES = [
  '게시물 목록 조회 및 관리',
  '좋아요, 댓글 등 통계 확인',
  '계정 인사이트 분석',
  '새 게시물 발행'
];

// Instagram 연동 요구사항
const INSTAGRAM_REQUIREMENTS = {
  title: '연동 요구사항:',
  items: [
    'Instagram 비즈니스 또는 크리에이터 계정',
    'Facebook 페이지와 연결된 계정'
  ]
};

function Instagram() {
  const { user } = useAuth();
  const [connection, setConnection] = useState(null);
  const [posts, setPosts] = useState([]);
  const [insights, setInsights] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState('posts');
  const [error, setError] = useState(null);
  const [showAccountSelector, setShowAccountSelector] = useState(false);

  // URL 파라미터 확인 (연동 성공/실패)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('connected') === 'true') {
      setError(null);
      // 연동 성공 시 페이지 새로고침하여 사이드바 업데이트
      window.location.replace('/instagram');
      return;
    }
    if (params.get('error')) {
      const errorType = params.get('error');
      const errorMessages = {
        no_pages: '연결된 Facebook 페이지가 없습니다. 먼저 Facebook 페이지를 생성하세요.',
        no_instagram_account: 'Facebook 페이지에 연결된 Instagram 비즈니스 계정이 없습니다.'
      };
      setError(errorMessages[errorType] || 'Instagram 연동에 실패했습니다. 다시 시도해주세요.');
      window.history.replaceState({}, '', '/instagram');
    }
  }, []);

  // 연결 가능한 Instagram 계정 목록 조회
  const fetchAccounts = useCallback(async () => {
    try {
      const data = await instagramAPI.getAccounts();
      setAccounts(data || []);
    } catch (err) {
      console.error('Failed to fetch accounts:', err);
    }
  }, []);

  // 게시물 목록 조회
  const fetchPosts = useCallback(async () => {
    try {
      const data = await instagramAPI.getPosts(0, 50);
      setPosts(data || []);
    } catch (err) {
      console.error('Failed to fetch posts:', err);
    }
  }, []);

  // 인사이트 조회
  const fetchInsights = useCallback(async () => {
    try {
      const data = await instagramAPI.getInsights();
      setInsights(data);
    } catch (err) {
      console.error('Failed to fetch insights:', err);
    }
  }, []);

  // 연동 상태 확인
  const fetchStatus = useCallback(async () => {
    try {
      const data = await instagramAPI.getStatus();
      setConnection(data);
      if (data) {
        if (data.instagram_account_id) {
          fetchPosts();
          fetchInsights();
        } else {
          fetchAccounts();
          setShowAccountSelector(true);
        }
      }
    } catch (err) {
      console.error('Failed to fetch Instagram status:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchAccounts, fetchPosts, fetchInsights]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Instagram 연동 시작
  const handleConnect = () => {
    if (!user?.id) {
      setError('로그인이 필요합니다.');
      return;
    }
    window.location.href = `${API_URL}/api/instagram/connect?user_id=${user.id}`;
  };

  // 연동 해제
  const handleDisconnect = async () => {
    if (!window.confirm('Instagram 연동을 해제하시겠습니까?')) return;
    try {
      await instagramAPI.disconnect();
      setConnection(null);
      setPosts([]);
      setInsights(null);
      setAccounts([]);
    } catch (err) {
      setError('연동 해제에 실패했습니다.');
    }
  };

  // 계정 선택
  const handleSelectAccount = async (instagramUserId) => {
    try {
      await instagramAPI.selectAccount(instagramUserId);
      setShowAccountSelector(false);
      fetchStatus();
    } catch (err) {
      setError('계정 선택에 실패했습니다.');
    }
  };

  // 게시물 동기화
  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await instagramAPI.syncPosts();
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
    return <LoadingSpinner className="instagram" />;
  }

  // 계정 통계 데이터
  const accountStats = connection ? [
    { value: connection.followers_count, label: '팔로워' },
    { value: connection.follows_count, label: '팔로잉' },
    { value: connection.media_count, label: '게시물' }
  ] : [];

  return (
    <div className="instagram-page">
      <PageHeader
        title="Instagram 관리"
        description="Instagram 비즈니스 계정을 연동하고 콘텐츠를 관리하세요"
      />

      <ErrorMessage error={error} onClose={() => setError(null)} />

      {!connection ? (
        <ConnectCard
          icon={<FaInstagram size={64} />}
          title="Instagram 비즈니스 계정 연동"
          description="Instagram 비즈니스 계정을 연동하여 게시물을 관리하고 인사이트를 확인하세요."
          features={INSTAGRAM_FEATURES}
          notice={INSTAGRAM_REQUIREMENTS}
          button={
            <button className="btn-connect-instagram" onClick={handleConnect}>
              <FaInstagram size={20} />
              Instagram 계정 연동하기
            </button>
          }
        />
      ) : showAccountSelector ? (
        <AccountSelector
          accounts={accounts}
          onSelect={handleSelectAccount}
          onDisconnect={handleDisconnect}
        />
      ) : (
        <>
          <AccountInfoCard
            thumbnailUrl={connection.instagram_profile_picture_url}
            name={`@${connection.instagram_username}`}
            subInfo={
              connection.instagram_name && (
                <span className="account-name">{connection.instagram_name}</span>
              )
            }
            bio={connection.instagram_biography}
            stats={accountStats}
            actions={
              <>
                <SyncButton syncing={syncing} onClick={handleSync} label="게시물 동기화" />
                <ChangeButton onClick={() => setShowAccountSelector(true)} label="계정 변경" />
                <DisconnectButton onClick={handleDisconnect} />
              </>
            }
          />

          <TabNavigation
            tabs={INSTAGRAM_TABS}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            className="instagram"
          />

          <div className="tab-content">
            {activeTab === 'posts' && (
              <PostsTab posts={posts} />
            )}

            {activeTab === 'insights' && (
              <InsightsTab insights={insights} />
            )}
          </div>
        </>
      )}
    </div>
  );
}

// 계정 선택 컴포넌트
function AccountSelector({ accounts, onSelect, onDisconnect }) {
  return (
    <SelectorCard
      title="Instagram 계정 선택"
      description="연동할 Instagram 비즈니스 계정을 선택해주세요."
      emptyMessage={
        <>
          <p>연결된 Instagram 비즈니스 계정이 없습니다.</p>
          <p>Instagram에서 비즈니스 계정으로 전환하고 Facebook 페이지와 연결해주세요.</p>
        </>
      }
      items={accounts}
      renderItem={(account) => (
        <div
          key={account.id}
          className="account-item"
          onClick={() => onSelect(account.id)}
        >
          <img
            src={account.profile_picture_url || '/default-avatar.png'}
            alt={account.username}
            className="account-picture"
          />
          <div className="account-info">
            <h4>@{account.username}</h4>
            <p>{account.name}</p>
            <div className="account-stats">
              <span>{formatNumber(account.followers_count)} 팔로워</span>
              <span>{formatNumber(account.media_count)} 게시물</span>
            </div>
            <p className="linked-page">연결된 페이지: {account.facebook_page_name}</p>
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
      <SectionHeader title="게시물" count={posts.length} />
      {posts.length === 0 ? (
        <EmptyState message="게시물이 없습니다. 동기화 버튼을 클릭하여 Instagram에서 게시물을 가져오세요." />
      ) : (
        <div className="post-grid">
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
  const mediaTypeBadges = {
    VIDEO: '동영상',
    CAROUSEL_ALBUM: '캐러셀'
  };

  return (
    <div className="post-card">
      <div className="post-image">
        <img
          src={post.media_type === 'VIDEO' ? (post.thumbnail_url || post.media_url) : post.media_url}
          alt=""
        />
        {mediaTypeBadges[post.media_type] && (
          <span className="media-type-badge">{mediaTypeBadges[post.media_type]}</span>
        )}
      </div>
      <div className="post-content">
        <p className="post-caption">
          {post.caption
            ? post.caption.substring(0, 100) + (post.caption.length > 100 ? '...' : '')
            : '(캡션 없음)'}
        </p>
        <div className="post-stats">
          <span>❤️ {formatNumber(post.like_count)}</span>
          <span>💬 {formatNumber(post.comments_count)}</span>
        </div>
        <div className="post-date">{formatDateSimple(post.timestamp)}</div>
      </div>
      {post.permalink && (
        <a
          href={post.permalink}
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
      <h3>계정 인사이트</h3>
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
        <EmptyState message={
          <>
            <p>인사이트 데이터를 가져올 수 없습니다.</p>
            <p>비즈니스 계정에서만 인사이트를 확인할 수 있습니다.</p>
          </>
        } />
      )}
    </div>
  );
}

export default Instagram;
