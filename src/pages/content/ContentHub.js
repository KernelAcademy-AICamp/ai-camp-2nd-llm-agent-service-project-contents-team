import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './ContentHub.css';

function ContentHub() {
  const navigate = useNavigate();
  const [inputText, setInputText] = useState('');

  // 샘플 콘텐츠 미리보기
  const samplePreviews = [
    {
      id: 1,
      type: 'blog',
      label: '블로그',
      title: '성수동 핫플 카페 투어 BEST 5',
      content: '요즘 성수동이 정말 핫하죠! 오늘은 제가 직접 다녀온 성수동 카페 중에서...',
      tags: ['#성수동카페', '#카페추천'],
    },
    {
      id: 2,
      type: 'instagram',
      label: 'Instagram',
      title: '',
      content: '성수동에서 발견한 숨은 보석 같은 카페 ☕✨\n빈티지 인테리어에 맛있는 커피까지!',
      tags: ['#성수카페', '#카페스타그램', '#서울카페'],
    },
    {
      id: 3,
      type: 'video',
      label: '숏폼 영상',
      title: '',
      content: '',
      isVideo: true,
    },
    {
      id: 4,
      type: 'image',
      label: 'AI 이미지',
      title: '자동 생성된 썸네일',
      content: '',
      isImage: true,
    },
  ];

  const handleGenerate = () => {
    navigate('/create', { state: { initialText: inputText } });
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleGenerate();
    }
  };

  return (
    <div className="content-hub">
      <div className="hub-container">
        {/* 왼쪽: 입력 섹션 */}
        <div className="hub-input-section">
          <h1 className="hub-title">
            <span className="title-highlight">AI</span>로 콘텐츠를
            <br />한번에 만들어보세요
          </h1>
          <p className="hub-subtitle">
            주제만 입력하면 블로그, SNS, 이미지까지 자동 생성
          </p>

          <div className="input-box">
            <textarea
              className="hub-textarea"
              placeholder="예: 성수동 카페 추천, 신메뉴 딸기라떼 출시, 홈카페 레시피..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={3}
            />
            <button className="generate-btn" onClick={handleGenerate}>
              AI 콘텐츠 생성
              <span className="btn-arrow">→</span>
            </button>
          </div>

          <div className="quick-options">
            <span className="quick-label">빠른 시작:</span>
            <button className="quick-chip" onClick={() => setInputText('신메뉴 출시 홍보')}>
              신메뉴 출시
            </button>
            <button className="quick-chip" onClick={() => setInputText('카페 방문 후기')}>
              카페 후기
            </button>
            <button className="quick-chip" onClick={() => setInputText('이벤트 공지')}>
              이벤트 공지
            </button>
          </div>

          <div className="other-options">
            <button className="option-btn" onClick={() => navigate('/ai-video')}>
              <span className="option-icon">🎬</span>
              AI 동영상 생성
            </button>
          </div>
        </div>

        {/* 오른쪽: 미리보기 섹션 */}
        <div className="hub-preview-section">
          <div className="preview-stack">
            {samplePreviews.map((item, index) => (
              <div
                key={item.id}
                className={`preview-card preview-${item.type}`}
                style={{ '--index': index }}
              >
                <div className="preview-card-header">
                  <span className={`preview-badge badge-${item.type}`}>
                    {item.label}
                  </span>
                </div>
                {item.isVideo ? (
                  <div className="preview-video-placeholder">
                    <div className="video-play-btn">▶</div>
                    <div className="video-progress">
                      <div className="video-progress-bar"></div>
                    </div>
                    <span className="video-duration">0:15</span>
                  </div>
                ) : item.isImage ? (
                  <div className="preview-image-placeholder">
                    <div className="image-icon">🖼️</div>
                    <span>AI 생성 이미지</span>
                  </div>
                ) : (
                  <div className="preview-card-body">
                    {item.title && <h4 className="preview-title">{item.title}</h4>}
                    <p className="preview-content">{item.content}</p>
                    {item.tags && (
                      <div className="preview-tags">
                        {item.tags.map((tag, i) => (
                          <span key={i} className="preview-tag">{tag}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
          <p className="preview-caption">하나의 입력으로 여러 플랫폼 콘텐츠 동시 생성</p>
        </div>
      </div>
    </div>
  );
}

export default ContentHub;
