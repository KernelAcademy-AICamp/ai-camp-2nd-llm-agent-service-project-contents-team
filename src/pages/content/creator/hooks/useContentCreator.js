// 콘텐츠 생성기 공통 훅

import { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { creditsAPI, userAPI, cardnewsAPI, contentSessionAPI } from '../../../../services/api';
import { CREDIT_COSTS, VIDEO_DURATION_OPTIONS } from '../constants';

/**
 * 콘텐츠 생성기의 공통 상태와 로직을 관리하는 훅
 */
export const useContentCreator = () => {
  const location = useLocation();

  // 입력 상태
  const [contentType, setContentType] = useState(null);
  const [topic, setTopic] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [imageCount, setImageCount] = useState(1);
  const [imageFormat, setImageFormat] = useState('ai-image');
  const [uploadedImages, setUploadedImages] = useState([]);
  const [videoDuration, setVideoDuration] = useState('standard');
  const [designTemplate, setDesignTemplate] = useState('minimal_white');
  const [designTemplates, setDesignTemplates] = useState([]);
  const [templateCategories, setTemplateCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [previewSlide, setPreviewSlide] = useState(0);
  const [aspectRatio, setAspectRatio] = useState('1:1');

  // 카드뉴스 미리보기 상태
  const [cardnewsPreview, setCardnewsPreview] = useState(null);
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [editingPageIndex, setEditingPageIndex] = useState(null);

  // 생성 상태
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState('');
  const [result, setResult] = useState(null);
  const hasSavedRef = useRef(false);

  // 팝업 상태
  const [popupImage, setPopupImage] = useState(null);

  // 크레딧 관련 상태
  const [creditBalance, setCreditBalance] = useState(0);
  const [isChargeModalOpen, setIsChargeModalOpen] = useState(false);

  // 사용자 컨텍스트
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
      setTopic(template.prompt || template.name || '');
      setContentType('both');
      setSelectedPlatforms(['blog', 'sns']);
      setImageFormat('ai-image');
      setImageCount(1);
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  // 디자인 템플릿 목록 조회
  useEffect(() => {
    const fetchDesignTemplates = async () => {
      try {
        const v2Data = await cardnewsAPI.getDesignTemplatesV2();
        if (v2Data.success && v2Data.categories) {
          setTemplateCategories(v2Data.categories);
          if (v2Data.categories.length > 0) {
            setSelectedCategory(v2Data.categories[0].id);
          }
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
    return 0;
  };

  // 플랫폼 토글
  const togglePlatform = (platformId) => {
    if (selectedPlatforms.includes(platformId)) {
      if (selectedPlatforms.length > 1) {
        setSelectedPlatforms(prev => prev.filter(id => id !== platformId));
      }
    } else {
      setSelectedPlatforms(prev => [...prev, platformId]);
    }
  };

  // 이미지 업로드 핸들러
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

  // 이미지 다운로드
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

  // 자동 저장
  const autoSaveContent = async (content, imageUrls, platforms, currentStyle, currentContentType, requestedImageCount) => {
    if (hasSavedRef.current) {
      console.log('이미 저장됨, 중복 저장 스킵');
      return;
    }

    if (!content.blog && !content.sns && !content.x && !content.threads) {
      console.log('저장할 콘텐츠가 없음, 스킵');
      return;
    }

    if (!platforms || platforms.length === 0) {
      console.log('선택된 플랫폼이 없음, 스킵');
      return;
    }

    // 저장 시작 표시 (중복 저장 방지)
    hasSavedRef.current = true;

    try {
      // Base64 이미지를 Supabase Storage에 업로드하고 URL로 변환
      const uploadedImageUrls = [];
      for (const url of imageUrls) {
        if (url && url.startsWith('data:')) {
          // Base64 이미지 -> Supabase Storage 업로드
          try {
            console.log('이미지 Supabase Storage 업로드 중...');
            const uploadResult = await contentSessionAPI.uploadImage(url, topic);
            if (uploadResult.success && uploadResult.image_url) {
              uploadedImageUrls.push(uploadResult.image_url);
              console.log('이미지 업로드 성공:', uploadResult.image_url.substring(0, 80));
            }
          } catch (uploadError) {
            console.error('이미지 업로드 실패:', uploadError);
            // 업로드 실패해도 계속 진행
          }
        } else if (url) {
          // 이미 URL인 경우 그대로 사용
          uploadedImageUrls.push(url);
        }
      }

      const imageData = uploadedImageUrls.length > 0
        ? uploadedImageUrls.map(url => ({ image_url: url, prompt: topic }))
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
      console.log('콘텐츠 저장 성공');
    } catch (error) {
      console.error('콘텐츠 저장 실패:', error);
      if (error.response?.data) {
        console.error('서버 응답:', error.response.data);
      }
      // 저장 실패 시 다시 시도 가능하도록
      hasSavedRef.current = false;
    }
  };

  // 리셋
  const handleReset = () => {
    setResult(null);
    setTopic('');
    setProgress('');
    setCardnewsPreview(null);
    setIsPreviewMode(false);
    setEditingPageIndex(null);
  };

  // 생성 버튼 비활성화 조건
  const isGenerateDisabled = isGenerating || !topic.trim() || !contentType ||
    (contentType !== 'image' && contentType !== 'shortform' && selectedPlatforms.length === 0) ||
    (contentType === 'shortform' && uploadedImages.length === 0);

  return {
    // 상태
    contentType,
    topic,
    selectedPlatforms,
    imageCount,
    imageFormat,
    uploadedImages,
    videoDuration,
    designTemplate,
    designTemplates,
    templateCategories,
    selectedCategory,
    previewSlide,
    aspectRatio,
    cardnewsPreview,
    isPreviewMode,
    editingPageIndex,
    isGenerating,
    progress,
    result,
    hasSavedRef,
    popupImage,
    creditBalance,
    isChargeModalOpen,
    userContext,
    snsColumnRef,
    blogCardRef,
    isGenerateDisabled,

    // 상태 변경 함수
    setContentType,
    setTopic,
    setSelectedPlatforms,
    setImageCount,
    setImageFormat,
    setUploadedImages,
    setVideoDuration,
    setDesignTemplate,
    setSelectedCategory,
    setPreviewSlide,
    setAspectRatio,
    setCardnewsPreview,
    setIsPreviewMode,
    setEditingPageIndex,
    setIsGenerating,
    setProgress,
    setResult,
    setPopupImage,
    setCreditBalance,
    setIsChargeModalOpen,

    // 핸들러
    calculateRequiredCredits,
    togglePlatform,
    handleImageUpload,
    handleDownloadImage,
    handleDownloadAllImages,
    autoSaveContent,
    handleReset,
  };
};

export default useContentCreator;
