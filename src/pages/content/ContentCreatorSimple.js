import { useState, useEffect, useCallback } from 'react';
import { FiCopy, FiTrash2 } from 'react-icons/fi';
import api, { contentSessionAPI } from '../../services/api';
import { generateAgenticContent } from '../../services/agenticService';
import './ContentCommon.css';
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
  { id: 'sns', label: 'Instagram/Facebook' },
  { id: 'blog', label: '블로그' },
  { id: 'x', label: 'X' },
  { id: 'threads', label: 'Threads' },
];

const VIDEO_DURATION_OPTIONS = [
  { id: 'short', label: 'Short', duration: '15초', cuts: 3, description: '빠른 임팩트' },
  { id: 'standard', label: 'Standard', duration: '30초', cuts: 5, description: '균형잡힌 구성' },
  { id: 'premium', label: 'Premium', duration: '60초', cuts: 8, description: '상세한 스토리' },
];

const CONTENT_TYPES = [
  { id: 'text', label: '글만', desc: '블로그, SNS 캡션' },
  { id: 'image', label: '이미지만', desc: '썸네일, 배너' },
  { id: 'both', label: '글 + 이미지', desc: '완성 콘텐츠' },
  { id: 'shortform', label: '숏폼 영상', desc: '마케팅 비디오' },
];

const IMAGE_COUNTS = [1, 2, 3, 4, 5, 6, 7, 8];

// ========== 유틸리티 함수 ==========
const formatDate = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const isCurrentYear = date.getFullYear() === now.getFullYear();
  const hh = String(date.getHours()).padStart(2, '0');
  const min = String(date.getMinutes()).padStart(2, '0');

  if (isCurrentYear) {
    return `${date.getMonth() + 1}/${date.getDate()} ${hh}:${min}`;
  }
  const yy = String(date.getFullYear()).slice(-2);
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${yy}/${mm}/${dd} ${hh}:${min}`;
};

const formatDateDetail = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const isCurrentYear = date.getFullYear() === now.getFullYear();
  const hours = date.getHours();
  const ampm = hours < 12 ? '오전' : '오후';
  const h12 = hours % 12 || 12;
  const min = String(date.getMinutes()).padStart(2, '0');

  const timeStr = `${ampm} ${h12}:${min}`;
  if (isCurrentYear) {
    return `${date.getMonth() + 1}월 ${date.getDate()}일 ${timeStr}`;
  }
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일 ${timeStr}`;
};

const copyToClipboard = (text, message) => {
  navigator.clipboard.writeText(text);
  alert(message);
};

const getStyleLabel = (styleId) => STYLES.find(s => s.id === styleId)?.label || styleId;

// ========== 서브 컴포넌트 ==========
const ResultCard = ({ title, children, onCopy }) => (
  <div className="result-card">
    <div className="result-card-header">
      <h3>{title}</h3>
      {onCopy && (
        <div className="result-card-actions">
          <button className="btn-icon" onClick={onCopy} title="복사">
            <FiCopy />
          </button>
        </div>
      )}
    </div>
    <div className="result-card-content">{children}</div>
  </div>
);

const TagList = ({ tags, isHashtag = false }) => (
  <div className="result-tags">
    {tags?.map((tag, idx) => (
      <span key={idx} className={`tag-item ${isHashtag ? 'hashtag' : ''}`}>{tag}</span>
    ))}
  </div>
);

const PlatformContent = ({ platform, data, onCopy }) => {
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
    <ResultCard title={title} onCopy={onCopy}>
      {platform === 'blog' && <div className="blog-title">{data.title}</div>}
      <div className={`text-result ${platform !== 'blog' ? 'sns-content' : ''}`}>
        {data.content}
      </div>
      <TagList tags={tags} isHashtag={isHashtag} />
    </ResultCard>
  );
};

