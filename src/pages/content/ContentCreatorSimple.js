import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiCopy, FiArrowRight, FiEdit3, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import api, { contentSessionAPI, creditsAPI, userAPI, cardnewsAPI } from '../../services/api';
import { generateAgenticContent } from '../../services/agenticService';
import CreditChargeModal from '../../components/credits/CreditChargeModal';
import './ContentCreatorSimple.css';

// ========== 상수 정의 ==========
const PLATFORMS = [
  { id: 'blog', label: '블로그' },
  { id: 'sns', label: 'Instagram/Facebook' },
  { id: 'x', label: 'X' },
  { id: 'threads', label: 'Threads' },
];

const VIDEO_DURATION_OPTIONS = [
  { id: 'short', label: 'Short', duration: '15초', cuts: 3, description: '빠른 임팩트', credits: 10 },
  { id: 'standard', label: 'Standard', duration: '30초', cuts: 5, description: '균형잡힌 구성', credits: 20 },
  { id: 'premium', label: 'Premium', duration: '60초', cuts: 8, description: '상세한 스토리', credits: 35 },
];

// 크레딧 비용 상수
const CREDIT_COSTS = {
  ai_image: 2,      // AI 이미지 1장당
  cardnews: 5,      // 카드뉴스 생성
};

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

const ASPECT_RATIOS = [
  { id: '1:1', label: '정방형 (1:1)', desc: '인스타그램 피드' },
  { id: '3:4', label: '세로형 (3:4)', desc: '인스타그램 릴스' },
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
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [imageCount, setImageCount] = useState(1);
  const [imageFormat, setImageFormat] = useState('ai-image'); // 'ai-image' | 'cardnews'
  const [uploadedImages, setUploadedImages] = useState([]);
  const [videoDuration, setVideoDuration] = useState('standard');
  const [designTemplate, setDesignTemplate] = useState('minimal_white'); // 카드뉴스 디자인 템플릿
  const [designTemplates, setDesignTemplates] = useState([]); // 사용 가능한 템플릿 목록 (호환성 유지)
  const [templateCategories, setTemplateCategories] = useState([]); // 카테고리별 그룹화된 템플릿
  const [selectedCategory, setSelectedCategory] = useState(null); // 선택된 카테고리
  const [previewSlide, setPreviewSlide] = useState(0); // 템플릿 미리보기 슬라이드 (0: 표지, 1: 내용)
  const [aspectRatio, setAspectRatio] = useState('1:1'); // 이미지 비율

  // 생성 상태
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState('');
  const [result, setResult] = useState(null);

  // 팝업 상태
  const [popupImage, setPopupImage] = useState(null);

  // 크레딧 관련 상태
  const [creditBalance, setCreditBalance] = useState(0);
  const [isChargeModalOpen, setIsChargeModalOpen] = useState(false);

  // 사용자 컨텍스트 (온보딩 정보)
  const [userContext, setUserContext] = useState(null);

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

  // 크레딧 잔액 및 사용자 컨텍스트 조회
  useEffect(() => {
    const fetchCreditBalance = async () => {
      try {
        const data = await creditsAPI.getBalance();
        setCreditBalance(data.balance);
      } catch (error) {
        console.error('크레딧 잔액 조회 실패:', error);
      }
    };

    const fetchUserContext = async () => {
      try {
        const data = await userAPI.getContext();
        setUserContext(data.context);
        console.log('✅ 사용자 컨텍스트 로드:', data.context);
      } catch (error) {
        console.error('사용자 컨텍스트 조회 실패:', error);
      }
    };

    fetchCreditBalance();
    fetchUserContext();
  }, []);

  // 디자인 템플릿 목록 조회 (카테고리별 - 새 템플릿 시스템만 사용)
  useEffect(() => {
    const fetchDesignTemplates = async () => {
      try {
        // 카테고리별 그룹화된 템플릿 로드
        const v2Data = await cardnewsAPI.getDesignTemplatesV2();
        if (v2Data.success && v2Data.categories) {
          setTemplateCategories(v2Data.categories);
          // 첫 번째 카테고리만 선택 (템플릿은 선택하지 않음 - 자동 선택 모드)
          if (v2Data.categories.length > 0) {
            setSelectedCategory(v2Data.categories[0].id);
          }
          // 전체 템플릿 목록도 설정 (미리보기용)
          const allTemplates = v2Data.categories.flatMap(cat => cat.templates);
          setDesignTemplates(allTemplates);
          console.log('✅ 카테고리별 템플릿 로드:', v2Data.total_templates, '개');
        }
      } catch (error) {
        console.error('디자인 템플릿 조회 실패:', error);
      }
    };

    fetchDesignTemplates();
  }, []);

  // 필요한 크레딧 계산
  const calculateRequiredCredits = () => {
    if (contentType === 'shortform') {
      const option = VIDEO_DURATION_OPTIONS.find(o => o.id === videoDuration);
      return option?.credits || 0;
    }
    if (contentType === 'image' || contentType === 'both') {
      if (imageFormat === 'cardnews') {
        return CREDIT_COSTS.cardnews;
      }
      return CREDIT_COSTS.ai_image * imageCount;
    }
    return 0; // 텍스트만 생성은 무료
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

    // 크레딧 필요량 계산 및 체크
    const requiredCredits = calculateRequiredCredits();
    if (requiredCredits > 0) {
      if (creditBalance < requiredCredits) {
        const shortage = requiredCredits - creditBalance;
        const confirmCharge = window.confirm(
          `크레딧이 부족합니다.\n\n필요: ${requiredCredits} 크레딧\n보유: ${creditBalance} 크레딧\n부족: ${shortage} 크레딧\n\n충전 페이지로 이동하시겠습니까?`
        );
        if (confirmCharge) {
          setIsChargeModalOpen(true);
        }
        return;
      }
    }

    setIsGenerating(true);
    setResult(null);
    setProgress('콘텐츠 생성 준비 중...');

    try {
      const generatedResult = { text: null, images: [] };

      // 글 생성
      if (contentType === 'text' || contentType === 'both') {
        setProgress('AI가 글을 작성하고 있습니다...');
        const agenticResult = await generateAgenticContent(
          {
            textInput: topic,
            images: [],
            styleTone: '친근하고 편안한 말투로',
            selectedPlatforms,
            userContext  // 온보딩에서 수집한 사용자 정보 전달
          },
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
        };
      }

      // 이미지 생성
      if (contentType === 'image' || contentType === 'both') {
        if (imageFormat === 'cardnews') {
          // 카드뉴스 생성
          setProgress('AI가 카드뉴스를 생성하고 있습니다...');
          try {
            const colorTheme = 'warm';

            // FormData 생성 (백엔드가 Form 데이터를 받음)
            const formData = new FormData();
            formData.append('prompt', topic);
            formData.append('purpose', 'info');
            formData.append('fontStyle', 'pretendard');
            formData.append('colorTheme', colorTheme);
            formData.append('generateImages', 'true');
            // 디자인 템플릿 추가 ('none'이면 템플릿 없이 AI 이미지만)
            formData.append('designTemplate', designTemplate);
            formData.append('aspectRatio', aspectRatio); // 이미지 비율 추가
            // 사용자 컨텍스트 전달
            if (userContext) {
              formData.append('userContext', JSON.stringify(userContext));
            }

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
          for (let i = 0; i < imageCount; i++) {
            setProgress(`AI가 이미지를 생성하고 있습니다... (${i + 1}/${imageCount})`);
            try {
              const imageResponse = await api.post('/api/generate-image', { prompt: topic, model: 'nanobanana' });
              if (imageResponse.data.imageUrl) {
                generatedResult.images.push({ url: imageResponse.data.imageUrl, prompt: topic });
              }
            } catch (imgError) {
              console.error(`이미지 ${i + 1} 생성 실패:`, imgError);
            }
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
        }, imageUrls, platforms, null, contentType, imageCount);
      }

      // 크레딧 차감 (이미지/카드뉴스 생성 성공 시)
      if (requiredCredits > 0 && generatedResult.images?.length > 0) {
        try {
          let description = '';
          let referenceType = '';

          if (imageFormat === 'cardnews') {
            description = `카드뉴스 생성 (${generatedResult.images.length}장)`;
            referenceType = 'cardnews';
          } else if (contentType === 'shortform') {
            const option = VIDEO_DURATION_OPTIONS.find(o => o.id === videoDuration);
            description = `숏폼 영상 생성 (${option?.duration || videoDuration})`;
            referenceType = 'video_generation';
          } else {
            description = `AI 이미지 생성 (${generatedResult.images.length}장)`;
            referenceType = 'image_generation';
          }

          await creditsAPI.use(requiredCredits, description, referenceType);
          // 잔액 업데이트
          setCreditBalance(prev => prev - requiredCredits);
          console.log(`✅ 크레딧 ${requiredCredits} 차감 완료`);
        } catch (creditError) {
          console.error('크레딧 차감 실패:', creditError);
          // 크레딧 차감 실패해도 생성은 완료된 것으로 처리
        }
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
                    <>
                      생성하기 <FiArrowRight className="btn-arrow" />
                      {calculateRequiredCredits() > 0 && (
                        <span className="credit-cost-badge">
                          {calculateRequiredCredits()} 크레딧
                        </span>
                      )}
                    </>
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

                  {/* 이미지 비율 선택 - 카드뉴스 선택 시 */}
                  {contentType === 'image' && imageFormat === 'cardnews' && (
                    <div className="creator-option-section">
                      <label className="creator-label">이미지 비율</label>
                      <div className="creator-chips">
                        {ASPECT_RATIOS.map(ratio => (
                          <button
                            key={ratio.id}
                            className={`creator-chip ${aspectRatio === ratio.id ? 'selected' : ''}`}
                            onClick={() => setAspectRatio(ratio.id)}
                            title={ratio.desc}
                          >
                            {ratio.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 디자인 템플릿 선택 - 카드뉴스 선택 시 */}
                  {contentType === 'image' && imageFormat === 'cardnews' && templateCategories.length > 0 && (
                    <div className="creator-option-section">
                      <label className="creator-label">디자인 템플릿</label>

                      {/* 카테고리 탭 + 선택 안함 */}
                      <div className="template-category-tabs">
                        {/* 선택 안함 옵션 */}
                        <button
                          className={`category-tab no-template-tab ${designTemplate === 'none' ? 'active' : ''}`}
                          onClick={() => setDesignTemplate('none')}
                          title="템플릿 없이 AI 이미지와 텍스트만 사용합니다"
                        >
                          <span className="category-icon">🖼️</span>
                          <span className="category-name">선택 안함</span>
                        </button>
                        {templateCategories.map(category => (
                          <button
                            key={category.id}
                            className={`category-tab ${selectedCategory === category.id && designTemplate !== 'none' ? 'active' : ''}`}
                            onClick={() => {
                              setSelectedCategory(category.id);
                              // 선택 안함 상태에서 카테고리 클릭 시 해당 카테고리의 첫 템플릿 선택
                              if (designTemplate === 'none') {
                                const firstTemplate = category.templates?.[0];
                                if (firstTemplate) setDesignTemplate(firstTemplate.id);
                              }
                            }}
                            title={category.description}
                          >
                            <span className="category-icon">{category.icon}</span>
                            <span className="category-name">{category.name}</span>
                          </button>
                        ))}
                      </div>

                      {/* 선택된 카테고리의 템플릿 그리드 (선택 안함이 아닐 때만 표시) */}
                      {designTemplate !== 'none' && (
                      <div className="creator-template-grid">
                        {templateCategories
                          .find(cat => cat.id === selectedCategory)
                          ?.templates.map(template => (
                            <button
                              key={template.id}
                              className={`creator-template-card ${designTemplate === template.id ? 'selected' : ''}`}
                              onClick={() => setDesignTemplate(template.id)}
                              title={template.description}
                            >
                              <span
                                className="template-color-preview"
                                style={{ backgroundColor: template.preview_color }}
                              />
                              <span className="template-name">{template.name}</span>
                            </button>
                          ))}
                      </div>
                      )}

                      {/* 선택된 템플릿 미리보기 - 이미지 슬라이더 (선택 안함일 때는 표시 안함) */}
                      {designTemplate && designTemplate !== 'none' && (() => {
                        const selectedTemplate = designTemplates.find(t => t.id === designTemplate);
                        const previewImages = selectedTemplate?.preview_images;
                        const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

                        return (
                        <div className="template-preview-section">
                          <label className="creator-label">미리보기</label>
                          <div className="template-preview-slider">
                            {/* 좌측 화살표 */}
                            <button
                              className="preview-nav-btn prev"
                              onClick={() => setPreviewSlide(prev => prev === 0 ? 1 : 0)}
                              aria-label="이전 슬라이드"
                            >
                              <FiChevronLeft />
                            </button>

                            {/* 슬라이드 컨테이너 */}
                            <div className="preview-slides-container">
                              <div className="preview-slides" style={{ transform: `translateX(-${previewSlide * 100}%)` }}>
                                {/* 슬라이드 1: 표지 이미지 */}
                                <div className="preview-slide">
                                  <div className="template-preview-card template-preview-image">
                                    {previewImages?.cover ? (
                                      <img
                                        src={`${apiBaseUrl}${previewImages.cover}`}
                                        alt={`${selectedTemplate?.name} 표지`}
                                        className="preview-img"
                                      />
                                    ) : (
                                      <div className="preview-placeholder">
                                        미리보기 없음
                                      </div>
                                    )}
                                  </div>
                                  <span className="slide-label">표지</span>
                                </div>

                                {/* 슬라이드 2: 내용 페이지 이미지 */}
                                <div className="preview-slide">
                                  <div className="template-preview-card template-preview-image">
                                    {previewImages?.content ? (
                                      <img
                                        src={`${apiBaseUrl}${previewImages.content}`}
                                        alt={`${selectedTemplate?.name} 내용`}
                                        className="preview-img"
                                      />
                                    ) : (
                                      <div className="preview-placeholder">
                                        미리보기 없음
                                      </div>
                                    )}
                                  </div>
                                  <span className="slide-label">내용</span>
                                </div>
                              </div>
                            </div>

                            {/* 우측 화살표 */}
                            <button
                              className="preview-nav-btn next"
                              onClick={() => setPreviewSlide(prev => prev === 1 ? 0 : 1)}
                              aria-label="다음 슬라이드"
                            >
                              <FiChevronRight />
                            </button>
                          </div>

                          {/* 슬라이드 인디케이터 */}
                          <div className="preview-indicators">
                            <button
                              className={`indicator ${previewSlide === 0 ? 'active' : ''}`}
                              onClick={() => setPreviewSlide(0)}
                              aria-label="표지 보기"
                            />
                            <button
                              className={`indicator ${previewSlide === 1 ? 'active' : ''}`}
                              onClick={() => setPreviewSlide(1)}
                              aria-label="내용 보기"
                            />
                          </div>

                          <p className="template-description-text">
                            {selectedTemplate?.description}
                          </p>
                        </div>
                        );
                      })()}
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

      {/* 크레딧 충전 모달 */}
      <CreditChargeModal
        isOpen={isChargeModalOpen}
        onClose={() => setIsChargeModalOpen(false)}
        onChargeComplete={() => {
          // 충전 완료 후 잔액 다시 조회
          creditsAPI.getBalance().then(data => setCreditBalance(data.balance));
        }}
      />

    </div>
  );
}

export default ContentCreatorSimple;
