import React, { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import SNSPublishModal from './sns/SNSPublishModal';
import './AgenticContentResult.css';

function AgenticContentResult({ result, onEdit, onSave }) {
  const [activeTab, setActiveTab] = useState('blog');
  const [showPublishModal, setShowPublishModal] = useState(false);

  // 이미지 생성 상태
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [imagePrompt, setImagePrompt] = useState('');
  const [imageError, setImageError] = useState(null);

  // 복사 상태
  const [isCopied, setIsCopied] = useState(false);

  // 이미지 첨부용 ref
  const fileInputRef = useRef(null);
  const blogContentRef = useRef(null);

  if (!result) return null;

  const { blog, sns, analysis, critique, metadata, uploadedImages } = result;

  // 블로그 콘텐츠를 이미지 마커 기준으로 분할하여 React 요소로 렌더링
  const renderBlogContentWithImages = (content) => {
    if (!uploadedImages || uploadedImages.length === 0) {
      return <ReactMarkdown>{content}</ReactMarkdown>;
    }

    // [IMAGE_1], [IMAGE_2] 등의 마커로 콘텐츠 분할
    const parts = [];
    let remainingContent = content;
    let partIndex = 0;

    // 모든 이미지 마커를 찾아서 분할
    for (let i = 1; i <= uploadedImages.length; i++) {
      const marker = `[IMAGE_${i}]`;
      const markerIndex = remainingContent.indexOf(marker);

      if (markerIndex !== -1) {
        // 마커 이전 텍스트
        const beforeText = remainingContent.substring(0, markerIndex);
        if (beforeText.trim()) {
          parts.push(
            <div key={`text-${partIndex}`} className="content-text-block">
              <ReactMarkdown>{beforeText}</ReactMarkdown>
            </div>
          );
          partIndex++;
        }

        // 이미지 삽입
        parts.push(
          <div key={`image-${i}`} className="content-image-block">
            <img
              src={uploadedImages[i - 1]}
              alt={`업로드 이미지 ${i}`}
              className="uploaded-content-image"
            />
          </div>
        );

        // 나머지 콘텐츠
        remainingContent = remainingContent.substring(markerIndex + marker.length);
      }
    }

    // 남은 텍스트 추가
    if (remainingContent.trim()) {
      parts.push(
        <div key={`text-final`} className="content-text-block">
          <ReactMarkdown>{remainingContent}</ReactMarkdown>
        </div>
      );
    }

    return <>{parts}</>;
  };

  // 블로그 콘텐츠 복사 (텍스트만 - 이미지 마커 제거)
  const handleCopyBlogContent = async () => {
    try {
      // 이미지 마커 제거한 텍스트
      let cleanContent = blog.content;
      if (uploadedImages && uploadedImages.length > 0) {
        for (let i = 1; i <= uploadedImages.length; i++) {
          cleanContent = cleanContent.replace(`[IMAGE_${i}]`, '\n\n[이미지 위치]\n\n');
        }
      }

      const textContent = `${blog.title}\n\n${cleanContent}\n\n${blog.tags.map(tag => `#${tag}`).join(' ')}`;
      await navigator.clipboard.writeText(textContent);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (error) {
      console.error('복사 실패:', error);
      alert('복사에 실패했습니다. 직접 선택하여 복사해주세요.');
    }
  };

  // 이미지 다운로드
  const handleDownloadImages = () => {
    if (!uploadedImages || uploadedImages.length === 0) {
      alert('다운로드할 이미지가 없습니다.');
      return;
    }

    uploadedImages.forEach((dataUrl, index) => {
      const link = document.createElement('a');
      link.href = dataUrl;
      link.download = `blog_image_${index + 1}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  };

  // 점수에 따른 색상 결정
  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981'; // green
    if (score >= 60) return '#f59e0b'; // orange
    return '#ef4444'; // red
  };

  // 점수에 따른 등급
  const getScoreGrade = (score) => {
    if (score >= 90) return '우수';
    if (score >= 80) return '양호';
    if (score >= 70) return '보통';
    return '개선필요';
  };

  // AI 이미지 생성
  const handleGenerateImage = async () => {
    const prompt = imagePrompt.trim() || `${analysis?.subject || blog?.title || sns?.content?.slice(0, 100)}`;

    if (!prompt) {
      setImageError('이미지 생성을 위한 프롬프트를 입력해주세요.');
      return;
    }

    setIsGeneratingImage(true);
    setImageError(null);

    try {
      const response = await fetch('http://localhost:8000/api/generate-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt,
          model: 'nanovana',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || '이미지 생성에 실패했습니다.');
      }

      const data = await response.json();
      setGeneratedImage(data.imageUrl);
    } catch (error) {
      console.error('Image generation error:', error);
      setImageError(error.message || '이미지 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGeneratingImage(false);
    }
  };

  // 이미지 다운로드
  const handleDownloadImage = () => {
    if (!generatedImage) return;
    const link = document.createElement('a');
    link.href = generatedImage;
    link.download = `sns_image_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // 이미지 첨부 핸들러
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // 파일 크기 체크 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setImageError('이미지 크기는 10MB 이하여야 합니다.');
      return;
    }

    // 이미지 타입 체크
    if (!file.type.startsWith('image/')) {
      setImageError('이미지 파일만 첨부할 수 있습니다.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      setGeneratedImage(event.target.result);
      setImageError(null);
    };
    reader.onerror = () => {
      setImageError('이미지를 읽는 중 오류가 발생했습니다.');
    };
    reader.readAsDataURL(file);
  };

  // 파일 선택 버튼 클릭
  const handleAttachClick = () => {
    fileInputRef.current?.click();
  };

  // SNS 발행 모달 열기
  const handleOpenPublishModal = () => {
    setShowPublishModal(true);
  };

  return (
    <div className="agentic-content-result">
      <div className="result-header">
        <div className="header-left">
          <h2>AI 생성 결과</h2>
          <div className="metadata-badges">
            <span className="badge badge-attempts">
              생성 시도: {metadata.attempts + 1}회
            </span>
            <span className="badge badge-score" style={{
              backgroundColor: getScoreColor(metadata.finalScores.blog),
              color: 'white'
            }}>
              블로그 점수: {metadata.finalScores.blog}점
            </span>
            <span className="badge badge-score" style={{
              backgroundColor: getScoreColor(metadata.finalScores.sns),
              color: 'white'
            }}>
              SNS 점수: {metadata.finalScores.sns}점
            </span>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={onEdit}>
            다시 생성
          </button>
          <button className="btn-primary" onClick={onSave}>
            저장하기
          </button>
        </div>
      </div>

      {/* 분석 정보 섹션 */}
      {analysis && (
        <div className="analysis-section">
          <h3>AI 분석 결과</h3>
          <div className="analysis-grid">
            <div className="analysis-item">
              <span className="analysis-label">주제:</span>
              <span className="analysis-value">{analysis.subject}</span>
            </div>
            <div className="analysis-item">
              <span className="analysis-label">카테고리:</span>
              <span className="analysis-value">{analysis.category}</span>
            </div>
            <div className="analysis-item">
              <span className="analysis-label">타겟 고객:</span>
              <span className="analysis-value">{analysis.targetAudience.join(', ')}</span>
            </div>
            <div className="analysis-item">
              <span className="analysis-label">분위기:</span>
              <span className="analysis-value">{analysis.mood}</span>
            </div>
            <div className="analysis-item">
              <span className="analysis-label">추천 톤:</span>
              <span className="analysis-value">{analysis.recommendedTone}</span>
            </div>
            {analysis.visualInfo && (
              <div className="analysis-item full-width">
                <span className="analysis-label">비주얼 분석:</span>
                <span className="analysis-value">{analysis.visualInfo}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 탭 네비게이션 */}
      <div className="content-tabs">
        <button
          className={`tab-button ${activeTab === 'blog' ? 'active' : ''}`}
          onClick={() => setActiveTab('blog')}
        >
          <span className="tab-icon">📝</span>
          네이버 블로그
        </button>
        <button
          className={`tab-button ${activeTab === 'sns' ? 'active' : ''}`}
          onClick={() => setActiveTab('sns')}
        >
          <span className="tab-icon">📱</span>
          인스타그램/페이스북
        </button>
        <button
          className={`tab-button ${activeTab === 'publish' ? 'active' : ''}`}
          onClick={() => setActiveTab('publish')}
        >
          <span className="tab-icon">🚀</span>
          이미지 생성 & SNS 발행
        </button>
      </div>

      {/* 블로그 콘텐츠 */}
      {activeTab === 'blog' && (
        <div className="content-panel">
          {/* 복사 버튼 */}
          <div className="copy-button-container">
            {uploadedImages && uploadedImages.length > 0 && (
              <button
                className="btn-download-images"
                onClick={handleDownloadImages}
              >
                이미지 다운로드 ({uploadedImages.length}개)
              </button>
            )}
            <button
              className={`btn-copy ${isCopied ? 'copied' : ''}`}
              onClick={handleCopyBlogContent}
            >
              {isCopied ? '완료!' : '복사'}
            </button>
          </div>

          <div className="content-section">
            <div className="section-header">
              <h3>제목</h3>
              <span className="quality-badge" style={{
                backgroundColor: getScoreColor(critique.blog.score)
              }}>
                {getScoreGrade(critique.blog.score)} ({critique.blog.score}점)
              </span>
            </div>
            <div className="title-display">{blog.title}</div>
          </div>

          <div className="content-section">
            <h3>본문</h3>
            <div className="content-display markdown-content" ref={blogContentRef}>
              {renderBlogContentWithImages(blog.content)}
            </div>
            <div className="content-stats">
              <span>글자 수: {blog.content.length}자</span>
              <span>예상 읽기 시간: {Math.ceil(blog.content.length / 500)}분</span>
              {uploadedImages && uploadedImages.length > 0 && (
                <span>첨부 이미지: {uploadedImages.length}개</span>
              )}
            </div>
          </div>

          <div className="content-section">
            <h3>태그</h3>
            <div className="tags-display">
              {blog.tags.map((tag, index) => (
                <span key={index} className="tag tag-blog">
                  #{tag}
                </span>
              ))}
            </div>
          </div>

          {/* 블로그 평가 상세 */}
          {critique && critique.blog && (
            <div className="critique-section">
              <h3>품질 평가</h3>
              <div className="critique-scores">
                <div className="score-item">
                  <span className="score-label">SEO 점수:</span>
                  <span className="score-value">{critique.blog.seoScore}점</span>
                </div>
                <div className="score-item">
                  <span className="score-label">가독성 점수:</span>
                  <span className="score-value">{critique.blog.readabilityScore}점</span>
                </div>
              </div>
              {critique.blog.strengths && critique.blog.strengths.length > 0 && (
                <div className="feedback-box strengths">
                  <h4>강점</h4>
                  <ul>
                    {critique.blog.strengths.map((strength, index) => (
                      <li key={index}>{strength}</li>
                    ))}
                  </ul>
                </div>
              )}
              {critique.blog.weaknesses && critique.blog.weaknesses.length > 0 && (
                <div className="feedback-box weaknesses">
                  <h4>약점</h4>
                  <ul>
                    {critique.blog.weaknesses.map((weakness, index) => (
                      <li key={index}>{weakness}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* SNS 콘텐츠 */}
      {activeTab === 'sns' && (
        <div className="content-panel">
          <div className="content-section">
            <div className="section-header">
              <h3>SNS 본문</h3>
              <span className="quality-badge" style={{
                backgroundColor: getScoreColor(critique.sns.score)
              }}>
                {getScoreGrade(critique.sns.score)} ({critique.sns.score}점)
              </span>
            </div>
            <div className="sns-content-display">
              {sns.content}
            </div>
            <div className="content-stats">
              <span>글자 수: {sns.content.length}자</span>
            </div>
          </div>

          <div className="content-section">
            <h3>해시태그</h3>
            <div className="tags-display">
              {sns.tags.map((tag, index) => (
                <span key={index} className="tag tag-sns">
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* SNS 평가 상세 */}
          {critique && critique.sns && (
            <div className="critique-section">
              <h3>품질 평가</h3>
              <div className="critique-scores">
                <div className="score-item">
                  <span className="score-label">참여도 점수:</span>
                  <span className="score-value">{critique.sns.engagementScore}점</span>
                </div>
                <div className="score-item">
                  <span className="score-label">해시태그 점수:</span>
                  <span className="score-value">{critique.sns.hashtagScore}점</span>
                </div>
              </div>
              {critique.sns.strengths && critique.sns.strengths.length > 0 && (
                <div className="feedback-box strengths">
                  <h4>강점</h4>
                  <ul>
                    {critique.sns.strengths.map((strength, index) => (
                      <li key={index}>{strength}</li>
                    ))}
                  </ul>
                </div>
              )}
              {critique.sns.weaknesses && critique.sns.weaknesses.length > 0 && (
                <div className="feedback-box weaknesses">
                  <h4>약점</h4>
                  <ul>
                    {critique.sns.weaknesses.map((weakness, index) => (
                      <li key={index}>{weakness}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 이미지 생성 & SNS 발행 탭 */}
      {activeTab === 'publish' && (
        <div className="content-panel publish-panel">
          <div className="publish-layout">
            {/* 왼쪽: 이미지 생성/첨부 */}
            <div className="publish-section image-section">
              <h3>🎨 이미지 준비</h3>
              <p className="section-desc">AI로 이미지를 생성하거나 직접 이미지를 첨부하세요</p>

              {/* 숨겨진 파일 입력 */}
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept="image/*"
                style={{ display: 'none' }}
              />

              {/* 이미지 첨부 버튼 */}
              <div className="image-attach-box">
                <button
                  className="btn-attach-image"
                  onClick={handleAttachClick}
                  disabled={isGeneratingImage}
                >
                  📎 이미지 첨부하기
                </button>
              </div>

              <div className="image-divider">
                <span>또는</span>
              </div>

              {/* AI 이미지 생성 */}
              <div className="image-prompt-box">
                <label>AI 이미지 생성</label>
                <textarea
                  value={imagePrompt}
                  onChange={(e) => setImagePrompt(e.target.value)}
                  placeholder={`기본값: ${analysis?.subject || blog?.title || '생성된 콘텐츠 주제'}\n\n더 구체적인 이미지를 원하시면 직접 입력해주세요.`}
                  rows={3}
                />
                <button
                  className="btn-generate-image"
                  onClick={handleGenerateImage}
                  disabled={isGeneratingImage}
                >
                  {isGeneratingImage ? (
                    <>
                      <span className="spinner-small"></span>
                      이미지 생성 중...
                    </>
                  ) : (
                    '🖼️ AI 이미지 생성'
                  )}
                </button>
              </div>

              {imageError && (
                <div className="error-message">{imageError}</div>
              )}

              {generatedImage && (
                <div className="generated-image-box">
                  <img src={generatedImage} alt="Generated" />
                  <div className="image-actions">
                    <button onClick={handleDownloadImage} className="btn-download">
                      💾 다운로드
                    </button>
                    <button onClick={() => setGeneratedImage(null)} className="btn-reset">
                      🗑️ 이미지 삭제
                    </button>
                  </div>
                </div>
              )}

              {!generatedImage && !isGeneratingImage && (
                <div className="image-placeholder">
                  <span className="placeholder-icon">🖼️</span>
                  <p>이미지를 첨부하거나 생성하면 여기에 표시됩니다</p>
                </div>
              )}
            </div>

            {/* 오른쪽: SNS 발행 미리보기 */}
            <div className="publish-section preview-section">
              <h3>📤 SNS 발행 미리보기</h3>
              <p className="section-desc">Instagram/Facebook에 발행될 내용입니다</p>

              <div className="preview-card">
                {/* 업로드된 이미지 또는 생성된 이미지 미리보기 */}
                {(uploadedImages?.length > 0 || generatedImage) && (
                  <div className="preview-image">
                    {uploadedImages?.length > 0 ? (
                      <div className="preview-image-grid">
                        {uploadedImages.map((img, idx) => (
                          <img key={idx} src={img} alt={`Preview ${idx + 1}`} />
                        ))}
                      </div>
                    ) : (
                      <img src={generatedImage} alt="Preview" />
                    )}
                  </div>
                )}
                <div className="preview-content">
                  <div className="preview-caption">
                    {sns?.content || ''}
                  </div>
                  {sns?.tags && sns.tags.length > 0 && (
                    <div className="preview-hashtags">
                      {sns.tags.map((tag, index) => (
                        <span key={index} className="preview-tag">{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <button
                className="btn-sns-publish-large"
                onClick={handleOpenPublishModal}
              >
                🚀 SNS에 발행하기
              </button>

              <p className="publish-note">
                * Instagram, Facebook 계정이 연동되어 있어야 발행할 수 있습니다.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* SNS 발행 모달 */}
      <SNSPublishModal
        isOpen={showPublishModal}
        onClose={() => setShowPublishModal(false)}
        content={{
          type: (uploadedImages?.length > 0 || generatedImage) ? 'image' : 'text',
          instagramCaption: sns?.content || '',
          facebookPost: sns?.content || '',
          hashtags: sns?.tags || [],
          images: uploadedImages?.length > 0
            ? uploadedImages
            : (generatedImage ? [generatedImage] : [])
        }}
      />
    </div>
  );
}

export default AgenticContentResult;
