import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiCopy, FiArrowRight, FiEdit3 } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import api, { contentSessionAPI } from '../../services/api';
import { generateAgenticContent } from '../../services/agenticService';
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
  { id: 'shortform', label: '숏폼 영상', desc: '마케팅 비디오', icon: '🎬' },
];

const IMAGE_COUNTS = [1, 2, 3, 4, 5, 6, 7, 8];

const IMAGE_FORMATS = [
  { id: 'ai-image', label: 'AI 이미지' },
  { id: 'cardnews', label: '카드뉴스' },
];

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

const PlatformContent = ({ platform, data, onCopy, score }) => {
  if (!data) return null;

  const config = {
    blog: { title: '네이버 블로그' },
    sns: { title: 'Instagram / Facebook' },
    x: { title: 'X' },
    threads: { title: 'Threads' },
  };

  const { title } = config[platform];

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

// 모든 플랫폼에서 태그를 모아서 중복 제거 (통합)
const collectAllTags = (textResult) => {
  if (!textResult) return [];

  const allTags = new Set();

  // 블로그 태그 (# 붙여서 통합)
  if (textResult.blog?.tags) {
    textResult.blog.tags.forEach(tag => {
      const normalizedTag = tag.startsWith('#') ? tag : `#${tag}`;
      allTags.add(normalizedTag);
    });
  }

  // SNS 해시태그
  const snsData = [textResult.sns, textResult.x, textResult.threads];
  snsData.forEach(data => {
    const tags = data?.hashtags || data?.tags || [];
    tags.forEach(tag => {
      const normalizedTag = tag.startsWith('#') ? tag : `#${tag}`;
      allTags.add(normalizedTag);
    });
  });

  return Array.from(allTags);
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
  const [imageFormat, setImageFormat] = useState('ai-image'); // 'ai-image' | 'cardnews'
  const [uploadedImages, setUploadedImages] = useState([]);
  const [videoDuration, setVideoDuration] = useState('standard');

  // 생성 상태
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState('');
  const [result, setResult] = useState(null);

  // 팝업 상태
  const [popupImage, setPopupImage] = useState(null);

  // 결과 컬럼 높이 동기화 ref
  const snsColumnRef = useRef(null);
  const blogCardRef = useRef(null);

  // SNS 컬럼 높이에 맞춰 블로그 카드 높이 설정
  useEffect(() => {
    if (result && snsColumnRef.current && blogCardRef.current) {
      const updateHeight = () => {
        const snsHeight = snsColumnRef.current.offsetHeight;
        blogCardRef.current.style.height = `${snsHeight}px`;
      };
      // 초기 설정 + 리사이즈 대응
      updateHeight();
      window.addEventListener('resize', updateHeight);
      return () => window.removeEventListener('resize', updateHeight);
    }
  }, [result]);

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
        if (imageFormat === 'cardnews') {
          // 카드뉴스 생성
          setProgress('AI가 카드뉴스를 생성하고 있습니다...');
          try {
            // 스타일을 컬러 테마로 매핑
            const styleToThemeMap = {
              'casual': 'warm',
              'professional': 'minimal',
              'friendly': 'warm',
              'formal': 'cool',
              'trendy': 'vibrant',
              'luxurious': 'purple',
              'cute': 'pastel',
              'minimal': 'minimal'
            };
            const colorTheme = styleToThemeMap[style] || 'warm';

            // FormData 생성 (백엔드가 Form 데이터를 받음)
            const formData = new FormData();
            formData.append('prompt', topic);
            formData.append('purpose', 'info');
            formData.append('fontStyle', 'pretendard');
            formData.append('colorTheme', colorTheme);
            formData.append('generateImages', 'true');
            // layoutType 제거: 첫 페이지는 Agent가 판단, 나머지는 상단 고정

            const cardnewsResponse = await api.post('/api/generate-agentic-cardnews', formData, {
              headers: {
                'Content-Type': 'multipart/form-data',
              },
            });

            if (cardnewsResponse.data.success && cardnewsResponse.data.cards) {
              // 생성된 카드뉴스 이미지들을 결과에 추가
              cardnewsResponse.data.cards.forEach((card, index) => {
                generatedResult.images.push({
                  url: card,
                  prompt: `${topic} - 카드 ${index + 1}`
                });
              });
              setProgress(`카드뉴스 ${cardnewsResponse.data.cards.length}장 생성 완료!`);
            }
          } catch (cardnewsError) {
            console.error('카드뉴스 생성 실패:', cardnewsError);
            alert('카드뉴스 생성 중 오류가 발생했습니다.');
          }
        } else {
          // AI 이미지 생성 (기존 로직)
          const selectedStyleForImage = STYLES.find(s => s.id === style);
          const imageStylePrompt = selectedStyleForImage?.imageStyle || '';

          for (let i = 0; i < imageCount; i++) {
            setProgress(`AI가 이미지를 생성하고 있습니다... (${i + 1}/${imageCount})`);
            try {
              const enhancedPrompt = imageStylePrompt ? `${topic}. Style: ${imageStylePrompt}` : topic;
              const imageResponse = await api.post('/api/generate-image', { prompt: enhancedPrompt, model: 'nanobanana' });
              if (imageResponse.data.imageUrl) {
                generatedResult.images.push({ url: imageResponse.data.imageUrl, prompt: topic });
              }
            } catch (imgError) {
              console.error(`이미지 ${i + 1} 생성 실패:`, imgError);
            }
          }
        }
      }

      // 숏폼 영상 생성
      if (contentType === 'shortform') {
        setProgress('AI가 숏폼 영상을 생성하고 있습니다...');
        try {
          // FormData 생성
          const formData = new FormData();
          formData.append('product_name', topic);
          formData.append('product_description', `${topic} 홍보 영상`);
          formData.append('tier', videoDuration);
          formData.append('image', uploadedImages[0].file);

          // 비디오 생성 작업 생성
          const videoJobResponse = await api.post('/api/ai-video/jobs', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });

          if (videoJobResponse.data && videoJobResponse.data.id) {
            const jobId = videoJobResponse.data.id;
            generatedResult.videoJobId = jobId;
            generatedResult.videoStatus = 'processing';

            console.log('Video generation job created:', jobId);

            // 작업 상태를 주기적으로 확인하는 폴링
            const checkVideoStatus = async () => {
              try {
                const statusResponse = await api.get(`/api/ai-video/jobs/${jobId}`);
                const job = statusResponse.data;

                console.log('Job status:', job.status, job.current_step);

                if (job.status === 'completed' && job.final_video_url) {
                  generatedResult.videoUrl = job.final_video_url;
                  generatedResult.videoStatus = 'completed';
                  setProgress('숏폼 영상 생성 완료!');
                  setResult({ ...generatedResult }); // 상태 업데이트
                } else if (job.status === 'failed') {
                  generatedResult.videoStatus = 'failed';
                  generatedResult.videoError = job.error_message;
                  setProgress(`영상 생성 실패: ${job.error_message}`);
                  setResult({ ...generatedResult }); // 상태 업데이트
                } else {
                  // 아직 처리 중 - 백엔드의 current_step을 그대로 표시
                  const currentStep = job.current_step || '처리 중';
                  setProgress(currentStep);
                  setResult({ ...generatedResult }); // 진행 중 상태도 계속 업데이트
                  setTimeout(checkVideoStatus, 2000); // 2초 후 다시 확인
                }
              } catch (statusError) {
                console.error('영상 상태 확인 실패:', statusError);
                setProgress('영상 상태 확인 중 오류가 발생했습니다.');
              }
            };

            // 즉시 결과 화면으로 전환하고 폴링 시작
            setProgress('AI가 숏폼 영상을 생성하고 있습니다...');
            setResult({ ...generatedResult });
            setTimeout(checkVideoStatus, 1000); // 1초 후 첫 번째 상태 확인
          }
        } catch (videoError) {
          console.error('숏폼 영상 생성 실패:', videoError);
          const errorMsg = videoError.response?.data?.detail || videoError.message || '알 수 없는 오류';
          alert(`숏폼 영상 생성 중 오류가 발생했습니다: ${errorMsg}`);
          setProgress('');
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
    // 스타일 필요: 글만, 글+이미지, 이미지만 (숏폼 제외)
    (contentType !== 'shortform' && !style) ||
    // 플랫폼 필요: 글만, 글+이미지
    (contentType !== 'image' && contentType !== 'shortform' && selectedPlatforms.length === 0) ||
    // 숏폼 영상은 이미지 업로드 필수
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

                  {/* 이미지 형태 선택 - '이미지만' 선택 시 가장 위에 표시 */}
                  {contentType === 'image' && (
                    <div className="creator-option-section">
                      <label className="creator-label">이미지 형태</label>
                      <div className="creator-chips">
                        {IMAGE_FORMATS.map(format => (
                          <button
                            key={format.id}
                            className={`creator-chip ${imageFormat === format.id ? 'selected' : ''}`}
                            onClick={() => setImageFormat(format.id)}
                          >
                            {format.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 스타일 선택 */}
                  {contentType !== 'shortform' && (
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
                  )}

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

                  {/* 이미지 갯수 선택 - AI 이미지일 때만 표시 */}
                  {(contentType === 'both' || (contentType === 'image' && imageFormat === 'ai-image')) && (
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
            {contentType === 'shortform' && result.videoStatus === 'processing' ? (
              <>
                <h2 className="result-title">생성 중..</h2>
                <p className="result-subtitle">"{topic}" 주제로 숏폼 영상을 생성하고 있습니다</p>
              </>
            ) : (
              <>
                <h2 className="result-title">생성 완료!</h2>
                <p className="result-subtitle">"{topic}" 주제로 콘텐츠가 생성되었습니다</p>
              </>
            )}
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

          {/* 생성된 비디오 */}
          {result.videoUrl && (
            <div className="creator-result-card result-video-section">
              <div className="creator-result-card-header">
                <h3>생성된 숏폼 영상</h3>
              </div>
              <div className="creator-result-card-content">
                <div className="creator-video-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <video
                    controls
                    style={{
                      width: '100%',
                      maxWidth: '400px',
                      aspectRatio: '9/16',
                      borderRadius: '8px',
                      backgroundColor: '#000'
                    }}
                  >
                    <source src={result.videoUrl} type="video/mp4" />
                    브라우저가 비디오를 지원하지 않습니다.
                  </video>
                  <a href={result.videoUrl} download className="btn-download" style={{ marginTop: '16px', display: 'inline-block' }}>
                    비디오 다운로드
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* 비디오 생성 중 */}
          {result.videoStatus === 'processing' && (() => {
            // 진행 단계 파싱
            const currentStep = progress || '';
            let currentPhase = 0;
            let progressPercent = 0;

            if (currentStep.includes('Analyzing') || currentStep.includes('storyboard')) {
              currentPhase = 0;
              progressPercent = currentStep.includes('storyboard') ? 20 : 10;
            } else if (currentStep.includes('Generating image')) {
              currentPhase = 1;
              const match = currentStep.match(/(\d+)\/(\d+)/);
              if (match) {
                const current = parseInt(match[1]);
                const total = parseInt(match[2]);
                progressPercent = 25 + (current / total) * 25;
              } else {
                progressPercent = 30;
              }
            } else if (currentStep.includes('transition')) {
              currentPhase = 2;
              const match = currentStep.match(/(\d+)\/(\d+)/);
              if (match) {
                const current = parseInt(match[1]);
                const total = parseInt(match[2]);
                progressPercent = 50 + (current / total) * 35;
              } else {
                progressPercent = 55;
              }
            } else if (currentStep.includes('Composing') || currentStep.includes('Concatenating') || currentStep.includes('Rendering') || currentStep.includes('Uploading')) {
              currentPhase = 3;
              if (currentStep.includes('Composing')) progressPercent = 85;
              else if (currentStep.includes('Concatenating')) progressPercent = 90;
              else if (currentStep.includes('Rendering')) progressPercent = 95;
              else if (currentStep.includes('Uploading')) progressPercent = 98;
            }

            const phases = [
              { name: '스토리보드 생성', icon: '📝' },
              { name: '이미지 생성', icon: '🖼️' },
              { name: '전환 비디오 생성', icon: '🎬' },
              { name: '최종 합성', icon: '✨' }
            ];

            return (
              <div className="creator-result-card result-video-section">
                <div className="creator-result-card-header">
                  <h3>숏폼 영상 생성 중...</h3>
                </div>
                <div className="creator-result-card-content">
                  <div style={{ padding: '40px' }}>
                    {/* 전체 프로그레스바 */}
                    <div style={{ marginBottom: '32px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontSize: '14px', fontWeight: '500' }}>전체 진행률</span>
                        <span style={{ fontSize: '14px', fontWeight: '600', color: '#D8BFD8' }}>{Math.round(progressPercent)}%</span>
                      </div>
                      <div style={{
                        width: '100%',
                        height: '8px',
                        backgroundColor: '#F8F8FF',
                        borderRadius: '4px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${progressPercent}%`,
                          height: '100%',
                          backgroundColor: '#D8BFD8',
                          transition: 'width 0.5s ease',
                          borderRadius: '4px'
                        }}></div>
                      </div>
                    </div>

                    {/* 단계별 표시 */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(4, 1fr)',
                      gap: '16px',
                      marginBottom: '24px'
                    }}>
                      {phases.map((phase, index) => (
                        <div key={index} style={{
                          padding: '16px',
                          borderRadius: '8px',
                          border: `2px solid ${currentPhase === index ? '#D8BFD8' : currentPhase > index ? '#E6E6FA' : '#F8F8FF'}`,
                          backgroundColor: currentPhase === index ? '#E6E6FA' : currentPhase > index ? '#F8F8FF' : '#fff',
                          textAlign: 'center',
                          transition: 'all 0.3s ease'
                        }}>
                          <div style={{ fontSize: '24px', marginBottom: '8px' }}>
                            {phase.icon}
                          </div>
                          <div style={{
                            fontSize: '12px',
                            fontWeight: currentPhase === index ? '600' : '500',
                            color: currentPhase === index ? '#D8BFD8' : currentPhase > index ? '#6b7280' : '#9ca3af'
                          }}>
                            {phase.name}
                          </div>
                          {currentPhase === index && (
                            <div style={{ marginTop: '8px' }}>
                              <div className="spinner" style={{ margin: '0 auto', width: '16px', height: '16px', borderWidth: '2px', borderColor: '#D8BFD8 transparent #D8BFD8 transparent' }}></div>
                            </div>
                          )}
                          {currentPhase > index && (
                            <div style={{ marginTop: '8px', fontSize: '16px', color: '#D8BFD8' }}>✓</div>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* 현재 작업 표시 */}
                    <div style={{ textAlign: 'center' }}>
                      <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>
                        현재 작업
                      </p>
                      <p style={{ fontSize: '15px', fontWeight: '500', color: '#111827' }}>
                        {currentStep || 'AI가 영상을 생성하고 있습니다...'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}

          {/* 비디오 생성 실패 */}
          {result.videoStatus === 'failed' && (
            <div className="creator-result-card result-video-section">
              <div className="creator-result-card-header">
                <h3>영상 생성 실패</h3>
              </div>
              <div className="creator-result-card-content">
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <p style={{ color: '#ef4444' }}>❌ {result.videoError || '알 수 없는 오류가 발생했습니다.'}</p>
                  <button className="btn-reset" onClick={handleReset} style={{ marginTop: '16px' }}>
                    다시 시도
                  </button>
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

          {/* 통합 태그 섹션 */}
          {result.text && (() => {
            const allTags = collectAllTags(result.text);
            if (allTags.length === 0) return null;
            return (
              <div className="creator-all-tags">
                <div className="tags-header">
                  <span className="tags-label">태그</span>
                  <button
                    className="btn-icon btn-copy-tags"
                    onClick={() => copyToClipboard(allTags.join(' '), '태그가 복사되었습니다!')}
                    title="전체 태그 복사"
                  >
                    <FiCopy />
                  </button>
                </div>
                <div className="tags-list">
                  {allTags.map((tag, idx) => (
                    <span key={idx} className="creator-tag-item hashtag">{tag}</span>
                  ))}
                </div>
              </div>
            );
          })()}

          {/* 텍스트 결과 */}
          <div className="creator-result-grid">
            <div className="result-column blog-column">
              {result.text?.blog && (
                <div className="creator-result-card" ref={blogCardRef}>
                  <div className="creator-result-card-header">
                    <h3>
                      네이버 블로그
                      {result.text?.critique?.blog?.score != null && (
                        <span className="header-score" style={{ color: getScoreColor(result.text.critique.blog.score) }}>
                          {result.text.critique.blog.score}점
                        </span>
                      )}
                    </h3>
                    <button className="btn-icon" onClick={() => handleCopyBlog({ blog: result.text.blog })} title="복사">
                      <FiCopy />
                    </button>
                  </div>
                  <div className="creator-result-card-content">
                    <div className="creator-blog-title">{result.text.blog.title}</div>
                    <div className="creator-text-result markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkBreaks]}>{result.text.blog.content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div className="result-column sns-column" ref={snsColumnRef}>
              <PlatformContent platform="sns" data={result.text?.sns} onCopy={() => handleCopySNS({ sns: result.text.sns })} score={result.text?.critique?.sns?.score} />
              <PlatformContent platform="x" data={result.text?.x} onCopy={() => handleCopyX({ x: result.text.x })} score={result.text?.critique?.x?.score} />
              <PlatformContent platform="threads" data={result.text?.threads} onCopy={() => handleCopyThreads({ threads: result.text.threads })} score={result.text?.critique?.threads?.score} />
            </div>
          </div>

          {/* 액션 버튼 */}
          <div className="creator-result-actions">
            <button className="btn-reset" onClick={handleReset}>새로 만들기</button>
            {result.text && (
              <button
                className="btn-edit-publish"
                onClick={() => navigate('/editor', { state: { result, topic } })}
              >
                <FiEdit3 /> 편집 & 발행
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

    </div>
  );
}

export default ContentCreatorSimple;
