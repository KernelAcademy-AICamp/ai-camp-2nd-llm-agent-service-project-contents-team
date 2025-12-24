import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { FiCopy, FiArrowRight, FiEdit3, FiChevronLeft, FiChevronRight, FiPlus, FiTrash2, FiMove } from 'react-icons/fi';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import api, { contentSessionAPI, creditsAPI, userAPI, cardnewsAPI } from '../../services/api';
import { generateAgenticContent } from '../../services/agenticService';
import { useVideoJob } from '../../contexts/VideoJobContext';
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
  { id: 'short', label: 'Short', duration: '15초', cuts: 4, description: '빠른 임팩트', credits: 10 },
  { id: 'standard', label: 'Standard', duration: '25초', cuts: 6, description: '균형잡힌 구성', credits: 20 },
  { id: 'premium', label: 'Premium', duration: '40초', cuts: 8, description: '상세한 스토리', credits: 35 },
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
  { id: '1:1', label: '정사각형 (1:1)', desc: '인스타그램 피드' },
  { id: '4:5', label: '세로형 (4:5)', desc: '인스타그램 세로 피드' },
  { id: '1.91:1', label: '가로형 (1.91:1)', desc: '페이스북, 트위터' },
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
  const location = useLocation();

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

  // 카드뉴스 텍스트 미리보기 상태
  const [cardnewsPreview, setCardnewsPreview] = useState(null); // 미리보기 데이터
  const [isPreviewMode, setIsPreviewMode] = useState(false); // 미리보기 모드 여부
  const [editingPageIndex, setEditingPageIndex] = useState(null); // 현재 편집 중인 페이지 인덱스

  // 생성 상태
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState('');
  const [result, setResult] = useState(null);
  const hasSavedRef = useRef(false); // 현재 생성 결과 저장 여부 추적

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
      } catch (error) {
        console.error('사용자 컨텍스트 조회 실패:', error);
      }
    };

    fetchCreditBalance();
    fetchUserContext();
  }, []);

  // 템플릿에서 넘어온 경우 데이터 설정
  useEffect(() => {
    if (location.state?.fromTemplate && location.state?.template) {
      const template = location.state.template;
      // 템플릿의 프롬프트를 topic에 설정
      setTopic(template.prompt || template.name || '');
      // 기본 콘텐츠 타입 설정 (글+이미지 추천)
      setContentType('both');
      // 기본 플랫폼 설정
      setSelectedPlatforms(['blog', 'sns']);
      // 이미지 형태 기본값 설정
      setImageFormat('ai-image');
      setImageCount(1);

      // state 정리 (뒤로가기 시 중복 적용 방지)
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

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
    // 이미 저장된 경우 스킵
    if (hasSavedRef.current) {
      console.log('이미 저장됨, 중복 저장 스킵');
      return;
    }

    // 저장할 콘텐츠가 없으면 스킵
    if (!content.blog && !content.sns && !content.x && !content.threads) {
      console.log('저장할 콘텐츠가 없음, 스킵');
      return;
    }

    // 플랫폼이 선택되지 않았으면 스킵
    if (!platforms || platforms.length === 0) {
      console.log('선택된 플랫폼이 없음, 스킵');
      return;
    }

    try {
      // Base64 이미지가 너무 크면 저장하지 않음 (URL만 저장)
      const processedImageUrls = imageUrls.map(url => {
        // Base64 이미지인 경우 크기 체크 (1MB 이상이면 저장 스킵)
        if (url && url.startsWith('data:') && url.length > 1000000) {
          console.warn('이미지가 너무 커서 저장을 건너뜁니다.');
          return null;
        }
        return url;
      }).filter(Boolean);

      // 이미지 데이터 준비 (빈 배열이면 null로 처리)
      const imageData = processedImageUrls.length > 0
        ? processedImageUrls.map(url => ({ image_url: url, prompt: topic }))
        : null;

      const saveData = {
        topic,
        content_type: currentContentType,
        style: currentStyle || 'default',
        selected_platforms: platforms,
        blog: content.blog ? { title: content.blog.title || '제목 없음', content: content.blog.content || '', tags: content.blog.tags || [], score: content.critique?.blog?.score || null } : null,
        sns: content.sns ? { content: content.sns.content || '', hashtags: content.sns.tags || content.sns.hashtags || [], score: content.critique?.sns?.score || null } : null,
        x: content.x ? { content: content.x.content || '', hashtags: content.x.tags || content.x.hashtags || [], score: content.critique?.x?.score || null } : null,
        threads: content.threads ? { content: content.threads.content || '', hashtags: content.threads.tags || content.threads.hashtags || [], score: content.critique?.threads?.score || null } : null,
        images: imageData,
        requested_image_count: requestedImageCount || 0,
        analysis_data: content.analysis || null,
        critique_data: content.critique || null,
        generation_attempts: content.metadata?.attempts || 1
      };

      await contentSessionAPI.save(saveData);
      hasSavedRef.current = true; // 저장 성공 표시
      console.log('콘텐츠 저장 성공');
    } catch (error) {
      // 저장 실패해도 사용자 경험에 영향 없이 조용히 실패
      console.error('콘텐츠 저장 실패:', error);
      if (error.response?.data) {
        console.error('서버 응답:', error.response.data);
      }
      // 에러가 발생해도 hasSavedRef는 false로 유지하여 재시도 가능
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
    hasSavedRef.current = false; // 새 생성 시 저장 상태 초기화

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
          // 카드뉴스 생성 - 1단계: 텍스트 + 이미지 미리보기 생성
          setProgress('AI가 카드뉴스 내용과 이미지를 생성하고 있습니다...');
          try {
            // FormData 생성 (텍스트 + 이미지 미리보기 API 호출)
            const previewFormData = new FormData();
            previewFormData.append('prompt', topic);
            previewFormData.append('purpose', 'info');
            previewFormData.append('generateImages', 'true');  // 이미지도 함께 생성
            previewFormData.append('fontStyle', 'pretendard');
            previewFormData.append('colorTheme', 'warm');
            previewFormData.append('designTemplate', 'none');
            previewFormData.append('aspectRatio', aspectRatio);  // 선택한 비율 전달
            if (userContext) {
              previewFormData.append('userContext', JSON.stringify(userContext));
            }

            const previewResponse = await api.post('/api/preview-cardnews-content', previewFormData, {
              headers: {
                'Content-Type': 'multipart/form-data',
              },
            });

            if (previewResponse.data.success && previewResponse.data.pages) {
              // 미리보기 모드로 전환 (이미지 포함)
              setCardnewsPreview({
                pages: previewResponse.data.pages,
                preview_images: previewResponse.data.preview_images || [],
                analysis: previewResponse.data.analysis,
                design_settings: previewResponse.data.design_settings,
                prompt: topic  // 원본 프롬프트 저장
              });
              setIsPreviewMode(true);
              setIsGenerating(false);
              setProgress('');
              return; // 여기서 중단하고 사용자 확인을 기다림
            }
          } catch (cardnewsError) {
            console.error('카드뉴스 미리보기 생성 실패:', cardnewsError);
            alert('카드뉴스 내용 생성 중 오류가 발생했습니다.');
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

            // 작업 상태를 주기적으로 확인하는 폴링
            const checkVideoStatus = async () => {
              try {
                const statusResponse = await api.get(`/api/ai-video/jobs/${jobId}`);
                const job = statusResponse.data;

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
        }, imageUrls, platforms, 'default', contentType, imageCount);
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
    setCardnewsPreview(null);
    setIsPreviewMode(false);
    setEditingPageIndex(null);
  };

  // ========== 카드뉴스 미리보기 관련 함수 ==========

  // 페이지 내용 수정
  const handlePageEdit = (pageIndex, field, value) => {
    if (!cardnewsPreview) return;

    const updatedPages = [...cardnewsPreview.pages];
    if (field === 'content') {
      // content는 배열이므로 문자열을 배열로 변환 (입력 중에는 빈 줄 유지)
      updatedPages[pageIndex] = {
        ...updatedPages[pageIndex],
        content: value.split('\n')
      };
    } else {
      updatedPages[pageIndex] = {
        ...updatedPages[pageIndex],
        [field]: value
      };
    }

    setCardnewsPreview({
      ...cardnewsPreview,
      pages: updatedPages
    });
  };

  // 페이지 추가
  const handleAddPage = (afterIndex) => {
    if (!cardnewsPreview) return;

    const newPage = {
      title: '새 페이지',
      content: ['내용을 입력하세요']
    };

    const updatedPages = [...cardnewsPreview.pages];
    updatedPages.splice(afterIndex + 1, 0, newPage);

    setCardnewsPreview({
      ...cardnewsPreview,
      pages: updatedPages
    });

    // 새로 추가된 페이지를 편집 모드로 전환
    setEditingPageIndex(afterIndex + 1);
  };

  // 페이지 삭제
  const handleDeletePage = (pageIndex) => {
    if (!cardnewsPreview) return;

    // 최소 2장은 유지 (표지 + 내용 1장)
    if (cardnewsPreview.pages.length <= 2) {
      alert('카드뉴스는 최소 2장 이상이어야 합니다.');
      return;
    }

    // 표지(0번 페이지)는 삭제 불가
    if (pageIndex === 0) {
      alert('표지는 삭제할 수 없습니다.');
      return;
    }

    if (!window.confirm(`${pageIndex}페이지를 삭제하시겠습니까?`)) {
      return;
    }

    const updatedPages = cardnewsPreview.pages.filter((_, idx) => idx !== pageIndex);

    setCardnewsPreview({
      ...cardnewsPreview,
      pages: updatedPages
    });

    // 편집 중인 페이지가 삭제되면 편집 모드 해제
    if (editingPageIndex === pageIndex) {
      setEditingPageIndex(null);
    } else if (editingPageIndex > pageIndex) {
      // 삭제된 페이지보다 뒤에 있는 페이지를 편집 중이면 인덱스 조정
      setEditingPageIndex(editingPageIndex - 1);
    }
  };

  // 페이지 순서 변경 (드래그 앤 드롭)
  const handleDragEnd = (result) => {
    if (!cardnewsPreview) return;

    const { destination, source } = result;

    // 드롭 대상이 없거나 같은 위치면 무시
    if (!destination) return;
    if (destination.index === source.index) return;

    // 표지(0번)는 이동 불가
    if (source.index === 0 || destination.index === 0) {
      return;
    }

    const updatedPages = Array.from(cardnewsPreview.pages);
    const [movedPage] = updatedPages.splice(source.index, 1);
    updatedPages.splice(destination.index, 0, movedPage);

    setCardnewsPreview({
      ...cardnewsPreview,
      pages: updatedPages
    });

    // 편집 중인 페이지 인덱스도 조정
    if (editingPageIndex !== null) {
      if (editingPageIndex === source.index) {
        setEditingPageIndex(destination.index);
      } else if (source.index < editingPageIndex && destination.index >= editingPageIndex) {
        setEditingPageIndex(editingPageIndex - 1);
      } else if (source.index > editingPageIndex && destination.index <= editingPageIndex) {
        setEditingPageIndex(editingPageIndex + 1);
      }
    }
  };

  // 미리보기 취소
  const handleCancelPreview = () => {
    setCardnewsPreview(null);
    setIsPreviewMode(false);
    setEditingPageIndex(null);
  };

  // 미리보기 확정 및 이미지 생성
  const handleConfirmPreview = async () => {
    if (!cardnewsPreview) return;

    setIsGenerating(true);
    setProgress('카드뉴스 이미지를 생성하고 있습니다...');

    try {
      const colorTheme = 'warm';

      // 빈 줄 필터링된 페이지 데이터 생성
      const cleanedPages = cardnewsPreview.pages.map(page => ({
        ...page,
        content: (page.content || []).filter(line => line.trim())
      }));

      // FormData 생성 (확정된 내용으로 이미지 생성)
      const formData = new FormData();
      formData.append('pages', JSON.stringify(cleanedPages));
      formData.append('prompt', cardnewsPreview.prompt);
      formData.append('purpose', 'info');
      formData.append('fontStyle', cardnewsPreview.design_settings?.font_pair || 'pretendard');
      formData.append('colorTheme', colorTheme);
      formData.append('designTemplate', designTemplate);
      formData.append('aspectRatio', aspectRatio);

      // 미리보기에서 생성된 배경 이미지가 있으면 전달 (재사용)
      if (cardnewsPreview.background_images && cardnewsPreview.background_images.length > 0) {
        formData.append('previewImages', JSON.stringify(cardnewsPreview.background_images));
      }

      const cardnewsResponse = await api.post('/api/generate-cardnews-from-content', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (cardnewsResponse.data.success && cardnewsResponse.data.cards) {
        const generatedResult = { text: null, images: [] };

        cardnewsResponse.data.cards.forEach((card, index) => {
          generatedResult.images.push({
            url: card,
            prompt: `${cardnewsPreview.prompt} - 카드 ${index + 1}`
          });
        });

        // 크레딧 차감
        const requiredCredits = CREDIT_COSTS.cardnews;
        if (requiredCredits > 0) {
          try {
            await creditsAPI.use(requiredCredits, '카드뉴스 생성', 'cardnews_generation');
            setCreditBalance(prev => prev - requiredCredits);
          } catch (creditError) {
            console.error('크레딧 차감 실패:', creditError);
          }
        }

        setResult(generatedResult);
        setCardnewsPreview(null);
        setIsPreviewMode(false);
        setEditingPageIndex(null);
        setProgress(`카드뉴스 ${cardnewsResponse.data.cards.length}장 생성 완료!`);
      }
    } catch (error) {
      console.error('카드뉴스 이미지 생성 실패:', error);
      alert('카드뉴스 이미지 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGenerating(false);
      setProgress('');
    }
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
      {/* 카드뉴스 텍스트 미리보기 모드 */}
      {isPreviewMode && cardnewsPreview ? (
        <div className="creator-container">
          <div className="page-header">
            <h2>카드뉴스 내용 확인</h2>
            <p className="page-description">AI가 생성한 내용을 확인하고 수정한 후 이미지로 변환합니다</p>
          </div>

          <div className="cardnews-preview-container">
            {/* 미리보기 헤더 */}
            <div className="preview-header">
              <div className="preview-info">
                <span className="preview-badge">📝 미리보기</span>
                <span className="preview-count">{cardnewsPreview.pages.length}장의 카드뉴스</span>
              </div>
              <div className="preview-actions">
                <button
                  className="preview-cancel-btn"
                  onClick={handleCancelPreview}
                  disabled={isGenerating}
                >
                  취소
                </button>
                <button
                  className="preview-confirm-btn"
                  onClick={handleConfirmPreview}
                  disabled={isGenerating}
                >
                  {isGenerating ? (
                    <><span className="spinner"></span>{progress}</>
                  ) : (
                    <>이미지 생성하기 <FiArrowRight /></>
                  )}
                </button>
              </div>
            </div>

            {/* 페이지별 편집 카드 */}
            <DragDropContext onDragEnd={handleDragEnd}>
              <Droppable droppableId="cardnews-pages" direction="vertical">
                {(provided) => (
                  <div
                    className="preview-pages"
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                  >
                    {cardnewsPreview.pages.map((page, index) => (
                      <Draggable
                        key={`page-${index}`}
                        draggableId={`page-${index}`}
                        index={index}
                        isDragDisabled={index === 0}
                      >
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            className={`preview-page-card ${editingPageIndex === index ? 'editing' : ''} ${snapshot.isDragging ? 'dragging' : ''}`}
                          >
                            <div className="page-card-header">
                              <div className="page-header-left">
                                {index > 0 && (
                                  <span
                                    className="drag-handle"
                                    {...provided.dragHandleProps}
                                    title="드래그하여 순서 변경"
                                  >
                                    <FiMove />
                                  </span>
                                )}
                                <span className="preview-page-label">
                                  {index === 0 ? '📌 표지' : `📄 ${index}페이지`}
                                </span>
                              </div>
                              <div className="page-card-actions">
                                <button
                                  className="page-edit-btn"
                                  onClick={() => setEditingPageIndex(editingPageIndex === index ? null : index)}
                                >
                                  <FiEdit3 /> {editingPageIndex === index ? '완료' : '수정'}
                                </button>
                                {index > 0 && (
                                  <button
                                    className="page-delete-btn"
                                    onClick={() => handleDeletePage(index)}
                                    title="페이지 삭제"
                                  >
                                    <FiTrash2 />
                                  </button>
                                )}
                              </div>
                            </div>

                            {editingPageIndex === index ? (
                              // 편집 모드
                              <div className="page-edit-form">
                                <div className="edit-field">
                                  <label>제목</label>
                                  <input
                                    type="text"
                                    value={page.title}
                                    onChange={(e) => handlePageEdit(index, 'title', e.target.value)}
                                    onKeyDown={(e) => e.stopPropagation()}
                                    placeholder="제목을 입력하세요"
                                  />
                                </div>
                                {index === 0 && (
                                  <div className="edit-field">
                                    <label>소제목</label>
                                    <textarea
                                      value={page.subtitle || ''}
                                      onChange={(e) => handlePageEdit(index, 'subtitle', e.target.value)}
                                      onKeyDown={(e) => e.stopPropagation()}
                                      placeholder="소제목을 입력하세요"
                                      rows={3}
                                    />
                                  </div>
                                )}
                                <div className="edit-field">
                                  <label>{index === 0 ? '내용 (선택사항)' : '내용'} (줄바꿈으로 구분)</label>
                                  <textarea
                                    value={(page.content || []).join('\n')}
                                    onChange={(e) => handlePageEdit(index, 'content', e.target.value)}
                                    onKeyDown={(e) => e.stopPropagation()}
                                    placeholder="• 내용 1&#10;• 내용 2&#10;• 내용 3"
                                    rows={6}
                                  />
                                </div>
                              </div>
                            ) : (
                              // 미리보기 모드 (이미지 + 텍스트)
                              <div className="page-preview-content">
                                {/* 이미지 미리보기 */}
                                {cardnewsPreview.preview_images && cardnewsPreview.preview_images[index] && (
                                  <div className="preview-image-container">
                                    <img
                                      src={cardnewsPreview.preview_images[index]}
                                      alt={`페이지 ${index + 1} 미리보기`}
                                      className="preview-card-image"
                                    />
                                  </div>
                                )}
                                {/* 텍스트 미리보기 */}
                                <div className="preview-text-content">
                                  <h4 className="preview-title">{page.title}</h4>
                                  {page.subtitle && (
                                    <p className="preview-subtitle">{page.subtitle}</p>
                                  )}
                                  {page.content && page.content.length > 0 && (
                                    <ul className="preview-content-list">
                                      {page.content.map((item, i) => (
                                        <li key={i}>{item}</li>
                                      ))}
                                    </ul>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}

                    {/* 카드 추가 버튼 */}
                    <button
                      className="add-page-card"
                      onClick={() => handleAddPage(cardnewsPreview.pages.length - 1)}
                    >
                      <FiPlus />
                      <span>페이지 추가</span>
                    </button>
                  </div>
                )}
              </Droppable>
            </DragDropContext>

            {/* 하단 안내 */}
            <div className="preview-footer">
              <p className="preview-tip">
                💡 카드를 드래그하여 순서를 변경할 수 있습니다. '수정' 버튼으로 내용을 편집하세요.
              </p>
            </div>
          </div>
        </div>
      ) : !result ? (
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
                      className={`creator-type-card ${contentType === type.id ? 'selected' : ''} ${isGenerating ? 'disabled' : ''}`}
                      onClick={() => !isGenerating && setContentType(type.id)}
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
                  disabled={isGenerating}
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
                  <button key={t} className="quick-chip" onClick={() => setTopic(t)} disabled={isGenerating}>{t}</button>
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
                            disabled={isGenerating}
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
                            disabled={isGenerating}
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
                          disabled={isGenerating}
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
                            disabled={isGenerating}
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
                              disabled={isGenerating}
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
                            disabled={isGenerating}
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
                            disabled={isGenerating}
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
                      <div className={`creator-upload-area ${isGenerating ? 'disabled' : ''}`}>
                        {uploadedImages.length === 0 ? (
                          <label className={`upload-label ${isGenerating ? 'disabled' : ''}`}>
                            <input type="file" accept="image/*" onChange={handleImageUpload} className="file-input" disabled={isGenerating} />
                            <span className="upload-icon">📸</span>
                            <span>클릭하여 이미지 업로드</span>
                            <span className="upload-hint">PNG, JPG, WebP (최대 10MB)</span>
                          </label>
                        ) : (
                          <div className="uploaded-preview">
                            <img src={uploadedImages[0].preview} alt="업로드된 이미지" />
                            <button type="button" className="btn-remove" onClick={() => setUploadedImages([])} disabled={isGenerating}>✕</button>
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
                            className={`creator-duration-card ${videoDuration === option.id ? 'selected' : ''} ${isGenerating ? 'disabled' : ''}`}
                            onClick={() => !isGenerating && setVideoDuration(option.id)}
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

            // 1단계: 스토리보드 생성 (4 Agents 포함)
            if (currentStep.includes('1단계') || currentStep.includes('제품 분석') || currentStep.includes('로딩')) {
              currentPhase = 0;
              progressPercent = 5;
            } else if (currentStep.includes('2단계') || currentStep.includes('스토리 기획')) {
              currentPhase = 0;
              progressPercent = 10;
            } else if (currentStep.includes('3단계') || currentStep.includes('장면 연출')) {
              currentPhase = 0;
              progressPercent = 15;
            } else if (currentStep.includes('4단계') || currentStep.includes('품질 검증')) {
              currentPhase = 0;
              progressPercent = 20;
            } else if (currentStep.includes('Generating image') || currentStep.includes('이미지')) {
              // 2단계: 이미지 생성
              currentPhase = 1;
              const match = currentStep.match(/(\d+)\/(\d+)/);
              if (match) {
                const current = parseInt(match[1]);
                const total = parseInt(match[2]);
                progressPercent = 25 + (current / total) * 25;
              } else {
                progressPercent = 30;
              }
            } else if (currentStep.includes('transition') || currentStep.includes('Kling') || currentStep.includes('Veo')) {
              // 3단계: 전환 비디오 생성
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
              // 4단계: 최종 합성
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

                    {/* 다른 기능 둘러보기 버튼 */}
                    <div style={{ textAlign: 'center', marginTop: '32px' }}>
                      <p style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '12px' }}>
                        영상 생성은 백그라운드에서 계속 진행됩니다
                      </p>
                      <button
                        onClick={() => {
                          // VideoJobContext에 작업 등록 후 홈으로 이동
                          if (result.videoJobId) {
                            addJob(result.videoJobId, topic || '숏폼 영상');
                          }
                          navigate('/');
                        }}
                        style={{
                          padding: '12px 24px',
                          backgroundColor: '#f3f4f6',
                          color: '#374151',
                          border: 'none',
                          borderRadius: '8px',
                          fontSize: '14px',
                          fontWeight: '500',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease'
                        }}
                        onMouseEnter={(e) => e.target.style.backgroundColor = '#e5e7eb'}
                        onMouseLeave={(e) => e.target.style.backgroundColor = '#f3f4f6'}
                      >
                        다른 기능 둘러보기
                      </button>
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
