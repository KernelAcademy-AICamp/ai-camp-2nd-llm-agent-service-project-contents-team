import React, { useState } from 'react';
import './ContentCreator.css';

function ContentCreator() {
  const [contentType, setContentType] = useState('social');
  const [platform, setPlatform] = useState('instagram');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  const contentTypes = [
    { id: 'social', label: '소셜 미디어', icon: '📱' },
    { id: 'blog', label: '블로그 포스트', icon: '📝' },
    { id: 'video', label: '비디오 스크립트', icon: '🎥' },
    { id: 'email', label: '이메일', icon: '✉️' },
  ];

  const platforms = {
    social: ['Instagram', 'Facebook', 'Twitter', 'LinkedIn'],
    blog: ['WordPress', 'Naver Blog', 'Tistory', 'Medium'],
    video: ['YouTube', 'TikTok', 'Reels'],
    email: ['Newsletter', 'Promotion', 'Announcement'],
  };

  const handleGenerate = () => {
    // AI 콘텐츠 생성 로직 (추후 구현)
    alert('AI 콘텐츠 생성 기능은 추후 구현 예정입니다.');
  };

  const handleSave = () => {
    // 저장 로직 (추후 구현)
    alert('콘텐츠가 저장되었습니다.');
  };

  const handleSchedule = () => {
    // 스케줄 설정 로직 (추후 구현)
    alert('스케줄 설정 화면으로 이동합니다.');
  };

  return (
    <div className="content-creator">
      <div className="creator-header">
        <h2>콘텐츠 생성</h2>
        <div className="header-actions">
          <button className="btn-secondary" onClick={handleSave}>
            임시 저장
          </button>
          <button className="btn-primary" onClick={handleSchedule}>
            저장 및 예약
          </button>
        </div>
      </div>

      <div className="creator-content">
        <div className="creator-main">
          <div className="section">
            <h3>콘텐츠 유형</h3>
            <div className="content-type-grid">
              {contentTypes.map((type) => (
                <button
                  key={type.id}
                  className={`type-card ${contentType === type.id ? 'active' : ''}`}
                  onClick={() => setContentType(type.id)}
                >
                  <span className="type-icon">{type.icon}</span>
                  <span className="type-label">{type.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="section">
            <h3>플랫폼 선택</h3>
            <select
              className="platform-select"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
            >
              {platforms[contentType]?.map((p) => (
                <option key={p} value={p.toLowerCase()}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          <div className="section">
            <h3>제목</h3>
            <input
              type="text"
              className="title-input"
              placeholder="콘텐츠 제목을 입력하세요"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="section">
            <div className="section-header">
              <h3>내용</h3>
              <button className="btn-ai" onClick={handleGenerate}>
                ✨ AI로 생성하기
              </button>
            </div>
            <textarea
              className="content-textarea"
              placeholder="콘텐츠 내용을 입력하거나 AI로 생성하세요..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={12}
            />
          </div>

          <div className="section">
            <h3>이미지/미디어</h3>
            <div className="media-upload">
              <div className="upload-area">
                <span className="upload-icon">📷</span>
                <p>이미지를 드래그하거나 클릭하여 업로드</p>
                <button className="btn-upload">파일 선택</button>
              </div>
            </div>
          </div>
        </div>

        <div className="creator-sidebar">
          <div className="preview-section">
            <h3>미리보기</h3>
            <div className="preview-box">
              <div className="preview-platform">{platform}</div>
              <div className="preview-content">
                <h4>{title || '제목 미리보기'}</h4>
                <p>{content || '내용이 여기에 표시됩니다...'}</p>
              </div>
            </div>
          </div>

          <div className="tips-section">
            <h3>💡 작성 팁</h3>
            <ul className="tips-list">
              <li>명확하고 간결한 제목을 사용하세요</li>
              <li>타겟 고객을 고려한 톤을 유지하세요</li>
              <li>행동 유도 문구(CTA)를 포함하세요</li>
              <li>해시태그를 적절히 활용하세요</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ContentCreator;
