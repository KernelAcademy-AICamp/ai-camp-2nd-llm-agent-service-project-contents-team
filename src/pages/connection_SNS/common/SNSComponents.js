import React from 'react';
import { formatNumber } from './utils';

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
