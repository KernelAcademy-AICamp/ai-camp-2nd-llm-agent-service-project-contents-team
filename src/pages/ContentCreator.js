import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './ContentCreator.css';

function ContentCreator() {
  const navigate = useNavigate();
  const [contentType, setContentType] = useState('social');
  const [platform, setPlatform] = useState('instagram');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [aiModel, setAiModel] = useState('nanovana');
  const [imagePrompt, setImagePrompt] = useState('');
  const [generatedImage, setGeneratedImage] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const contentTypes = [
    { id: 'social', label: '소셜 미디어', icon: '📱' },
    { id: 'blog', label: '블로그 포스트', icon: '📝' },
    { id: 'video', label: '비디오 스크립트', icon: '🎥' },
    { id: 'email', label: '이메일', icon: '✉️' },
    { id: 'image', label: '이미지 생성', icon: '🎨' },
    { id: 'cardnews', label: '카드뉴스', icon: '📰' },
  ];

  const platforms = {
    social: ['Instagram', 'Facebook', 'Twitter', 'LinkedIn'],
    blog: ['WordPress', 'Naver Blog', 'Tistory', 'Medium'],
    video: ['YouTube', 'TikTok', 'Reels'],
    email: ['Newsletter', 'Promotion', 'Announcement'],
    image: ['Instagram', 'Pinterest', 'Blog', 'Social Media'],
    cardnews: ['Instagram', 'Facebook', 'Blog', 'Social Media'],
  };

  const aiModels = [
    { id: 'nanovana', label: '나노바나나 (Nanovana)', provider: 'Anthropic' },
    { id: 'gemini', label: '제미나이 (Gemini)', provider: 'Google' },
  ];

  // 카드뉴스 선택 시 /cardnews로 이동
  useEffect(() => {
    if (contentType === 'cardnews') {
      navigate('/cardnews');
    }
  }, [contentType, navigate]);

  const handleGenerateImage = async () => {
    if (!imagePrompt.trim()) {
      alert('이미지 생성을 위한 프롬프트를 입력해주세요.');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await fetch('/api/generate-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: imagePrompt,
          model: aiModel,
        }),
      });

      // 응답 텍스트 먼저 확인
      const responseText = await response.text();

      if (!response.ok) {
        let errorMessage = '이미지 생성에 실패했습니다.';
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.error || errorMessage;
        } catch (e) {
          // JSON 파싱 실패 시 원본 텍스트 사용
          errorMessage = responseText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      // 성공 응답 파싱
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (e) {
        throw new Error('서버 응답을 파싱할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.');
      }

      if (!data.imageUrl) {
        throw new Error('이미지 URL을 받지 못했습니다.');
      }

      setGeneratedImage(data.imageUrl);

      // Claude로 프롬프트가 최적화되었는지 확인
      let successMessage = '이미지가 성공적으로 생성되었습니다!';
      if (data.usedClaudeOptimization && data.optimizedPrompt) {
        successMessage += `\n\n🤖 나노바나나(Claude)가 프롬프트를 최적화했습니다:\n"${data.optimizedPrompt}"`;
      }

      alert(successMessage);
    } catch (error) {
      console.error('Image generation error:', error);

      let errorMessage = error.message;

      // 네트워크 오류인 경우
      if (error.message === 'Failed to fetch') {
        errorMessage = '백엔드 서버에 연결할 수 없습니다.\n\n터미널에서 "npm run dev" 또는 "npm run server"를 실행했는지 확인해주세요.';
      }

      alert(`이미지 생성 중 오류가 발생했습니다:\n\n${errorMessage}`);
    } finally {
      setIsGenerating(false);
    }
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

          {contentType === 'image' ? (
            <>
              <div className="section">
                <h3>AI 모델 선택</h3>
                <div className="ai-model-selection">
                  {aiModels.map((model) => (
                    <button
                      key={model.id}
                      className={`model-btn ${aiModel === model.id ? 'active' : ''}`}
                      onClick={() => setAiModel(model.id)}
                    >
                      <span className="model-label">{model.label}</span>
                      <span className="model-provider">{model.provider}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="section">
                <div className="section-header">
                  <h3>이미지 생성 프롬프트</h3>
                  <button
                    className="btn-ai"
                    onClick={handleGenerateImage}
                    disabled={isGenerating}
                  >
                    {isGenerating ? '🔄 생성 중...' : '🎨 이미지 생성하기'}
                  </button>
                </div>
                <textarea
                  className="content-textarea"
                  placeholder="생성할 이미지를 설명하는 프롬프트를 입력하세요... 예: 'A beautiful sunset over the ocean with vibrant colors'"
                  value={imagePrompt}
                  onChange={(e) => setImagePrompt(e.target.value)}
                  rows={6}
                />
              </div>

              {generatedImage && (
                <div className="section">
                  <h3>생성된 이미지</h3>
                  <div className="generated-image-container">
                    <img src={generatedImage} alt="Generated" className="generated-image" />
                  </div>
                </div>
              )}
            </>
          ) : (
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
          )}

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
                {contentType === 'image' ? (
                  <>
                    <h4>{title || '이미지 제목'}</h4>
                    {generatedImage ? (
                      <img src={generatedImage} alt="Preview" style={{ width: '100%', borderRadius: '8px', marginTop: '12px' }} />
                    ) : (
                      <p style={{ textAlign: 'center', color: '#9ca3af', padding: '40px 0' }}>
                        이미지 생성 후 미리보기가 표시됩니다
                      </p>
                    )}
                  </>
                ) : (
                  <>
                    <h4>{title || '제목 미리보기'}</h4>
                    <p>{content || '내용이 여기에 표시됩니다...'}</p>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="tips-section">
            <h3>💡 작성 팁</h3>
            {contentType === 'image' ? (
              <ul className="tips-list">
                <li>구체적이고 상세한 프롬프트를 작성하세요</li>
                <li>원하는 스타일과 분위기를 명확히 하세요</li>
                <li>색상, 조명, 구도 등을 구체적으로 명시하세요</li>
                <li>영어로 작성하면 더 좋은 결과를 얻을 수 있습니다</li>
              </ul>
            ) : (
              <ul className="tips-list">
                <li>명확하고 간결한 제목을 사용하세요</li>
                <li>타겟 고객을 고려한 톤을 유지하세요</li>
                <li>행동 유도 문구(CTA)를 포함하세요</li>
                <li>해시태그를 적절히 활용하세요</li>
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ContentCreator;
