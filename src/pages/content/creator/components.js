// 콘텐츠 생성기 공통 컴포넌트

import { FiCopy } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import { getScoreColor } from './utils';
import { PLATFORM_CONFIG } from './constants';

/**
 * 결과 카드 컴포넌트
 */
export const ResultCard = ({ title, children, onCopy, score }) => (
  <div className="creator-result-card">
    <div className="creator-result-card-header">
      <h3>
        {title}
        {score != null && (
          <span className="header-score" style={{ color: getScoreColor(score) }}>
            {score}점
          </span>
        )}
      </h3>
      {onCopy && (
        <button className="btn-icon" onClick={onCopy} title="복사">
          <FiCopy />
        </button>
      )}
    </div>
    <div className="creator-result-card-content">{children}</div>
  </div>
);

/**
 * 플랫폼별 콘텐츠 컴포넌트
 */
export const PlatformContent = ({ platform, data, onCopy, score }) => {
  if (!data) return null;

  const { title } = PLATFORM_CONFIG[platform];

  return (
    <ResultCard title={title} onCopy={onCopy} score={score}>
      {platform === 'blog' && <div className="creator-blog-title">{data.title}</div>}
      {platform === 'blog' ? (
        <div className="creator-text-result markdown-content">
          <ReactMarkdown remarkPlugins={[remarkBreaks]}>{data.content}</ReactMarkdown>
        </div>
      ) : (
        <div className="creator-text-result sns-content">
          {data.content}
        </div>
      )}
    </ResultCard>
  );
};

/**
 * 이미지 팝업 컴포넌트
 */
export const ImagePopup = ({ imageUrl, onClose }) => {
  if (!imageUrl) return null;

  return (
    <div className="image-popup-overlay" onClick={onClose}>
      <div className="image-popup-content" onClick={(e) => e.stopPropagation()}>
        <button className="image-popup-close" onClick={onClose}>✕</button>
        <img src={imageUrl} alt="확대 이미지" />
      </div>
    </div>
  );
};

/**
 * 콘텐츠 타입 선택 카드 컴포넌트
 */
export const ContentTypeCard = ({ type, isSelected, isDisabled, onClick }) => (
  <div
    className={`creator-type-card ${isSelected ? 'selected' : ''} ${isDisabled ? 'disabled' : ''}`}
    onClick={() => !isDisabled && onClick(type.id)}
  >
    {type.recommended && <span className="recommended-badge">추천</span>}
    {type.isNew && <span className="new-badge">NEW</span>}
    <span className="type-icon">{type.icon}</span>
    <span className="type-label">{type.label}</span>
    <span className="type-desc">{type.desc}</span>
  </div>
);

/**
 * 옵션 칩 버튼 컴포넌트
 */
export const OptionChip = ({ label, isSelected, isDisabled, onClick }) => (
  <button
    className={`creator-chip ${isSelected ? 'selected' : ''}`}
    onClick={onClick}
    disabled={isDisabled}
  >
    {label}
  </button>
);

/**
 * 빈 옵션 플레이스홀더 컴포넌트
 */
export const OptionsPlaceholder = () => (
  <div className="creator-options-placeholder">
    <span className="placeholder-icon">⚙️</span>
    <p>생성 타입을 선택하면<br />추가 옵션이 표시됩니다</p>
  </div>
);