// ========== 메인 컴포넌트 ==========
function ContentCreatorSimple() {
  // 탭 상태
  const [activeTab, setActiveTab] = useState('create');

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

  // 히스토리 상태
  const [history, setHistory] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);
  const [historyDetailTab, setHistoryDetailTab] = useState('blog');

  // 팝업 상태
  const [popupImage, setPopupImage] = useState(null);

  // ========== 히스토리 관련 함수 ==========
  const fetchHistory = useCallback(async () => {
    setIsLoadingHistory(true);
    try {
      const data = await contentSessionAPI.list(0, 50);
      setHistory(data);
    } catch (error) {
      console.error('생성 내역 로드 실패:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'history') fetchHistory();
  }, [activeTab, fetchHistory]);

  const handleSelectHistory = async (item) => {
    const firstTab = item.blog ? 'blog' : item.sns ? 'sns' : item.x ? 'x' : item.threads ? 'threads' : (item.image_count > 0 ? 'images' : 'blog');
    setHistoryDetailTab(firstTab);

    try {
      const detail = await contentSessionAPI.get(item.id);
      setSelectedHistoryItem(detail);
    } catch (error) {
      console.error('상세 조회 실패:', error);
      setSelectedHistoryItem(item);
    }
  };

  const handleDeleteHistory = async (sessionId) => {
    if (!window.confirm('이 콘텐츠를 삭제하시겠습니까?')) return;
    try {
      await contentSessionAPI.delete(sessionId);
      setHistory(prev => prev.filter(item => item.id !== sessionId));
      if (selectedHistoryItem?.id === sessionId) setSelectedHistoryItem(null);
      alert('삭제되었습니다.');
    } catch (error) {
      console.error('삭제 실패:', error);
      alert('삭제에 실패했습니다.');
    }
  };

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

        fetchHistory();
      }

      setResult(generatedResult);
      setProgress('');
      setActiveTab('result');
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
    setActiveTab('create');
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
    <div className="content-page">
      {/* 헤더 */}
      <div className="page-header">
        <h2>Contents 생성</h2>
        <p className="page-description">주제만 입력하면 AI가 글과 이미지를 한번에 생성합니다</p>
      </div>

      {/* 탭 네비게이션 */}
      <div className="content-tabs">
        <button className={`content-tab ${activeTab === 'create' ? 'active' : ''}`} onClick={() => setActiveTab('create')}>
          콘텐츠 생성
        </button>
        {result && (
          <button className={`content-tab ${activeTab === 'result' ? 'active' : ''}`} onClick={() => setActiveTab('result')}>
            생성 결과
          </button>
        )}
        <button className={`content-tab ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>
          생성 내역
        </button>
      </div>

      {/* 콘텐츠 생성 탭 */}
      {activeTab === 'create' && (
        <div className="content-grid single-column">
          <div className="form-section">
            {/* 콘텐츠 타입 선택 */}
            <div className="form-group">
              <label>생성 타입</label>
              <div className="type-options type-options-4">
                {CONTENT_TYPES.map(type => (
                  <div
                    key={type.id}
                    className={`type-card ${contentType === type.id ? 'selected' : ''}`}
                    onClick={() => setContentType(type.id)}
                  >
                    <div className="type-header"><h4>{type.label}</h4></div>
                    <p className="type-desc">{type.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* 주제 입력 */}
            <div className="form-group">
              <label>주제 *</label>
              <textarea
                className="form-textarea"
                placeholder="예: 가을 신상 니트 소개, 카페 오픈 이벤트 안내, 새로운 메뉴 출시..."
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                rows={3}
              />
            </div>

            {/* 이미지 업로드 (숏폼 영상) */}
            {contentType === 'shortform' && (
              <div className="form-group">
                <label>이미지 *</label>
                <div className="image-upload-area">
                  {uploadedImages.length === 0 ? (
                    <label className="upload-label">
                      <input type="file" accept="image/*" onChange={handleImageUpload} className="file-input" />
                      <span className="upload-icon">📸</span>
                      <span>클릭하여 이미지 업로드</span>
                      <span className="upload-hint">PNG, JPG, WebP (최대 10MB)</span>
                    </label>
                  ) : (
                    <div className="uploaded-image-preview">
                      <img src={uploadedImages[0].preview} alt="업로드된 이미지" />
                      <button type="button" className="btn-remove-image" onClick={() => setUploadedImages([])}>✕ 제거</button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 스타일 선택 */}
            <div className="form-group">
              <label>스타일</label>
              <div className="option-cards">
                {STYLES.map(s => (
                  <div key={s.id} className={`option-card ${style === s.id ? 'selected' : ''}`} onClick={() => setStyle(s.id)}>
                    {s.label}
                  </div>
                ))}
              </div>
            </div>

            {/* 플랫폼 선택 */}
            {(contentType === 'text' || contentType === 'both') && (
              <div className="form-group">
                <label>플랫폼</label>
                <div className="option-cards">
                  {PLATFORMS.map(p => (
                    <div
                      key={p.id}
                      className={`option-card ${selectedPlatforms.includes(p.id) ? 'selected' : ''}`}
                      onClick={() => togglePlatform(p.id)}
                    >
                      {p.label}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 이미지 갯수 선택 */}
            {(contentType === 'image' || contentType === 'both') && (
              <div className="form-group">
                <label>이미지 갯수</label>
                <div className="option-cards">
                  {IMAGE_COUNTS.map(count => (
                    <div
                      key={count}
                      className={`option-card ${imageCount === count ? 'selected' : ''}`}
                      onClick={() => setImageCount(count)}
                    >
                      {count}장
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 영상 길이 선택 */}
            {contentType === 'shortform' && (
              <div className="form-group">
                <label>영상 길이</label>
                <div className="video-duration-options">
                  {VIDEO_DURATION_OPTIONS.map(option => (
                    <div
                      key={option.id}
                      className={`duration-card ${videoDuration === option.id ? 'selected' : ''}`}
                      onClick={() => setVideoDuration(option.id)}
                    >
                      <div className="duration-header">
                        <h4>{option.label}</h4>
                        <span className="duration-time">{option.duration}</span>
                      </div>
                      <div className="duration-info">
                        <span className="duration-cuts">{option.cuts}개 컷</span>
                        <span className="duration-desc">{option.description}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 생성 버튼 */}
            <button className="btn-generate" onClick={handleGenerate} disabled={isGenerateDisabled}>
              {isGenerating ? <><span className="spinner"></span>{progress}</> : '생성하기'}
            </button>
          </div>
        </div>
      )}

      {/* 결과 탭 */}
      {activeTab === 'result' && result && (
        <div className="result-content">
          {/* 생성된 이미지 */}
          {result.images?.length > 0 && (
            <div className="result-card result-images-top">
              <div className="result-card-header">
                <h3>생성된 이미지 ({result.images.length}장)</h3>
                {result.images.length > 1 && (
                  <div className="result-card-actions">
                    <button className="btn-download" onClick={handleDownloadAllImages}>전체 다운로드</button>
                  </div>
                )}
              </div>
              <div className="result-card-content">
                <div className="images-grid">
                  {result.images.map((img, index) => (
                    <div key={index} className="image-item" onClick={() => setPopupImage(img.url)}>
                      <img src={img.url} alt={`Generated ${index + 1}`} />
                      <button className="btn-download-single" onClick={(e) => { e.stopPropagation(); handleDownloadImage(img.url, index); }}>
                        다운로드
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 2열 레이아웃 */}
          <div className="result-two-column">
            <div className="result-column-left">
              <PlatformContent platform="blog" data={result.text?.blog} onCopy={() => handleCopyBlog({ blog: result.text.blog })} />
            </div>
            <div className="result-column-right">
              {/* 품질 점수 */}
              {result.text?.critique && (
                <div className="quality-scores">
                  <div className="quality-score-card">
                    <div className="score-circle blog"><span className="score-number">{result.text.critique.blog?.score || '-'}</span></div>
                    <span className="score-label">블로그 품질</span>
                  </div>
                  <div className="quality-score-card">
                    <div className="score-circle sns"><span className="score-number">{result.text.critique.sns?.score || '-'}</span></div>
                    <span className="score-label">SNS 품질</span>
                  </div>
                </div>
              )}
              <PlatformContent platform="sns" data={result.text?.sns} onCopy={() => handleCopySNS({ sns: result.text.sns })} />
              <PlatformContent platform="x" data={result.text?.x} onCopy={() => handleCopyX({ x: result.text.x })} />
              <PlatformContent platform="threads" data={result.text?.threads} onCopy={() => handleCopyThreads({ threads: result.text.threads })} />
            </div>
          </div>

          <div className="result-actions-bar">
            <button className="btn-reset" onClick={handleReset}>새로 만들기</button>
          </div>
        </div>
      )}

      {/* 생성 내역 탭 */}
      {activeTab === 'history' && (
        <div className="history-content">
          {isLoadingHistory ? (
            <div className="loading-state">
              <span className="spinner"></span>
              <p>생성 내역을 불러오는 중...</p>
            </div>
          ) : history.length === 0 ? (
            <div className="empty-state">
              <span className="empty-icon">📝</span>
              <h3>생성 내역이 없습니다</h3>
              <p>콘텐츠를 생성하면 여기에 저장됩니다.</p>
              <button className="btn-primary" onClick={() => setActiveTab('create')}>콘텐츠 생성하기</button>
            </div>
          ) : (
            <div className="history-layout">
              {/* 히스토리 목록 */}
              <div className="history-list">
                {history.map(item => (
                  <div
                    key={item.id}
                    className={`history-item ${selectedHistoryItem?.id === item.id ? 'selected' : ''}`}
                    onClick={() => handleSelectHistory(item)}
                  >
                    <div className="history-item-header">
                      <h4>{item.topic || '주제 없음'}</h4>
                      <span className="history-date">{formatDate(item.created_at)}</span>
                    </div>
                    <div className="history-item-info">
                      <span className="info-badge type">
                        {item.content_type === 'text' ? '글만' : item.content_type === 'image' ? '이미지만' : '글+이미지'}
                      </span>
                      <span className="info-badge style">{getStyleLabel(item.style)}</span>
                    </div>
                    <div className="history-item-meta">
                      {item.blog && <span className="platform-badge">블로그</span>}
                      {item.sns && <span className="platform-badge">SNS</span>}
                      {item.x && <span className="platform-badge">X</span>}
                      {item.threads && <span className="platform-badge">Threads</span>}
                    </div>
                  </div>
                ))}
              </div>

              {/* 히스토리 상세 */}
              <div className="history-detail">
                {selectedHistoryItem ? (
                  <>
                    <div className="history-detail-header">
                      <div className="history-detail-title-row">
                        <h3>{selectedHistoryItem.topic}</h3>
                        <button className="btn-icon btn-icon-delete" onClick={() => handleDeleteHistory(selectedHistoryItem.id)} title="삭제">
                          <FiTrash2 />
                        </button>
                      </div>
                      <div className="history-detail-meta">
                        <span className="info-badge type">
                          {selectedHistoryItem.content_type === 'text' ? '글만' : selectedHistoryItem.content_type === 'image' ? '이미지만' : '글+이미지'}
                        </span>
                        <span className="info-badge style">{getStyleLabel(selectedHistoryItem.style)}</span>
                        <span className="history-date">{formatDateDetail(selectedHistoryItem.created_at)}</span>
                      </div>
                    </div>

                    {/* 플랫폼 탭 */}
                    <div className="history-detail-tabs">
                      {['blog', 'sns', 'x', 'threads'].map(platform => (
                        selectedHistoryItem[platform] && (
                          <button
                            key={platform}
                            className={`history-tab ${historyDetailTab === platform ? 'active' : ''}`}
                            onClick={() => setHistoryDetailTab(platform)}
                          >
                            {platform === 'blog' ? '블로그' : platform === 'sns' ? 'SNS' : platform.toUpperCase()}
                          </button>
                        )
                      ))}
                      {selectedHistoryItem.images?.length > 0 && (
                        <button
                          className={`history-tab ${historyDetailTab === 'images' ? 'active' : ''}`}
                          onClick={() => setHistoryDetailTab('images')}
                        >
                          이미지 ({selectedHistoryItem.images.length})
                        </button>
                      )}
                    </div>

                    {/* 탭 콘텐츠 */}
                    <div className="history-detail-content">
                      {historyDetailTab === 'blog' && (
                        <PlatformContent platform="blog" data={selectedHistoryItem.blog} onCopy={() => handleCopyBlog(selectedHistoryItem)} />
                      )}
                      {historyDetailTab === 'sns' && (
                        <PlatformContent platform="sns" data={selectedHistoryItem.sns} onCopy={() => handleCopySNS(selectedHistoryItem)} />
                      )}
                      {historyDetailTab === 'x' && (
                        <PlatformContent platform="x" data={selectedHistoryItem.x} onCopy={() => handleCopyX(selectedHistoryItem)} />
                      )}
                      {historyDetailTab === 'threads' && (
                        <PlatformContent platform="threads" data={selectedHistoryItem.threads} onCopy={() => handleCopyThreads(selectedHistoryItem)} />
                      )}
                      {historyDetailTab === 'images' && selectedHistoryItem.images?.length > 0 && (
                        <div className="result-card result-card-full">
                          <div className="result-card-header">
                            <h3>생성된 이미지 ({selectedHistoryItem.images.length}장)</h3>
                          </div>
                          <div className="result-card-content">
                            <div className="images-grid">
                              {selectedHistoryItem.images.map((img, idx) => (
                                <div key={idx} className="image-item" onClick={() => setPopupImage(img.image_url)}>
                                  <img src={img.image_url} alt={`생성된 이미지 ${idx + 1}`} />
                                  <button
                                    className="btn-download-single"
                                    onClick={(e) => { e.stopPropagation(); handleDownloadImage(img.image_url, idx); }}
                                  >
                                    다운로드
                                  </button>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="empty-detail">
                    <span className="empty-icon">👈</span>
                    <p>왼쪽에서 콘텐츠를 선택하세요</p>
                  </div>
                )}
              </div>
            </div>
          )}
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
    </div>
  );
}

export default ContentCreatorSimple;
