import React from 'react';
import { formatNumber, formatDate, formatDuration } from './utils';

// 로딩 스피너
export const LoadingSpinner = ({ className = '' }) => (
  <div className={`${className}-page`}>
    <div className="loading-spinner">로딩 중...</div>
  </div>
);

// 에러 메시지
export const ErrorMessage = ({ error, onClose }) => {
  if (!error) return null;
  return (
    <div className="error-message">
      {error}
      <button onClick={onClose}>닫기</button>
    </div>
  );
};

// 페이지 헤더
export const PageHeader = ({ title, description }) => (
  <div className="sns-header">
    <h2>{title}</h2>
    <p>{description}</p>
  </div>
);

// 연동 카드 (미연동 상태)
export const ConnectCard = ({ icon, title, description, features, button, notice }) => (
  <div className="connect-section">
    <div className="connect-card">
      <div className="connect-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{description}</p>
      <ul className="feature-list">
        {features.map((feature, idx) => (
          <li key={idx}>{feature}</li>
        ))}
      </ul>
      {notice && (
        <div className="requirement-notice">
          <strong>{notice.title}</strong>
          <ul>
            {notice.items.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>
      )}
      {button}
    </div>
  </div>
);

// 계정 정보 카드
export const AccountInfoCard = ({
  thumbnailUrl,
  name,
  subInfo,
  bio,
  stats,
  actions
}) => (
  <div className="account-info-card">
    <div className="account-header">
      <img
        src={thumbnailUrl || '/default-avatar.png'}
        alt={name}
        className="account-thumbnail"
      />
      <div className="account-details">
        <h3>{name}</h3>
        {subInfo}
        {bio && <p className="account-bio">{bio}</p>}
      </div>
      <div className="account-actions">
        {actions}
      </div>
    </div>
    <div className="account-stats-bar">
      {stats.map((stat, idx) => (
        <div key={idx} className="stat-item">
          <span className="stat-value">{formatNumber(stat.value)}</span>
          <span className="stat-label">{stat.label}</span>
        </div>
      ))}
    </div>
  </div>
);

// 탭 네비게이션
export const TabNavigation = ({ tabs, activeTab, onTabChange, className = '' }) => (
  <div className={`${className}-tabs sns-tabs`}>
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
        onClick={() => onTabChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </div>
);

// 빈 상태 표시
export const EmptyState = ({ message, action }) => (
  <div className="empty-state">
    <p>{message}</p>
    {action}
  </div>
);

// 섹션 헤더
export const SectionHeader = ({ title, count }) => (
  <div className="section-header">
    <h3>{title} {count !== undefined && `(${count}개)`}</h3>
  </div>
);

// 포스트 통계
export const PostStats = ({ stats }) => (
  <div className="post-stats">
    {stats.map((stat, idx) => (
      <span key={idx}>{stat.icon} {formatNumber(stat.value)}</span>
    ))}
  </div>
);

// 버튼 컴포넌트들
export const SyncButton = ({ syncing, onClick, label = '동기화' }) => (
  <button className="btn-secondary" onClick={onClick} disabled={syncing}>
    {syncing ? '동기화 중...' : label}
  </button>
);

export const DisconnectButton = ({ onClick }) => (
  <button className="btn-danger" onClick={onClick}>
    연동 해제
  </button>
);

export const ChangeButton = ({ onClick, label }) => (
  <button className="btn-secondary" onClick={onClick}>
    {label}
  </button>
);

// 선택자 카드 (페이지/계정 선택)
export const SelectorCard = ({
  title,
  description,
  emptyMessage,
  items,
  renderItem,
  onDisconnect
}) => (
  <div className="selector-section">
    <div className="selector-card">
      <h3>{title}</h3>
      <p>{description}</p>
      {items.length === 0 ? (
        <div className="no-items">
          {emptyMessage}
        </div>
      ) : (
        <div className="item-list">
          {items.map(renderItem)}
        </div>
      )}
      <button className="btn-secondary" onClick={onDisconnect}>
        연동 해제
      </button>
    </div>
  </div>
);

// 포스트 작성 폼 기본 구조
export const ComposeFormLayout = ({ title, children, onSubmit }) => (
  <div className="compose-section">
    <h3>{title}</h3>
    <form onSubmit={onSubmit} className="compose-form">
      {children}
    </form>
  </div>
);

// 글자 수 카운터
export const CharCounter = ({ current, max, warningThreshold }) => (
  <div className="char-count">
    <span className={current > warningThreshold ? 'warning' : ''}>
      {current}/{max}
    </span>
  </div>
);

// 미디어 미리보기
export const MediaPreview = ({ src, onRemove, type = 'image' }) => (
  <div className="media-preview">
    {type === 'video' ? (
      <video src={src} controls />
    ) : (
      <img src={src} alt="Preview" onError={(e) => e.target.style.display = 'none'} />
    )}
    {onRemove && (
      <button type="button" className="remove-media" onClick={onRemove}>
        ✕
      </button>
    )}
  </div>
);

// ===== 플랫폼별 아이콘 컴포넌트 =====

// Threads 아이콘
const THREADS_ICON_PATH = "M141.537 88.9883C140.71 88.5919 139.87 88.2104 139.019 87.8451C137.537 60.5382 122.616 44.905 97.5619 44.745C97.4484 44.7443 97.3355 44.7443 97.222 44.7443C82.2364 44.7443 69.7731 51.1409 62.102 62.7807L75.881 72.2328C81.6116 63.5383 90.6052 61.6848 97.2266 61.6848C97.3051 61.6848 97.3827 61.6848 97.4594 61.6855C105.707 61.7381 111.932 64.1366 115.961 68.814C118.893 72.2193 120.854 76.925 121.825 82.8638C114.511 81.6207 106.601 81.2385 98.145 81.7233C74.3247 83.0954 59.0111 96.9879 60.0396 116.292C60.5615 126.084 65.4397 134.508 73.775 140.011C80.8224 144.663 89.899 146.938 99.3323 146.423C111.79 145.74 121.563 140.987 128.381 132.296C133.559 125.696 136.834 117.143 138.28 106.366C144.217 109.949 148.617 114.664 151.047 120.332C155.179 129.967 155.42 145.8 142.501 158.708C131.182 170.016 117.576 174.908 97.0135 175.059C74.2042 174.89 56.9538 167.575 45.7381 153.317C35.2355 139.966 29.8077 120.682 29.6052 96C29.8077 71.3175 35.2355 52.0337 45.7381 38.6827C56.9538 24.4249 74.2039 17.11 97.0132 16.9405C120.038 17.1113 137.536 24.4614 148.955 38.788C154.359 45.5687 158.402 53.8915 160.989 63.4962L176.96 59.6267C173.59 46.9666 168.25 36.1558 160.855 27.3569C146.115 9.61287 124.739 0.270049 97.0695 0.00146779C97.0426 0.001375 97.0159 0.00128174 96.9892 0.00128174C96.9614 0.00128174 96.9342 0.001375 96.9065 0.00146779C69.2347 0.270049 47.8581 9.61287 33.1182 27.3569C16.5697 48.3197 13.0458 71.6709 12.6655 96C13.0458 120.329 16.5697 143.68 33.1182 164.643C47.8581 182.387 69.2344 191.73 96.9065 191.999C96.9336 191.999 96.9614 191.999 96.9892 191.999C97.0159 191.999 97.0426 191.999 97.0695 191.999C124.695 191.731 146.023 182.386 160.855 164.643C180.362 140.992 179.938 110.571 169.286 94.0256C162.361 83.1122 150.883 74.7974 136.063 69.4857C136.683 75.6754 136.907 82.3196 136.644 89.3784C136.62 89.9666 136.583 90.5481 136.54 91.1236C137.593 91.5793 138.619 92.0609 139.614 92.5674C153.058 99.5416 161.09 109.995 162.105 122.266C163.133 134.702 157.016 146.606 145.161 153.885C135.088 159.955 121.39 163.06 105.099 162.863C93.2296 162.711 83.5974 159.714 77.0641 154.157C70.934 148.948 67.6479 141.631 67.3282 132.663C66.808 118.697 77.5965 107.861 95.6624 106.755C100.997 106.444 106.058 106.439 110.839 106.721C116.288 106.979 121.388 107.553 126.104 108.415C126.047 112.478 125.67 116.155 124.963 119.407C123.534 126.071 120.463 131.102 115.741 134.431C110.456 138.167 103.143 140.157 94.2509 140.402C88.4388 140.571 81.7814 139.344 76.2747 136.103C70.3506 132.616 66.9697 127.461 66.7063 121.032C66.2413 109.723 77.8048 100.468 95.0614 99.4978C102.169 99.0953 108.872 99.3934 115.033 100.391C115.003 100.133 114.976 99.8743 114.954 99.6146C114.627 95.7816 114.775 92.1063 115.402 88.6248C108.868 87.8135 101.943 87.5577 94.4795 87.9747C70.3699 89.4051 52.6773 105.013 53.6973 127.478C54.2084 137.903 59.2389 146.905 68.0619 152.914C77.0116 159.009 89.1052 161.829 102.629 161.429C118.785 160.965 133.054 156.639 143.836 148.831C155.954 139.994 162.587 127.274 161.544 113.36C160.671 101.698 154.232 92.0549 141.537 88.9883Z";

export const ThreadsIcon = ({ size = 64 }) => (
  <svg viewBox="0 0 192 192" width={size} height={size}>
    <path fill="currentColor" d={THREADS_ICON_PATH} />
  </svg>
);

// X 아이콘
const X_ICON_PATH = "M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z";

export const XIcon = ({ size = 64 }) => (
  <svg viewBox="0 0 24 24" width={size} height={size}>
    <path fill="currentColor" d={X_ICON_PATH} />
  </svg>
);

// ===== 공통 콘텐츠 카드 컴포넌트 =====

// 동영상 카드 (TikTok, YouTube용)
export const VideoCard = ({
  video,
  thumbnailKey = 'cover_image_url',
  titleKey = 'title',
  descriptionKey = 'description',
  durationKey = 'duration',
  statsConfig = [],
  linkUrl,
  linkText,
  placeholder
}) => (
  <div className="video-card">
    <div className="video-thumbnail">
      {video[thumbnailKey] ? (
        <img src={video[thumbnailKey]} alt={video[titleKey] || '동영상'} />
      ) : (
        <div className="video-placeholder">
          {placeholder}
        </div>
      )}
      {video[durationKey] && (
        <div className="video-duration">{formatDuration(video[durationKey])}</div>
      )}
    </div>
    <div className="video-info">
      <h4 className="video-title">{video[titleKey] || '제목 없음'}</h4>
      {video[descriptionKey] && (
        <p className="video-description">{video[descriptionKey]}</p>
      )}
      <div className="video-stats">
        {statsConfig.map((stat, idx) => (
          <span key={idx}>{stat.icon} {formatNumber(video[stat.key])}</span>
        ))}
      </div>
      <div className="video-footer">
        <span className="video-date">{formatDate(video.created_at)}</span>
        {linkUrl && (
          <a
            href={linkUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="view-on-platform"
          >
            {linkText}
          </a>
        )}
      </div>
    </div>
  </div>
);

// 포스트 카드 (Threads, X, Facebook용)
export const PostCard = ({
  post,
  textKey = 'text',
  mediaUrlKey = 'media_url',
  mediaTypeKey = 'media_type',
  statsConfig = [],
  dateKey = 'created_at',
  linkUrl,
  linkText
}) => (
  <div className="post-card">
    <div className="post-content">
      <p className="post-text">{post[textKey]}</p>
      {post[mediaUrlKey] && (
        <div className="post-media">
          {post[mediaTypeKey] === 'VIDEO' ? (
            <video src={post[mediaUrlKey]} controls />
          ) : (
            <img src={post[mediaUrlKey]} alt="Post media" />
          )}
        </div>
      )}
    </div>
    <div className="post-stats">
      {statsConfig.map((stat, idx) => (
        <span key={idx}>{stat.icon} {formatNumber(post[stat.key])}</span>
      ))}
    </div>
    <div className="post-footer">
      <span className="post-date">{formatDate(post[dateKey])}</span>
      {linkUrl && (
        <a
          href={linkUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="view-on-platform"
        >
          {linkText}
        </a>
      )}
    </div>
  </div>
);

// 콘텐츠 목록 탭 (동영상/포스트)
export const ContentListTab = ({
  items,
  sectionTitle,
  emptyMessage,
  gridClassName = 'post-list',
  renderItem
}) => (
  <div className="content-section">
    <SectionHeader title={sectionTitle} count={items.length} />
    {items.length === 0 ? (
      <EmptyState message={emptyMessage} />
    ) : (
      <div className={gridClassName}>
        {items.map(renderItem)}
      </div>
    )}
  </div>
);

// 업로드/작성 섹션 레이아웃
export const UploadSection = ({ title, notice, children }) => (
  <div className="upload-section">
    <h3>{title}</h3>
    {notice && <p className="upload-notice">{notice}</p>}
    {children}
  </div>
);

// 폼 그룹
export const FormGroup = ({ label, required, help, children }) => (
  <div className="form-group">
    {label && <label>{label}{required && ' *'}</label>}
    {children}
    {help && <small className="form-help">{help}</small>}
  </div>
);

// 제출 버튼
export const SubmitButton = ({ loading, disabled, loadingText, text, className = 'btn-post' }) => (
  <button
    type="submit"
    className={className}
    disabled={loading || disabled}
  >
    {loading ? loadingText : text}
  </button>
);
