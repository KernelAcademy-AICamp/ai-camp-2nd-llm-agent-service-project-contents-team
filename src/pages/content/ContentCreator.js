import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './ContentCreator.css';
import BlogPostForm from '../../components/BlogPostForm';
import BlogPostResult from '../../components/BlogPostResult';
import AIContentGenerator from './AIContentGenerator';
import { generateBlogPost } from '../../services/geminiService';

function ContentCreator() {
  const navigate = useNavigate();
  const [contentType, setContentType] = useState('social');
  const [platform, setPlatform] = useState('instagram');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [aiModel, setAiModel] = useState('whisk');
  const [imagePrompt, setImagePrompt] = useState('');
  const [generatedImage, setGeneratedImage] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedBlogPost, setGeneratedBlogPost] = useState(null);
  const [referenceImage, setReferenceImage] = useState(null); // 레퍼런스 이미지
  const [generationMode, setGenerationMode] = useState('text'); // 'text' or 'image'

  const contentTypes = [
    { id: 'ai', label: 'AI 글 생성', icon: '🤖' },
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
    { id: 'whisk', label: '✨ Whisk AI (무료)', provider: 'Pollinations' },
    { id: 'nanovana', label: '나노바나나 (Nanovana)', provider: 'Anthropic' },
    { id: 'gemini', label: '제미나이 (Gemini)', provider: 'Google' },
  ];

  // 카드뉴스 선택 시 /cardnews로 이동
  useEffect(() => {
    if (contentType === 'cardnews') {
      navigate('/cardnews');
    }
  }, [contentType, navigate]);

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setReferenceImage(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleGenerateImage = async () => {
    if (!imagePrompt.trim()) {
      alert('이미지 생성을 위한 프롬프트를 입력해주세요.');
      return;
    }

    setIsGenerating(true);
    try {
      const requestBody = {
        prompt: imagePrompt,
        model: aiModel,
      };

      // 레퍼런스 이미지가 있으면 추가
      if (generationMode === 'image' && referenceImage) {
        requestBody.referenceImage = referenceImage;
      }

      const response = await fetch('/api/generate-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
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

  const handleGenerateBlogPost = async (formData) => {
    setIsGenerating(true);
    try {
      const result = await generateBlogPost(formData);
      setGeneratedBlogPost(result);
      setTitle(result.title);
      setContent(result.content);
    } catch (error) {
      alert('블로그 포스트 생성 중 오류가 발생했습니다. 다시 시도해주세요.');
      console.error('Error:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleEditBlogPost = () => {
    setGeneratedBlogPost(null);
  };

  const handleSaveBlogPost = () => {
    alert('콘텐츠가 저장되었습니다.');
    // 추후 실제 저장 로직 구현
  };

  const handleGenerate = () => {
    // 다른 콘텐츠 타입의 AI 생성 로직 (추후 구현)
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
        {contentType !== 'ai' && (
          <div className="header-actions">
            <button className="btn-secondary" onClick={handleSave}>
              임시 저장
            </button>
            <button className="btn-primary" onClick={handleSchedule}>
              저장 및 예약
            </button>
          </div>
        )}
      </div>

      <div className={`creator-content ${contentType === 'blog' || contentType === 'ai' ? 'blog-layout' : ''}`}>
        {/* 콘텐츠 타입 선택 */}
        <div className="section">
          <h3>콘텐츠 유형</h3>
          <div className="content-type-grid">
            {contentTypes.map((type) => (
              <button
                key={type.id}
                className={`type-card ${contentType === type.id ? 'active' : ''}`}
                onClick={() => {
                  setContentType(type.id);
                  setGeneratedBlogPost(null);
                }}
              >
                <span className="type-icon">{type.icon}</span>
                <span className="type-label">{type.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* AI 글 생성 전용 UI */}
        {contentType === 'ai' && (
          <AIContentGenerator />
        )}

        {/* 블로그 포스트 전용 UI */}
        {contentType === 'blog' && (
          <>
            <BlogPostForm
              onGenerate={handleGenerateBlogPost}
              isGenerating={isGenerating}
            />

            {generatedBlogPost && (
              <BlogPostResult
                result={generatedBlogPost}
                onEdit={handleEditBlogPost}
                onSave={handleSaveBlogPost}
              />
            )}
          </>
        )}

        {/* 다른 콘텐츠 타입 UI (기존) */}
        {contentType !== 'blog' && contentType !== 'ai' && (
          <>
            <div className="creator-main">
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

              {/* 이미지 생성 타입일 때 AI 모델 선택 추가 */}
              {contentType === 'image' && (
                <>
                  <div className="section">
                    <h3>🤖 AI 모델 선택</h3>
                    <select
                      className="platform-select"
                      value={aiModel}
                      onChange={(e) => setAiModel(e.target.value)}
                      style={{ marginBottom: '12px' }}
                    >
                      {aiModels.map((model) => (
                        <option key={model.id} value={model.id}>
                          {model.label}
                        </option>
                      ))}
                    </select>
                    <p style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                      {aiModels.find(m => m.id === aiModel)?.provider} 제공
                    </p>
                  </div>

                  <div className="section">
                    <h3>📐 생성 모드 선택</h3>
                    <div style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
                      <button
                        className={`mode-button ${generationMode === 'text' ? 'active' : ''}`}
                        onClick={() => {
                          setGenerationMode('text');
                          setReferenceImage(null);
                        }}
                        style={{
                          flex: 1,
                          padding: '12px',
                          border: generationMode === 'text' ? '2px solid #2196F3' : '2px solid #e0e0e0',
                          borderRadius: '8px',
                          background: generationMode === 'text' ? '#e3f2fd' : 'white',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                        }}
                      >
                        <div style={{ fontSize: '24px', marginBottom: '4px' }}>📝</div>
                        <div style={{ fontWeight: 'bold' }}>텍스트 → 이미지</div>
                        <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
                          텍스트 설명으로 이미지 생성
                        </div>
                      </button>
                      <button
                        className={`mode-button ${generationMode === 'image' ? 'active' : ''}`}
                        onClick={() => setGenerationMode('image')}
                        style={{
                          flex: 1,
                          padding: '12px',
                          border: generationMode === 'image' ? '2px solid #2196F3' : '2px solid #e0e0e0',
                          borderRadius: '8px',
                          background: generationMode === 'image' ? '#e3f2fd' : 'white',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                        }}
                      >
                        <div style={{ fontSize: '24px', marginBottom: '4px' }}>🖼️</div>
                        <div style={{ fontWeight: 'bold' }}>이미지 → 이미지</div>
                        <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
                          레퍼런스 이미지 기반 생성
                        </div>
                      </button>
                    </div>

                    {generationMode === 'image' && (
                      <div style={{ marginTop: '12px' }}>
                        <label
                          htmlFor="reference-image-upload"
                          style={{
                            display: 'block',
                            padding: '16px',
                            border: '2px dashed #2196F3',
                            borderRadius: '8px',
                            textAlign: 'center',
                            cursor: 'pointer',
                            background: referenceImage ? '#e3f2fd' : '#f5f5f5',
                            transition: 'all 0.2s',
                          }}
                        >
                          <input
                            id="reference-image-upload"
                            type="file"
                            accept="image/*"
                            onChange={handleImageUpload}
                            style={{ display: 'none' }}
                          />
                          {referenceImage ? (
                            <div>
                              <img
                                src={referenceImage}
                                alt="Reference"
                                style={{
                                  maxWidth: '100%',
                                  maxHeight: '200px',
                                  borderRadius: '4px',
                                  marginBottom: '8px',
                                }}
                              />
                              <p style={{ color: '#2196F3', fontSize: '12px' }}>
                                ✅ 레퍼런스 이미지 업로드됨 (클릭하여 변경)
                              </p>
                            </div>
                          ) : (
                            <div>
                              <div style={{ fontSize: '48px', marginBottom: '8px' }}>📁</div>
                              <p style={{ color: '#2196F3', fontWeight: 'bold' }}>
                                레퍼런스 이미지 업로드
                              </p>
                              <p style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                                클릭하여 이미지 파일 선택
                              </p>
                            </div>
                          )}
                        </label>
                      </div>
                    )}
                  </div>
                </>
              )}

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
                  <h3>{contentType === 'image' ? '이미지 프롬프트' : '내용'}</h3>
                  {contentType === 'image' ? (
                    <button
                      className="btn-ai"
                      onClick={handleGenerateImage}
                      disabled={isGenerating}
                    >
                      {isGenerating ? '🎨 생성 중...' : '🚀 이미지 생성하기'}
                    </button>
                  ) : (
                    <button className="btn-ai" onClick={handleGenerate}>
                      ✨ AI로 생성하기
                    </button>
                  )}
                </div>
                <textarea
                  className="content-textarea"
                  placeholder={contentType === 'image'
                    ? "이미지 설명을 입력하세요 (예: A beautiful sunset over mountains with golden light)"
                    : "콘텐츠 내용을 입력하거나 AI로 생성하세요..."}
                  value={contentType === 'image' ? imagePrompt : content}
                  onChange={(e) => contentType === 'image'
                    ? setImagePrompt(e.target.value)
                    : setContent(e.target.value)}
                  rows={12}
                />
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
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <h4>{title || '이미지 미리보기'}</h4>
                      {generatedImage && (
                        <span style={{ fontSize: '11px', color: '#666', backgroundColor: '#f0f9ff', padding: '4px 8px', borderRadius: '4px' }}>
                          {aiModels.find(m => m.id === aiModel)?.label}
                        </span>
                      )}
                    </div>
                    {isGenerating ? (
                      <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                        <div style={{
                          border: '3px solid #f3f3f3',
                          borderTop: '3px solid #3498db',
                          borderRadius: '50%',
                          width: '40px',
                          height: '40px',
                          animation: 'spin 1s linear infinite',
                          margin: '0 auto 16px'
                        }}></div>
                        <p style={{ color: '#666' }}>🎨 AI가 이미지를 생성하고 있습니다...</p>
                        <p style={{ color: '#999', fontSize: '12px', marginTop: '8px' }}>
                          {aiModel === 'whisk' ? '보통 10-20초 정도 소요됩니다' : '보통 30초~1분 정도 소요됩니다'}
                        </p>
                      </div>
                    ) : generatedImage ? (
                      <>
                        <img src={generatedImage} alt="Preview" style={{ width: '100%', borderRadius: '8px', marginTop: '12px' }} />
                        <p style={{ fontSize: '12px', color: '#666', marginTop: '8px', textAlign: 'center' }}>
                          ✅ 생성 완료! 이미지를 우클릭하여 저장할 수 있습니다.
                        </p>
                      </>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎨</div>
                        <p style={{ color: '#9ca3af' }}>프롬프트를 입력하고<br />이미지를 생성해보세요</p>
                      </div>
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
              <>
                <div style={{ marginBottom: '12px', padding: '8px', backgroundColor: '#f0f9ff', borderRadius: '4px', fontSize: '13px' }}>
                  <strong>선택된 모델:</strong> {aiModels.find(m => m.id === aiModel)?.label}
                </div>
                {aiModel === 'whisk' ? (
                  <ul className="tips-list">
                    <li><strong>✨ 간단하게:</strong> Whisk는 짧고 핵심적인 아이디어를 좋아합니다</li>
                    <li><strong>🎨 창의성:</strong> 예상치 못한 창의적인 해석을 기대하세요</li>
                    <li><strong>🌈 추상적 개념:</strong> "행복", "모험", "미래" 같은 단어도 효과적</li>
                    <li><strong>🔮 조합 실험:</strong> 서로 다른 요소를 조합해보세요 (예: "우주 카페")</li>
                    <li><strong>무료 &amp; 빠름:</strong> API 키 없이 고품질 이미지 생성</li>
                  </ul>
                ) : aiModel === 'nanovana' ? (
                  <ul className="tips-list">
                    <li><strong>🍌 상세하게:</strong> 구체적인 디테일을 많이 포함하세요</li>
                    <li><strong>📸 사실적:</strong> "고화질", "사진 같은", "리얼리스틱" 표현 추가</li>
                    <li><strong>🌟 품질 키워드:</strong> "프로페셔널", "4K", "고품질" 등</li>
                    <li><strong>💡 조명과 색감:</strong> 조명과 색상 톤을 구체적으로 설명</li>
                    <li><strong>⚠️ 할당량:</strong> Google API 무료 할당량 제한 있음</li>
                  </ul>
                ) : (
                  <ul className="tips-list">
                    <li><strong>🎨 구체적으로:</strong> "필라테스 센터" 보다 "현대적인 필라테스 센터 인테리어, 밝은 자연광"</li>
                    <li><strong>🌅 분위기 설명:</strong> "따뜻한", "차가운", "활기찬" 같은 표현 추가</li>
                    <li><strong>💡 조명 언급:</strong> "자연광", "따뜻한 조명", "스튜디오 조명" 등</li>
                    <li><strong>🌐 한국어 가능:</strong> 모든 모델이 한국어를 잘 이해합니다</li>
                    <li><strong>🚫 네거티브:</strong> 원하지 않는 요소를 명시하면 더 정확</li>
                  </ul>
                )}
              </>
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
          </>
        )}
      </div>
    </div>
  );
}

export default ContentCreator;
