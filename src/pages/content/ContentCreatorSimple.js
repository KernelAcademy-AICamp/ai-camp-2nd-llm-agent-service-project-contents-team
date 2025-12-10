import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiCopy, FiSend, FiArrowRight } from 'react-icons/fi';
import api, { contentSessionAPI } from '../../services/api';
import { generateAgenticContent } from '../../services/agenticService';
import SNSPublishModal from '../../components/sns/SNSPublishModal';
import './ContentCreatorSimple.css';

// ========== 상수 정의 ==========
const STYLES = [
  { id: 'casual', label: '캐주얼', textTone: '친근하고 편안한 말투로, 이모지를 적절히 사용', imageStyle: 'casual lifestyle photography, warm natural lighting, relaxed atmosphere' },
  { id: 'professional', label: '전문적', textTone: '전문적이고 신뢰감 있는 어조로, 정확한 정보 전달', imageStyle: 'professional corporate style, clean minimalist design, sophisticated lighting' },
  { id: 'friendly', label: '친근한', textTone: '다정하고 따뜻한 말투로, 독자와 대화하듯', imageStyle: 'friendly warm tones, soft lighting, inviting and approachable mood' },
  { id: 'formal', label: '격식체', textTone: '격식있고 품위있는 문체로, 존댓말 사용', imageStyle: 'formal elegant style, classic composition, refined and prestigious look' },
  { id: 'trendy', label: '트렌디', textTone: 'MZ세대 감성으로, 신조어와 트렌디한 표현 사용', imageStyle: 'trendy modern aesthetic, vibrant colors, Gen-Z style, dynamic composition' },
  { id: 'luxurious', label: '럭셔리', textTone: '고급스럽고 세련된 톤으로, 프리미엄 가치 강조', imageStyle: 'luxury premium style, rich dark tones, gold accents, elegant and exclusive' },
  { id: 'cute', label: '귀여운', textTone: '귀엽고 발랄한 말투로, 이모지 많이 사용', imageStyle: 'cute kawaii style, pastel colors, soft rounded shapes, adorable and playful' },
  { id: 'minimal', label: '미니멀', textTone: '간결하고 핵심만 담은 문체로, 군더더기 없이', imageStyle: 'minimalist clean design, white space, simple geometric shapes, modern simplicity' },
];

const PLATFORMS = [
  { id: 'blog', label: '블로그' },
  { id: 'sns', label: 'Instagram/Facebook' },
  { id: 'x', label: 'X' },
  { id: 'threads', label: 'Threads' },
];

const VIDEO_DURATION_OPTIONS = [
  { id: 'short', label: 'Short', duration: '15초', cuts: 3, description: '빠른 임팩트' },
  { id: 'standard', label: 'Standard', duration: '30초', cuts: 5, description: '균형잡힌 구성' },
  { id: 'premium', label: 'Premium', duration: '60초', cuts: 8, description: '상세한 스토리' },
];

const CONTENT_TYPES = [
  { id: 'text', label: '글만', desc: '블로그, SNS 캡션', icon: '📝' },
  { id: 'image', label: '이미지만', desc: '썸네일, 배너', icon: '🖼️' },
  { id: 'both', label: '글 + 이미지', desc: '완성 콘텐츠', icon: '✨', recommended: true },
  { id: 'shortform', label: '숏폼 영상', desc: '마케팅 비디오', icon: '🎬', isNew: true },
];

const IMAGE_COUNTS = [1, 2, 3, 4, 5, 6, 7, 8];

const QUICK_TOPICS = ['신제품 출시', '이벤트 안내', '후기 소개', '브랜드 소개'];

// ========== 유틸리티 함수 ==========
const copyToClipboard = (text, message) => {
  navigator.clipboard.writeText(text);
  alert(message);
};

const getScoreColor = (score) => {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#f59e0b';
  return '#ef4444';
};

const calcSnsAverageScore = (critique) => {
  if (!critique) return null;
  const scores = [critique.sns?.score, critique.x?.score, critique.threads?.score].filter(s => s != null);
  if (scores.length === 0) return null;
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
};

// ========== 서브 컴포넌트 ==========
const ResultCard = ({ title, children, onCopy, score }) => (
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

const TagList = ({ tags, isHashtag = false }) => (
  <div className="creator-result-tags">
    {tags?.map((tag, idx) => (
      <span key={idx} className={`creator-tag-item ${isHashtag ? 'hashtag' : ''}`}>{tag}</span>
    ))}
  </div>
);

const PlatformContent = ({ platform, data, onCopy, score }) => {
  if (!data) return null;

  const config = {
    blog: { title: '네이버 블로그', tagsKey: 'tags', isHashtag: false },
    sns: { title: 'Instagram / Facebook', tagsKey: 'hashtags', isHashtag: true },
    x: { title: 'X', tagsKey: 'hashtags', isHashtag: true },
    threads: { title: 'Threads', tagsKey: 'hashtags', isHashtag: true },
  };

  const { title, tagsKey, isHashtag } = config[platform];
  const tags = data[tagsKey] || data.tags;

  return (
    <ResultCard title={title} onCopy={onCopy} score={score}>
      {platform === 'blog' && <div className="creator-blog-title">{data.title}</div>}
      <div className={`creator-text-result ${platform !== 'blog' ? 'sns-content' : ''}`}>
        {data.content}
      </div>
      <TagList tags={tags} isHashtag={isHashtag} />
    </ResultCard>
  );
};

// ========== 메인 컴포넌트 ==========
function ContentCreatorSimple() {
  const navigate = useNavigate();

  // 입력 상태
  const [contentType, setContentType] = useState(null);
  const [topic, setTopic] = useState('');
  const [style, setStyle] = useState(null);
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [imageCount, setImageCount] = useState(1);
  const [uploadedImages, setUploadedImages] = useState([]);
  const [videoDuration, setVideoDuration] = useState('standard');

  // 생성 상태
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState('');
  const [result, setResult] = useState(null);

  // 팝업 상태
  const [popupImage, setPopupImage] = useState(null);

  // SNS 발행 모달 상태
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [publishContent, setPublishContent] = useState(null);

  // ========== 복사 함수 ==========
  const createCopyHandler = (getData, message) => (item) => {
    const data = getData(item);
    if (data) copyToClipboard(data, message);
  };

  const handleCopyBlog = createCopyHandler(
    (item) => item?.blog ? `${item.blog.title}\n\n${item.blog.content}\n\n태그: ${(item.blog.tags || []).join(', ')}` : null,
    '블로그 콘텐츠가 복사되었습니다.'
  );

  const handleCopySNS = createCopyHandler(
    (item) => item?.sns ? `${item.sns.content}\n\n${(item.sns.hashtags || item.sns.tags || []).join(' ')}` : null,
    'SNS 콘텐츠가 복사되었습니다.'
  );

  const handleCopyX = createCopyHandler(
    (item) => item?.x ? `${item.x.content}\n\n${(item.x.hashtags || item.x.tags || []).join(' ')}` : null,
    'X 콘텐츠가 복사되었습니다.'
  );

  const handleCopyThreads = createCopyHandler(
    (item) => item?.threads ? `${item.threads.content}\n\n${(item.threads.hashtags || item.threads.tags || []).join(' ')}` : null,
    'Threads 콘텐츠가 복사되었습니다.'
  );

  // ========== 이미지 다운로드 ==========
  const handleDownloadImage = (imageUrl, index) => {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `generated-image-${index + 1}-${Date.now()}.png`;
    link.click();
  };

  const handleDownloadAllImages = () => {
    result?.images?.forEach((img, index) => {
      setTimeout(() => handleDownloadImage(img.url, index), index * 500);
    });
  };

  // ========== 자동 저장 ==========
  const autoSaveContent = async (content, imageUrls, platforms, currentStyle, currentContentType, requestedImageCount) => {
    try {
      const saveData = {
        topic,
        content_type: currentContentType,
        style: currentStyle,
        selected_platforms: platforms,
        blog: content.blog ? { title: content.blog.title, content: content.blog.content, tags: content.blog.tags, score: content.critique?.blog?.score || null } : null,
        sns: content.sns ? { content: content.sns.content, hashtags: content.sns.tags, score: content.critique?.sns?.score || null } : null,
        x: content.x ? { content: content.x.content, hashtags: content.x.tags, score: content.critique?.x?.score || null } : null,
        threads: content.threads ? { content: content.threads.content, hashtags: content.threads.tags, score: content.critique?.threads?.score || null } : null,
        images: imageUrls.map(url => ({ image_url: url, prompt: topic })),
        requested_image_count: requestedImageCount,
        analysis_data: content.analysis || null,
        critique_data: content.critique || null,
        generation_attempts: content.metadata?.attempts || 1
      };
      await contentSessionAPI.save(saveData);
      console.log('✅ 콘텐츠 세션 저장 완료');
    } catch (error) {
      console.error('콘텐츠 저장 실패:', error);
    }
  };

  // ========== 콘텐츠 생성 ==========
  const handleGenerate = async () => {
    if (!topic.trim()) {
      alert('주제를 입력해주세요.');
      return;
    }

    setIsGenerating(true);
    setResult(null);
    setProgress('콘텐츠 생성 준비 중...');

    try {
      const generatedResult = { text: null, images: [] };

      // 글 생성
      if (contentType === 'text' || contentType === 'both') {
        setProgress('AI가 글을 작성하고 있습니다...');
        const selectedStyle = STYLES.find(s => s.id === style);
        const agenticResult = await generateAgenticContent(
          { textInput: topic, images: [], styleTone: selectedStyle?.textTone || '친근하고 편안한 말투로', selectedPlatforms },
          (progress) => setProgress(progress.message)
        );

        generatedResult.agenticResult = agenticResult;
        generatedResult.text = {
          blog: selectedPlatforms.includes('blog') ? agenticResult.blog : null,
          sns: selectedPlatforms.includes('sns') ? agenticResult.sns : null,
          x: selectedPlatforms.includes('x') ? agenticResult.x : null,
          threads: selectedPlatforms.includes('threads') ? agenticResult.threads : null,
          analysis: agenticResult.analysis,
          critique: agenticResult.critique,
          platforms: selectedPlatforms,
          style,
        };
      }

      // 이미지 생성
      if (contentType === 'image' || contentType === 'both') {
        const selectedStyleForImage = STYLES.find(s => s.id === style);
        const imageStylePrompt = selectedStyleForImage?.imageStyle || '';

        for (let i = 0; i < imageCount; i++) {
          setProgress(`AI가 이미지를 생성하고 있습니다... (${i + 1}/${imageCount})`);
          try {
            const enhancedPrompt = imageStylePrompt ? `${topic}. Style: ${imageStylePrompt}` : topic;
            const imageResponse = await api.post('/api/generate-image', { prompt: enhancedPrompt, model: 'nanovana' });
            if (imageResponse.data.imageUrl) {
              generatedResult.images.push({ url: imageResponse.data.imageUrl, prompt: topic });
            }
          } catch (imgError) {
            console.error(`이미지 ${i + 1} 생성 실패:`, imgError);
          }
        }
      }

      // 자동 저장
      if (generatedResult.agenticResult || generatedResult.text) {
        const imageUrls = generatedResult.images?.map(img => img.url) || [];
        const platforms = generatedResult.text?.platforms || [];
        const original = generatedResult.agenticResult || {};

        await autoSaveContent({
          blog: platforms.includes('blog') ? original.blog : null,
          sns: platforms.includes('sns') ? original.sns : null,
          x: platforms.includes('x') ? original.x : null,
          threads: platforms.includes('threads') ? original.threads : null,
          analysis: original.analysis || generatedResult.text?.analysis,
          critique: original.critique || generatedResult.text?.critique,
          metadata: { attempts: original.metadata?.attempts || 1 }
        }, imageUrls, platforms, style, contentType, imageCount);
      }

      setResult(generatedResult);
      setProgress('');
    } catch (error) {
      console.error('콘텐츠 생성 실패:', error);
      alert('콘텐츠 생성 중 오류가 발생했습니다.');
      setProgress('');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setTopic('');
    setProgress('');
  };

  // ========== 플랫폼 토글 ==========
  const togglePlatform = (platformId) => {
    if (selectedPlatforms.includes(platformId)) {
      if (selectedPlatforms.length > 1) {
        setSelectedPlatforms(prev => prev.filter(id => id !== platformId));
      }
    } else {
      setSelectedPlatforms(prev => [...prev, platformId]);
    }
  };

  // ========== 이미지 업로드 핸들러 ==========
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      alert('이미지 파일 크기는 10MB 이하여야 합니다.');
      return;
    }
    const reader = new FileReader();
    reader.onloadend = () => setUploadedImages([{ file, preview: reader.result }]);
    reader.readAsDataURL(file);
  };

  // ========== 생성 버튼 비활성화 조건 ==========
  const isGenerateDisabled = isGenerating || !topic.trim() || !contentType ||
    (contentType !== 'image' && contentType !== 'shortform' && !style) ||
    (contentType !== 'image' && contentType !== 'shortform' && selectedPlatforms.length === 0) ||
    (contentType === 'shortform' && uploadedImages.length === 0);

  // ========== 렌더링 ==========
  return (
    <div className="content-creator">
      {/* 결과가 없을 때: 생성 폼 */}
      {!result ? (
        <div className="creator-container">
          {/* 페이지 헤더 */}
          <div className="page-header">
            <h2>콘텐츠 생성</h2>
            <p className="page-description">AI로 블로그, SNS용 콘텐츠와 이미지를 생성합니다</p>
          </div>

          <div className="creator-grid">
            {/* 왼쪽: 기본 입력 */}
            <div className="creator-left">
              {/* 콘텐츠 타입 선택 */}
              <div className="creator-type-section">
                <label className="creator-label">생성 타입</label>
                <div className="creator-type-grid">
                  {CONTENT_TYPES.map(type => (
                    <div
                      key={type.id}
                      className={`creator-type-card ${contentType === type.id ? 'selected' : ''}`}
                      onClick={() => setContentType(type.id)}
                    >
                      {type.recommended && <span className="recommended-badge">추천</span>}
                      {type.isNew && <span className="new-badge">NEW</span>}
                      <span className="type-icon">{type.icon}</span>
                      <span className="type-label">{type.label}</span>
                      <span className="type-desc">{type.desc}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 주제 입력 */}
              <div className="creator-input-box">
                <textarea
                  className="creator-textarea"
                  placeholder="무엇에 대한 콘텐츠를 만들까요? 예: 가을 신상 니트 소개"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  rows={3}
                />
                <button
                  className="creator-generate-btn"
                  onClick={handleGenerate}
                  disabled={isGenerateDisabled}
                >
                  {isGenerating ? (
                    <><span className="spinner"></span>{progress}</>
                  ) : (
                    <>생성하기 <FiArrowRight className="btn-arrow" /></>
                  )}
                </button>
              </div>

              {/* 빠른 시작 */}
              <div className="creator-quick-options">
                <span className="quick-label">빠른 시작:</span>
                {QUICK_TOPICS.map(t => (
                  <button key={t} className="quick-chip" onClick={() => setTopic(t)}>{t}</button>
                ))}
              </div>

              {/* 기타 옵션 */}
              <div className="creator-other-options">
                <button className="option-btn" onClick={() => navigate('/history')}>
                  <span className="option-icon">📋</span>
                  생성 내역 보기
                </button>
              </div>
            </div>

            {/* 오른쪽: 타입별 옵션 */}
            <div className="creator-right">
              {!contentType ? (
                <div className="creator-options-placeholder">
                  <span className="placeholder-icon">⚙️</span>
                  <p>생성 타입을 선택하면<br />추가 옵션이 표시됩니다</p>
                </div>
              ) : (
                <div className="creator-options-panel">
                  <h3 className="options-title">옵션 설정</h3>

                  {/* 스타일 선택 */}
                  <div className="creator-option-section">
                    <label className="creator-label">스타일</label>
                    <div className="creator-chips">
                      {STYLES.map(s => (
                        <button
                          key={s.id}
                          className={`creator-chip ${style === s.id ? 'selected' : ''}`}
                          onClick={() => setStyle(s.id)}
                        >
                          {s.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 플랫폼 선택 */}
                  {(contentType === 'text' || contentType === 'both') && (
                    <div className="creator-option-section">
                      <label className="creator-label">플랫폼</label>
                      <div className="creator-chips">
                        {PLATFORMS.map(p => (
                          <button
                            key={p.id}
                            className={`creator-chip ${selectedPlatforms.includes(p.id) ? 'selected' : ''}`}
                            onClick={() => togglePlatform(p.id)}
                          >
                            {p.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 이미지 갯수 선택 */}
                  {(contentType === 'image' || contentType === 'both') && (
                    <div className="creator-option-section">
                      <label className="creator-label">이미지 갯수</label>
                      <div className="creator-chips">
                        {IMAGE_COUNTS.map(count => (
                          <button
                            key={count}
                            className={`creator-chip ${imageCount === count ? 'selected' : ''}`}
                            onClick={() => setImageCount(count)}
                          >
                            {count}장
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 이미지 업로드 (숏폼 영상) */}
                  {contentType === 'shortform' && (
                    <div className="creator-option-section">
                      <label className="creator-label">이미지 업로드 *</label>
                      <div className="creator-upload-area">
                        {uploadedImages.length === 0 ? (
                          <label className="upload-label">
                            <input type="file" accept="image/*" onChange={handleImageUpload} className="file-input" />
                            <span className="upload-icon">📸</span>
                            <span>클릭하여 이미지 업로드</span>
                            <span className="upload-hint">PNG, JPG, WebP (최대 10MB)</span>
                          </label>
                        ) : (
                          <div className="uploaded-preview">
                            <img src={uploadedImages[0].preview} alt="업로드된 이미지" />
                            <button type="button" className="btn-remove" onClick={() => setUploadedImages([])}>✕</button>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* 영상 길이 선택 */}
                  {contentType === 'shortform' && (
                    <div className="creator-option-section">
                      <label className="creator-label">영상 길이</label>
                      <div className="creator-duration-grid">
                        {VIDEO_DURATION_OPTIONS.map(option => (
                          <div
                            key={option.id}
                            className={`creator-duration-card ${videoDuration === option.id ? 'selected' : ''}`}
                            onClick={() => setVideoDuration(option.id)}
                          >
                            <span className="duration-label">{option.label}</span>
                            <span className="duration-time">{option.duration}</span>
                            <span className="duration-info">{option.cuts}컷 · {option.description}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* 결과 화면 */
        <div className="creator-result">
          <div className="result-header">
            <h2 className="result-title">생성 완료!</h2>
            <p className="result-subtitle">"{topic}" 주제로 콘텐츠가 생성되었습니다</p>
          </div>

          {/* 생성된 이미지 */}
          {result.images?.length > 0 && (
            <div className="creator-result-card result-images-section">
              <div className="creator-result-card-header">
                <h3>생성된 이미지 ({result.images.length}장)</h3>
                {result.images.length > 1 && (
                  <button className="btn-download" onClick={handleDownloadAllImages}>전체 다운로드</button>
                )}
              </div>
              <div className="creator-result-card-content">
                <div className="creator-images-grid">
                  {result.images.map((img, index) => (
                    <div key={index} className="creator-image-item" onClick={() => setPopupImage(img.url)}>
                      <img src={img.url} alt={`Generated ${index + 1}`} />
                      <button className="btn-download-overlay" onClick={(e) => { e.stopPropagation(); handleDownloadImage(img.url, index); }}>
                        다운로드
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 품질 점수 */}
          {result.text?.critique && (
            <div className="creator-quality-scores">
              <div className="quality-score-item">
                <div className="score-circle blog">
                  <span className="score-number">{result.text.critique.blog?.score || '-'}</span>
                </div>
                <span className="score-label">블로그</span>
              </div>
              <div className="quality-score-item">
                <div className="score-circle sns">
                  <span className="score-number">{calcSnsAverageScore(result.text.critique) || '-'}</span>
                </div>
                <span className="score-label">SNS 평균</span>
              </div>
            </div>
          )}

          {/* 텍스트 결과 */}
          <div className="creator-result-grid">
            <div className="result-column">
              <PlatformContent platform="blog" data={result.text?.blog} onCopy={() => handleCopyBlog({ blog: result.text.blog })} score={result.text?.critique?.blog?.score} />
            </div>
            <div className="result-column">
              <PlatformContent platform="sns" data={result.text?.sns} onCopy={() => handleCopySNS({ sns: result.text.sns })} score={result.text?.critique?.sns?.score} />
              <PlatformContent platform="x" data={result.text?.x} onCopy={() => handleCopyX({ x: result.text.x })} score={result.text?.critique?.x?.score} />
              <PlatformContent platform="threads" data={result.text?.threads} onCopy={() => handleCopyThreads({ threads: result.text.threads })} score={result.text?.critique?.threads?.score} />
            </div>
          </div>

          {/* 액션 버튼 */}
          <div className="creator-result-actions">
            <button className="btn-reset" onClick={handleReset}>새로 만들기</button>
            {result.text?.sns && (
              <button
                className="btn-publish"
                onClick={() => {
                  setPublishContent({
                    type: result.images?.length > 0 ? 'image' : 'text',
                    instagramCaption: result.text.sns?.content || '',
                    facebookPost: result.text.sns?.content || '',
                    hashtags: result.text.sns?.tags || result.text.sns?.hashtags || [],
                    images: result.images?.map(img => img.url) || []
                  });
                  setShowPublishModal(true);
                }}
              >
                <FiSend /> SNS 발행하기
              </button>
            )}
          </div>
        </div>
      )}

      {/* 이미지 팝업 */}
      {popupImage && (
        <div className="image-popup-overlay" onClick={() => setPopupImage(null)}>
          <div className="image-popup-content" onClick={(e) => e.stopPropagation()}>
            <button className="image-popup-close" onClick={() => setPopupImage(null)}>✕</button>
            <img src={popupImage} alt="확대 이미지" />
          </div>
        </div>
      )}

      {/* SNS 발행 모달 */}
      <SNSPublishModal
        isOpen={showPublishModal}
        onClose={() => setShowPublishModal(false)}
        content={publishContent}
      />
    </div>
  );
}

export default ContentCreatorSimple;
