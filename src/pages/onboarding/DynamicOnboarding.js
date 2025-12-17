import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import './DynamicOnboarding.css';

// 스타일별 콘텐츠 예시
const styleExamples = {
  '따뜻한': {
    industry: '카페',
    text: '추운 겨울, 따뜻한 라떼 한 잔으로 몸과 마음을 녹여보세요. 오늘도 우리 카페에서 손님들의 웃음소리가 들려왔어요. 편안한 공간에서 잠시 쉬어가시길 바라며, 정성껏 내린 커피 한 잔 준비해두었습니다.'
  },
  '친근한': {
    industry: '반려동물 용품점',
    text: '우리 강아지가 이 간식 먹고 꼬리가 프로펠러처럼 돌아가더라구요 ㅋㅋ 여러분네 댕댕이는 어때요? 요즘 날씨 건조해서 발바닥 케어도 신경 써주셔야 해요! 궁금한 거 있으면 언제든 물어보세요~'
  },
  '전문적인': {
    industry: 'IT 보안 솔루션',
    text: '최신 암호화 기술을 적용한 엔터프라이즈급 보안 시스템을 제공합니다. ISO 27001 인증을 획득하였으며, 연간 99.9%의 가동률을 보장합니다. 전담 보안 전문가가 24시간 모니터링하여 귀사의 데이터를 안전하게 보호합니다.'
  },
  '유머러스한': {
    industry: '헬스장',
    text: '운동은 내일부터? 그 내일이 오늘입니다! 😂 PT 선생님이 \'하나만 더~\' 할 때마다 제 영혼이 빠져나가는 기분이지만, 신기하게도 몸은 좋아지더라구요. 같이 고통(?)받으실 분들 환영합니다! 첫 달 회원권 50% 할인 중!'
  },
  '진지한': {
    industry: '법률 사무소',
    text: '법적 분쟁은 신중하고 체계적인 접근이 필요합니다. 저희는 15년간 누적된 판례 연구를 바탕으로 최선의 법률 서비스를 제공합니다. 의뢰인의 권리를 지키기 위해 끝까지 책임지고 대응하겠습니다.'
  },
  '창의적인': {
    industry: '인테리어 디자인 스튜디오',
    text: '벽 하나로 공간의 분위기가 180도 바뀐다면 믿으시겠나요? 우리는 \'불가능\'이란 말 대신 \'어떻게 하면 될까?\'를 고민합니다. 당신만의 라이프스타일을 공간에 담아내는 새로운 경험, 지금 시작해보세요.'
  },
  '신뢰감있는': {
    industry: '자동차 정비소',
    text: '25년 경력의 국가공인 정비사가 직접 점검합니다. 모든 정비 과정은 고객님께 투명하게 공개되며, 정품 부품만을 사용합니다. A/S 보증서를 발급해드리고, 정비 후 3개월 무상 재점검을 약속드립니다.'
  },
  '트렌디한': {
    industry: '패션 편집샵',
    text: '요즘 인스타에서 난리난 그 브랜드, 드디어 입고됐어요! 🔥 완판 임박이니까 서두르세요! 연예인 ○○○이 착용한 바로 그 아이템! OOTD 찍기 딱 좋은 감성 가득 신상 라인업, 놓치면 후회할걸요?'
  }
};

function DynamicOnboarding() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(0); // 0: SNS 질문, 1: 비즈니스 정보, 2: 스타일, 3: 완료
  const [isLoading, setIsLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  // 온보딩 경로 선택
  const [onboardingPath, setOnboardingPath] = useState(null); // 'sns_analysis' or 'manual_input'

  // Step 1: 비즈니스 정보
  const [businessInfo, setBusinessInfo] = useState({
    brand_name: '',
    business_type: '',
    business_description: '',
    target_audience: {
      age_range: '',
      gender: 'all',
      interests: []
    },
    custom_fields: {}, // 업종별 맞춤 필드
    selected_styles: [], // 선택한 스타일 (최대 3개)
    brand_values: [] // 브랜드 가치 (최대 5개)
  });

  // 업종별 맞춤 질문
  const [customQuestions, setCustomQuestions] = useState([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);

  // AI 추천 관심사
  const [recommendedInterests, setRecommendedInterests] = useState([]);
  const [aiReasoning, setAiReasoning] = useState('');
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);

  // SNS 분석 (멀티 플랫폼)
  const [platformUrls, setPlatformUrls] = useState({
    blog: '',
    instagram: '',
    youtube: ''
  });

  // 블로그 분석 (기존 - 레거시)
  const [blogUrl, setBlogUrl] = useState('');
  const [blogAnalysisStatus, setBlogAnalysisStatus] = useState('idle'); // idle, analyzing, completed, failed
  const [blogAnalysisResult, setBlogAnalysisResult] = useState(null);

  // 멀티 플랫폼 분석 상태
  const [multiPlatformAnalysisStatus, setMultiPlatformAnalysisStatus] = useState('idle'); // idle, analyzing, completed, failed
  const [multiPlatformAnalysisResult, setMultiPlatformAnalysisResult] = useState(null);
  const [analysisProgress, setAnalysisProgress] = useState(0); // SNS 분석 진행률 (0-100)

  // YouTube 연동 상태
  const [youtubeConnection, setYoutubeConnection] = useState(null);
  const [youtubeConnectionLoading, setYoutubeConnectionLoading] = useState(false);

  // 수동 입력 분석 상태
  const [manualAnalysisStatus, setManualAnalysisStatus] = useState('idle'); // idle, analyzing, completed, failed
  const [manualAnalysisResult, setManualAnalysisResult] = useState(null);

  // Step 2: 콘텐츠 선호도
  const [preferences, setPreferences] = useState({
    text_style_sample: '',
    text_tone: 'casual',
    image_style_description: '',
    video_style_description: '',
    video_duration_preference: 'short'
  });

  // 파일 업로드 (드래그 앤 드롭) - 수동 입력 경로용 (여러 개)
  const [textSamples, setTextSamples] = useState([]); // 최소 2개
  const [imageSamples, setImageSamples] = useState([]); // 최소 2개
  const [videoSamples, setVideoSamples] = useState([]); // 최소 2개

  // 레거시 - SNS 분석 경로에서는 사용 안 함
  const [imageSample, setImageSample] = useState(null);
  const [videoSample, setVideoSample] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);
  const [dragActive, setDragActive] = useState({ image: false, video: false });

  // 관심사 입력
  const [interestInput, setInterestInput] = useState('');

  // 브랜드 가치 입력
  const [valueInput, setValueInput] = useState('');

  // 스타일 미리보기
  const [selectedStyleForPreview, setSelectedStyleForPreview] = useState(null);

  // 실시간 유효성 검사
  const [validation, setValidation] = useState({
    brand_name: { valid: false, message: '' },
    business_type: { valid: false, message: '' },
  });

  const imageInputRef = useRef(null);
  const videoInputRef = useRef(null);

  useEffect(() => {
    checkOnboardingStatus();
  }, []);

  // 업종 변경 시 맞춤 질문 로드
  useEffect(() => {
    if (businessInfo.business_type) {
      loadCustomQuestions();
    }
  }, [businessInfo.business_type]);

  // SNS 분석 진행률 자동 증가
  useEffect(() => {
    if (multiPlatformAnalysisStatus === 'analyzing') {
      const progressInterval = setInterval(() => {
        setAnalysisProgress(prev => {
          // 95%까지만 자동 증가 (완료 시 100%로 설정)
          if (prev < 95) {
            // 처음에는 빠르게, 나중에는 느리게 증가
            const increment = prev < 30 ? 2 : prev < 60 ? 1 : 0.5;
            return Math.min(prev + increment, 95);
          }
          return prev;
        });
      }, 800); // 0.8초마다 업데이트

      return () => clearInterval(progressInterval);
    }
  }, [multiPlatformAnalysisStatus]);

  // YouTube 연동 상태 확인
  useEffect(() => {
    checkYouTubeConnection();
  }, []);

  const checkOnboardingStatus = async () => {
    // 개발 모드: URL에 ?dev=true 파라미터가 있으면 리다이렉트 안함
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('dev') === 'true') {
      console.log('개발 모드: 온보딩 리다이렉트 비활성화');
      return;
    }

    try {
      const response = await api.get('/api/onboarding/status');
      if (response.data.onboarding_completed) {
        navigate('/content');
      }
    } catch (error) {
      console.error('온보딩 상태 확인 실패:', error);
    }
  };

  // YouTube 연동 상태 확인
  const checkYouTubeConnection = async () => {
    try {
      const response = await api.get('/api/youtube/status');
      if (response.data) {
        setYoutubeConnection(response.data);
        // YouTube 연동되어 있으면 platformUrls에 표시
        setPlatformUrls(prev => ({ ...prev, youtube: 'connected' }));
      }
    } catch (error) {
      console.log('YouTube 연동 없음:', error.response?.status === 404 ? '연동되지 않음' : error.message);
      setYoutubeConnection(null);
    }
  };

  // YouTube 계정 연동
  const handleYouTubeConnect = async () => {
    try {
      setYoutubeConnectionLoading(true);
      const user = JSON.parse(localStorage.getItem('user'));
      if (!user || !user.id) {
        alert('로그인이 필요합니다.');
        return;
      }

      // YouTube OAuth 연동 페이지로 이동 (user_id 전달)
      window.location.href = `http://localhost:8000/api/youtube/connect?user_id=${user.id}`;
    } catch (error) {
      console.error('YouTube 연동 실패:', error);
      alert('YouTube 연동에 실패했습니다.');
      setYoutubeConnectionLoading(false);
    }
  };

  const loadCustomQuestions = async () => {
    setLoadingQuestions(true);
    try {
      const response = await api.post('/api/ai/business-questions', {
        business_type: businessInfo.business_type
      });
      setCustomQuestions(response.data.questions || []);
    } catch (error) {
      console.error('맞춤 질문 로드 실패:', error);
      setCustomQuestions([]);
    } finally {
      setLoadingQuestions(false);
    }
  };

  const requestAIRecommendations = async () => {
    if (!businessInfo.brand_name || !businessInfo.business_type || !businessInfo.target_audience.age_range) {
      return;
    }

    setLoadingRecommendations(true);
    try {
      const response = await api.post('/api/ai/recommend-interests', {
        brand_name: businessInfo.brand_name,
        business_type: businessInfo.business_type,
        business_description: businessInfo.business_description,
        age_range: businessInfo.target_audience.age_range,
        gender: businessInfo.target_audience.gender
      });

      setRecommendedInterests(response.data.interests || []);
      setAiReasoning(response.data.reasoning || '');
    } catch (error) {
      console.error('AI 추천 실패:', error);
    } finally {
      setLoadingRecommendations(false);
    }
  };

  const analyzeBlog = async () => {
    if (!blogUrl.trim()) {
      alert('네이버 블로그 URL을 입력해주세요.');
      return;
    }

    setBlogAnalysisStatus('analyzing');
    try {
      // 분석 시작
      await api.post('/api/blog/analyze', {
        blog_url: blogUrl,
        max_posts: 10
      });

      // 분석 상태 폴링 (3초마다 체크)
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await api.get('/api/blog/analysis-status');
          const status = statusResponse.data.status;

          if (status === 'completed') {
            clearInterval(pollInterval);
            setBlogAnalysisStatus('completed');
            setBlogAnalysisResult(statusResponse.data.analysis);
          } else if (status === 'failed') {
            clearInterval(pollInterval);
            setBlogAnalysisStatus('failed');
            alert('블로그 분석에 실패했습니다. 다시 시도해주세요.');
          }
        } catch (error) {
          console.error('분석 상태 확인 실패:', error);
        }
      }, 3000);

      // 최대 2분 후 타임아웃
      setTimeout(() => {
        clearInterval(pollInterval);
        if (blogAnalysisStatus === 'analyzing') {
          setBlogAnalysisStatus('failed');
          alert('분석 시간이 초과되었습니다. 다시 시도해주세요.');
        }
      }, 120000);

    } catch (error) {
      console.error('블로그 분석 실패:', error);
      setBlogAnalysisStatus('failed');
      alert('블로그 분석 요청에 실패했습니다.');
    }
  };

  const analyzeMultiPlatform = async () => {
    const hasAtLeastOne = platformUrls.blog || platformUrls.instagram || platformUrls.youtube;
    if (!hasAtLeastOne) {
      alert('최소 1개 이상의 플랫폼 URL을 입력해주세요.');
      return;
    }

    setMultiPlatformAnalysisStatus('analyzing');
    setAnalysisProgress(0); // 진행률 초기화
    setCurrentStep(2); // 분석 중 페이지로 이동

    try {
      // 분석 시작
      const requestData = {};
      if (platformUrls.blog) requestData.blog_url = platformUrls.blog;
      if (platformUrls.instagram) requestData.instagram_url = platformUrls.instagram;
      if (platformUrls.youtube) requestData.youtube_url = platformUrls.youtube;
      requestData.max_posts = 10;

      const response = await api.post('/api/brand-analysis/multi-platform', requestData);
      console.log('멀티 플랫폼 분석 시작:', response.data);

      // 분석 상태 폴링 (5초마다 체크)
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await api.get('/api/brand-analysis/status');
          console.log('분석 상태:', statusResponse.data);

          const { overall } = statusResponse.data;

          // overall 데이터가 있으면 분석 완료
          if (overall && overall.brand_tone) {
            clearInterval(pollInterval);
            setAnalysisProgress(100); // 진행률 100% 완료
            setMultiPlatformAnalysisStatus('completed');
            setMultiPlatformAnalysisResult(statusResponse.data);

            // ✅ businessInfo 업데이트: 백엔드에서 추출한 브랜드명, 업종, 타겟 반영
            setBusinessInfo(prev => ({
              ...prev,
              brand_name: overall.brand_name || prev.brand_name,
              business_type: overall.business_type || prev.business_type,
              target_audience: {
                ...prev.target_audience,
                age_range: overall.target_audience || prev.target_audience.age_range
              }
            }));

            // 완료 페이지로 이동
            setTimeout(() => {
              setCurrentStep(3);
            }, 1000);
          }
        } catch (error) {
          console.error('분석 상태 확인 실패:', error);
        }
      }, 5000);

      // 최대 5분 후 타임아웃
      setTimeout(() => {
        clearInterval(pollInterval);
        if (multiPlatformAnalysisStatus === 'analyzing') {
          setMultiPlatformAnalysisStatus('failed');
          alert('분석 시간이 초과되었습니다. 다시 시도해주세요.');
          setCurrentStep(1); // 다시 입력 페이지로
        }
      }, 300000);

    } catch (error) {
      console.error('멀티 플랫폼 분석 실패:', error);
      setMultiPlatformAnalysisStatus('failed');
      alert('플랫폼 분석 요청에 실패했습니다: ' + (error.response?.data?.detail || error.message));
      setCurrentStep(1); // 다시 입력 페이지로
    }
  };

  const analyzeManualContent = async () => {
    // 유효성 검사: 최소 1개 타입에서 2개 이상의 샘플
    const hasValidText = textSamples.length >= 2 && textSamples.every(s => s.trim());
    const hasValidImages = imageSamples.length >= 2;
    const hasValidVideos = videoSamples.length >= 2;

    if (!hasValidText && !hasValidImages && !hasValidVideos) {
      alert('최소 1개 콘텐츠 타입에서 2개 이상의 샘플을 업로드해주세요.');
      return;
    }

    // 각 타입별로 업로드된 경우 2개 미만이면 경고
    if (textSamples.length > 0 && !hasValidText) {
      alert('글 샘플은 최소 2개 이상 입력해주세요.');
      return;
    }
    if (imageSamples.length > 0 && !hasValidImages) {
      alert('이미지 샘플은 최소 2개 이상 업로드해주세요.');
      return;
    }
    if (videoSamples.length > 0 && !hasValidVideos) {
      alert('영상 샘플은 최소 2개 이상 업로드해주세요.');
      return;
    }

    setManualAnalysisStatus('analyzing');
    setIsLoading(true);

    try {
      // FormData 생성
      const formData = new FormData();

      // 텍스트 샘플 추가 (JSON 문자열로)
      if (hasValidText) {
        formData.append('text_samples', JSON.stringify(textSamples.filter(s => s.trim())));
      }

      // 이미지 샘플 추가
      if (hasValidImages) {
        imageSamples.forEach((file) => {
          formData.append('image_files', file);
        });
      }

      // 영상 샘플 추가
      if (hasValidVideos) {
        videoSamples.forEach((file) => {
          formData.append('video_files', file);
        });
      }

      const response = await api.post('/api/brand-analysis/manual', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      console.log('수동 콘텐츠 분석 시작:', response.data);

      // 분석 상태 폴링 (5초마다 체크)
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await api.get('/api/brand-analysis/status');
          console.log('분석 상태:', statusResponse.data);

          const { overall } = statusResponse.data;

          // overall 데이터가 있으면 분석 완료
          if (overall && overall.brand_tone) {
            clearInterval(pollInterval);
            setManualAnalysisStatus('completed');
            setManualAnalysisResult(statusResponse.data);
            setIsLoading(false);

            // 완료 페이지로 이동
            setShowSuccess(true);
            setTimeout(() => {
              setShowSuccess(false);
              setCurrentStep(3);
            }, 1000);
          }
        } catch (error) {
          console.error('분석 상태 확인 실패:', error);
        }
      }, 5000);

      // 최대 5분 후 타임아웃
      setTimeout(() => {
        clearInterval(pollInterval);
        if (manualAnalysisStatus === 'analyzing') {
          setManualAnalysisStatus('failed');
          setIsLoading(false);
          alert('분석 시간이 초과되었습니다. 다시 시도해주세요.');
        }
      }, 300000);

    } catch (error) {
      console.error('수동 콘텐츠 분석 실패:', error);
      setManualAnalysisStatus('failed');
      setIsLoading(false);
      alert('콘텐츠 분석 요청에 실패했습니다: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 실시간 유효성 검사
  const validateField = (name, value) => {
    let valid = false;
    let message = '';

    switch (name) {
      case 'brand_name':
        valid = value.length >= 2;
        message = valid ? '좋아요!' : '2자 이상 입력해주세요';
        break;
      case 'business_type':
        valid = value !== '';
        message = valid ? '선택 완료!' : '업종을 선택해주세요';
        break;
      default:
        break;
    }

    setValidation(prev => ({
      ...prev,
      [name]: { valid, message }
    }));
  };

  const handleBusinessInfoChange = (e) => {
    const { name, value } = e.target;
    setBusinessInfo(prev => ({
      ...prev,
      [name]: value
    }));
    validateField(name, value);
  };

  const handleCustomFieldChange = (fieldName, value) => {
    setBusinessInfo(prev => ({
      ...prev,
      custom_fields: {
        ...prev.custom_fields,
        [fieldName]: value
      }
    }));
  };

  const handleTargetAudienceChange = (e) => {
    const { name, value } = e.target;
    setBusinessInfo(prev => ({
      ...prev,
      target_audience: {
        ...prev.target_audience,
        [name]: value
      }
    }));
  };

  const handleAddInterest = (interest = null) => {
    const newInterest = interest || interestInput.trim();
    if (newInterest && businessInfo.target_audience.interests.length < 10) {
      setBusinessInfo(prev => ({
        ...prev,
        target_audience: {
          ...prev.target_audience,
          interests: [...prev.target_audience.interests, newInterest]
        }
      }));
      setInterestInput('');
    }
  };

  const handleRemoveInterest = (index) => {
    setBusinessInfo(prev => ({
      ...prev,
      target_audience: {
        ...prev.target_audience,
        interests: prev.target_audience.interests.filter((_, i) => i !== index)
      }
    }));
  };

  // 스타일 선택/해제
  const toggleStyle = (style) => {
    // 미리보기 업데이트
    setSelectedStyleForPreview(style);

    setBusinessInfo(prev => {
      const currentStyles = prev.selected_styles || [];
      if (currentStyles.includes(style)) {
        // 이미 선택된 스타일이면 제거
        return {
          ...prev,
          selected_styles: currentStyles.filter(s => s !== style)
        };
      } else {
        // 최대 3개까지만 선택 가능
        if (currentStyles.length < 3) {
          return {
            ...prev,
            selected_styles: [...currentStyles, style]
          };
        }
        return prev;
      }
    });
  };

  // 브랜드 가치 추가
  const addValue = () => {
    const newValue = valueInput.trim();
    if (newValue && businessInfo.brand_values.length < 5) {
      setBusinessInfo(prev => ({
        ...prev,
        brand_values: [...prev.brand_values, newValue]
      }));
      setValueInput('');
    }
  };

  // 브랜드 가치 제거
  const removeValue = (index) => {
    setBusinessInfo(prev => ({
      ...prev,
      brand_values: prev.brand_values.filter((_, i) => i !== index)
    }));
  };

  // 아이덴티티 정보(스타일/가치) 입력 여부 확인
  const hasIdentityInfo = () => {
    return (
      (businessInfo.selected_styles && businessInfo.selected_styles.length > 0) ||
      (businessInfo.brand_values && businessInfo.brand_values.length > 0)
    );
  };

  const handlePreferenceChange = (e) => {
    const { name, value } = e.target;
    setPreferences(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // 드래그 앤 드롭 핸들러
  const handleDrag = (e, type) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(prev => ({ ...prev, [type]: true }));
    } else if (e.type === "dragleave") {
      setDragActive(prev => ({ ...prev, [type]: false }));
    }
  };

  const handleDrop = (e, type) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(prev => ({ ...prev, [type]: false }));

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0], type);
    }
  };

  const handleFileUpload = (file, type) => {
    if (type === 'image') {
      if (file.type.startsWith('image/')) {
        setImageSample(file);
        setImagePreview(URL.createObjectURL(file));
      } else {
        alert('이미지 파일만 업로드 가능합니다.');
      }
    } else if (type === 'video') {
      if (file.type.startsWith('video/')) {
        setVideoSample(file);
        setVideoPreview(URL.createObjectURL(file));
      } else {
        alert('영상 파일만 업로드 가능합니다.');
      }
    }
  };

  const handleImageInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0], 'image');
    }
  };

  const handleVideoInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0], 'video');
    }
  };

  const saveBusinessInfo = async () => {
    if (!validation.brand_name.valid || !validation.business_type.valid) {
      alert('필수 정보를 모두 입력해주세요.');
      return;
    }

    setIsLoading(true);
    try {
      await api.put('/api/onboarding/business-info', {
        ...businessInfo,
        business_description: businessInfo.business_description +
          (Object.keys(businessInfo.custom_fields).length > 0
            ? '\n\n추가 정보:\n' + JSON.stringify(businessInfo.custom_fields, null, 2)
            : '')
      });

      setShowSuccess(true);
      setTimeout(() => {
        setShowSuccess(false);
        setCurrentStep(2);
      }, 800);
    } catch (error) {
      console.error('비즈니스 정보 저장 실패:', error);
      alert('비즈니스 정보 저장에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const savePreferences = async () => {
    setIsLoading(true);
    try {
      await api.post('/api/onboarding/preferences', preferences);

      if (imageSample) {
        const formData = new FormData();
        formData.append('file', imageSample);
        formData.append('description', preferences.image_style_description);
        await api.post('/api/onboarding/upload-image-sample', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      }

      if (videoSample) {
        const formData = new FormData();
        formData.append('file', videoSample);
        formData.append('description', preferences.video_style_description);
        formData.append('duration_preference', preferences.video_duration_preference);
        await api.post('/api/onboarding/upload-video-sample', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      }

      setShowSuccess(true);
      setTimeout(() => {
        setShowSuccess(false);
        setCurrentStep(3);
      }, 800);
    } catch (error) {
      console.error('선호도 저장 실패:', error);
      alert('선호도 저장에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const completeOnboarding = async () => {
    setIsLoading(true);
    try {
      await api.post('/api/onboarding/complete');
      setShowSuccess(true);
      setTimeout(() => {
        navigate('/content');
      }, 1500);
    } catch (error) {
      console.error('온보딩 완료 실패:', error);
      alert('온보딩 완료에 실패했습니다.');
      setIsLoading(false);
    }
  };

  const getProgressPercentage = () => {
    if (currentStep === 1) {
      let progress = 0;
      if (businessInfo.brand_name) progress += 20;
      if (businessInfo.business_type) progress += 20;
      if (businessInfo.target_audience.age_range) progress += 10;
      return progress;
    } else if (currentStep === 2) {
      return 50;
    } else {
      return 100;
    }
  };

  return (
    <div className="dynamic-onboarding">
      {showSuccess && (
        <div className="success-overlay">
          <div className="success-checkmark">✓</div>
        </div>
      )}

      <div className="onboarding-header">
        <h1>환영합니다, {user?.full_name || user?.username}님!</h1>
        <p>AI가 회원님만의 맞춤 콘텐츠를 만들어드립니다</p>
      </div>

      {/* 프로그레스 바 */}
      <div className="progress-container">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${getProgressPercentage()}%` }}
          />
        </div>
        <div className="progress-steps">
          {currentStep > 0 && (
            <>
              <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>
                <div className="step-number">1</div>
                <div className="step-label">{onboardingPath === 'sns_analysis' ? 'SNS 입력' : '비즈니스'}</div>
              </div>
              <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
                <div className="step-number">2</div>
                <div className="step-label">{onboardingPath === 'sns_analysis' ? '분석 중' : '스타일'}</div>
              </div>
              <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>
                <div className="step-number">3</div>
                <div className="step-label">완료</div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Step 0: SNS 여부 질문 */}
      {currentStep === 0 && (
        <div className="onboarding-step fade-in">
          <h2>안녕하세요! 기존에 운영하시는 SNS가 있으신가요?</h2>
          <p className="step-description">
            기존 SNS가 있다면 AI가 자동으로 브랜드 특성을 분석해드립니다
          </p>

          <div className="sns-choice-container">
            <button
              className="choice-button yes-button"
              onClick={() => {
                setOnboardingPath('sns_analysis');
                setCurrentStep(1);
              }}
            >
              <div className="choice-icon">✅</div>
              <div className="choice-title">예, 있습니다</div>
              <div className="choice-description">
                블로그, 인스타그램, 유튜브 등 운영 중인 SNS를 분석하여
                <br />
                브랜드 특성을 자동으로 파악합니다
              </div>
            </button>

            <button
              className="choice-button no-button"
              onClick={() => {
                setOnboardingPath('manual_input');
                setCurrentStep(1);
              }}
            >
              <div className="choice-icon">📝</div>
              <div className="choice-title">아니오, 없습니다</div>
              <div className="choice-description">
                비즈니스 정보와 콘텐츠 샘플을 직접 입력하여
                <br />
                브랜드 특성을 설정합니다
              </div>
            </button>
          </div>
        </div>
      )}

      {/* Step 1: 비즈니스 정보 (또는 SNS URL 입력) */}
      {currentStep === 1 && onboardingPath === 'manual_input' && (
        <div className="onboarding-step fade-in">
          <h2>비즈니스를 알려주세요</h2>
          <p className="step-description">AI가 이 정보를 바탕으로 완벽한 콘텐츠를 만듭니다</p>

          <div className="onboarding-form-section">
            <div className="form-group">
              <label>브랜드명 *</label>
              <input
                type="text"
                name="brand_name"
                value={businessInfo.brand_name}
                onChange={handleBusinessInfoChange}
                placeholder="예: 나의 카페"
                className={validation.brand_name.valid ? 'valid' : ''}
              />
              {validation.brand_name.message && (
                <span className={`validation-message ${validation.brand_name.valid ? 'success' : 'error'}`}>
                  {validation.brand_name.message}
                </span>
              )}
            </div>

            <div className="form-group">
              <label>업종 *</label>
              <select
                name="business_type"
                value={businessInfo.business_type}
                onChange={handleBusinessInfoChange}
                className={validation.business_type.valid ? 'valid' : ''}
              >
                <option value="">업종 선택</option>
                <option value="food">음식/카페</option>
                <option value="fashion">패션/뷰티</option>
                <option value="health">헬스/피트니스</option>
                <option value="education">교육</option>
                <option value="tech">IT/기술</option>
                <option value="retail">소매/유통</option>
                <option value="service">서비스</option>
                <option value="other">기타</option>
              </select>
              {validation.business_type.message && (
                <span className={`validation-message ${validation.business_type.valid ? 'success' : 'error'}`}>
                  {validation.business_type.message}
                </span>
              )}
            </div>

            {/* 업종별 맞춤 질문 */}
            {loadingQuestions && (
              <div className="loading-questions">
                <div className="spinner-small"></div>
                <span>맞춤 질문 준비 중...</span>
              </div>
            )}

            {customQuestions.length > 0 && (
              <div className="custom-questions fade-in">
                <h3>🎯 {businessInfo.business_type === 'food' ? '음식/카페' : businessInfo.business_type} 맞춤 질문</h3>
                {customQuestions.map((q, index) => (
                  <div key={index} className="form-group">
                    <label>{q.question}</label>
                    <input
                      type="text"
                      placeholder={q.placeholder}
                      onChange={(e) => handleCustomFieldChange(q.field_name, e.target.value)}
                      value={businessInfo.custom_fields[q.field_name] || ''}
                    />
                  </div>
                ))}
              </div>
            )}

            <div className="form-group">
              <label>비즈니스 설명</label>
              <textarea
                name="business_description"
                value={businessInfo.business_description}
                onChange={handleBusinessInfoChange}
                placeholder="예: 건강한 재료로 만든 디저트를 판매하는 카페입니다."
                rows={4}
              />
            </div>

            <h3 className="section-title">타겟 고객</h3>

            <div className="form-group">
              <label>타겟 고객층</label>
              <input
                type="text"
                name="target_description"
                value={businessInfo.target_audience.age_range}
                onChange={(e) => {
                  setBusinessInfo(prev => ({
                    ...prev,
                    target_audience: {
                      ...prev.target_audience,
                      age_range: e.target.value,
                      gender: 'all'
                    }
                  }));
                }}
                placeholder="예: 20-30대 남성, 40-50대 여성, 30대 직장인 등"
              />
              <p className="input-hint">
                자유롭게 입력하세요. 예: "20-30대 남성", "40-50대 여성", "30대 직장인"
              </p>
            </div>

            {/* AI 추천 버튼 */}
            {businessInfo.brand_name && businessInfo.business_type && businessInfo.target_audience.age_range && (
              <button
                type="button"
                onClick={requestAIRecommendations}
                className="btn-ai-recommend"
                disabled={loadingRecommendations}
              >
                {loadingRecommendations ? (
                  <>
                    <div className="spinner-small"></div>
                    <span>AI가 분석 중...</span>
                  </>
                ) : (
                  <>✨ AI가 관심사 추천</>
                )}
              </button>
            )}

            {/* AI 추천 관심사 */}
            {recommendedInterests.length > 0 && (
              <div className="ai-recommendations fade-in">
                <h4>🤖 AI 추천 관심사</h4>
                {aiReasoning && <p className="ai-reasoning">{aiReasoning}</p>}
                <div className="recommended-tags">
                  {recommendedInterests.map((interest, index) => (
                    <button
                      key={index}
                      className="recommended-tag"
                      onClick={() => handleAddInterest(interest)}
                      disabled={businessInfo.target_audience.interests.includes(interest)}
                    >
                      {interest} +
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="form-group">
              <label>관심사 (최대 10개)</label>
              <div className="interest-input-container">
                <input
                  type="text"
                  value={interestInput}
                  onChange={(e) => setInterestInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddInterest())}
                  placeholder="예: 건강, 다이어트"
                  disabled={businessInfo.target_audience.interests.length >= 10}
                />
                <button
                  type="button"
                  onClick={() => handleAddInterest()}
                  className="btn-add"
                  disabled={businessInfo.target_audience.interests.length >= 10}
                >
                  추가
                </button>
              </div>
              <div className="interest-tags">
                {businessInfo.target_audience.interests.map((interest, index) => (
                  <span key={index} className="interest-tag">
                    {interest}
                    <button onClick={() => handleRemoveInterest(index)}>×</button>
                  </span>
                ))}
              </div>
            </div>

            <h3 className="section-title">
              🎨 브랜드 아이덴티티
              <span className="optional-badge">선택</span>
            </h3>
            <p className="section-hint">
              💡 입력하시면 샘플 없이도 콘텐츠 생성이 가능합니다.
              <br />
              {hasIdentityInfo() ? (
                <span className="text-success">
                  ✓ 입력 완료! 다음 단계에서 샘플은 선택 사항입니다.
                </span>
              ) : (
                <span className="text-warning">
                  ⚠️ 미입력 시 다음 단계에서 샘플이 필수입니다.
                </span>
              )}
            </p>

            <div className="form-group">
              <label>추구하는 스타일 (최대 3개 선택)</label>
              <div className="style-selector-container">
                {/* 왼쪽: 스타일 옵션 그리드 (2행 4열) */}
                <div className="style-options-grid">
                  {['따뜻한', '친근한', '전문적인', '유머러스한', '진지한', '창의적인', '신뢰감있는', '트렌디한'].map(style => (
                    <button
                      key={style}
                      type="button"
                      className={`style-option-button ${businessInfo.selected_styles?.includes(style) ? 'selected' : ''} ${selectedStyleForPreview === style ? 'previewing' : ''}`}
                      onClick={() => toggleStyle(style)}
                      disabled={businessInfo.selected_styles?.length >= 3 && !businessInfo.selected_styles?.includes(style)}
                    >
                      {style}
                    </button>
                  ))}
                </div>

                {/* 오른쪽: 스타일 예시 카드 */}
                <div className="style-preview-card">
                  {selectedStyleForPreview ? (
                    <div className="preview-content fade-in">
                      <div className="preview-header">
                        <h4>{selectedStyleForPreview}</h4>
                        <span className="preview-industry">{styleExamples[selectedStyleForPreview].industry}</span>
                      </div>
                      <div className="preview-text">
                        {styleExamples[selectedStyleForPreview].text}
                      </div>
                    </div>
                  ) : (
                    <div className="preview-placeholder">
                      <p>스타일을 선택하면 예시를 확인할 수 있습니다</p>
                    </div>
                  )}
                </div>
              </div>
              {businessInfo.selected_styles?.length > 0 && (
                <small className="input-hint">
                  {businessInfo.selected_styles.length}/3개 선택됨
                </small>
              )}
            </div>

            <div className="form-group">
              <label>브랜드 가치 (최대 5개)</label>
              <div className="interest-input-container">
                <input
                  type="text"
                  value={valueInput}
                  onChange={(e) => setValueInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addValue())}
                  placeholder="예: 친환경, 고품질"
                  disabled={businessInfo.brand_values?.length >= 5}
                />
                <button
                  type="button"
                  onClick={addValue}
                  className="btn-add"
                  disabled={businessInfo.brand_values?.length >= 5}
                >
                  추가
                </button>
              </div>
              <div className="interest-tags">
                {businessInfo.brand_values?.map((value, index) => (
                  <span key={index} className="interest-tag">
                    {value}
                    <button onClick={() => removeValue(index)}>×</button>
                  </span>
                ))}
              </div>
            </div>

            <div className="step-actions">
              <button
                onClick={() => setCurrentStep(0)}
                className="btn-secondary"
              >
                이전
              </button>
              <button
                onClick={() => setCurrentStep(2)}
                className="btn-secondary"
              >
                건너뛰기
              </button>
              <button
                onClick={saveBusinessInfo}
                disabled={isLoading || !validation.brand_name.valid || !validation.business_type.valid}
                className="btn-primary"
              >
                {isLoading ? '저장 중...' : '다음 단계'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 1: SNS URL 입력 (SNS 분석 경로) */}
      {currentStep === 1 && onboardingPath === 'sns_analysis' && (
        <div className="onboarding-step fade-in">
          <h2>SNS 계정을 알려주세요</h2>
          <p className="step-description">
            운영 중인 플랫폼의 URL을 입력해주세요.
            <br />
            입력하신 플랫폼만 분석되며, 선택적으로 입력 가능합니다.
          </p>

          <div className="platform-note" style={{ marginBottom: 'var(--space-lg)' }}>
            ℹ️ 최소 1개 이상의 플랫폼 URL을 입력해주세요
          </div>

          <div className="onboarding-form-section">
            <div className="platform-input-group">
              <h3>📝 네이버 블로그 (선택)</h3>
              <input
                type="text"
                value={platformUrls.blog}
                onChange={(e) => setPlatformUrls(prev => ({ ...prev, blog: e.target.value }))}
                placeholder="예: https://blog.naver.com/your_blog_id"
                className="platform-url-input"
              />
              <small>블로그 URL을 입력하시면 글쓰기 스타일과 브랜드 톤을 분석합니다</small>
            </div>

            <div className="platform-input-group">
              <h3>📸 인스타그램 (선택)</h3>
              <input
                type="text"
                value={platformUrls.instagram}
                onChange={(e) => setPlatformUrls(prev => ({ ...prev, instagram: e.target.value }))}
                placeholder="예: https://instagram.com/your_account"
                className="platform-url-input"
              />
              <small>인스타그램 URL을 입력하시면 이미지 스타일과 캡션 특성을 분석합니다</small>
            </div>

            <div className="platform-input-group">
              <h3>🎥 유튜브 (선택)</h3>
              {youtubeConnection ? (
                <div style={{
                  padding: '16px',
                  backgroundColor: '#f0f8ff',
                  borderRadius: '8px',
                  border: '2px solid #D8BFD8'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {youtubeConnection.channel_thumbnail_url && (
                      <img
                        src={youtubeConnection.channel_thumbnail_url}
                        alt="Channel"
                        style={{ width: '48px', height: '48px', borderRadius: '50%' }}
                      />
                    )}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                        {youtubeConnection.channel_title}
                      </div>
                      <div style={{ fontSize: '14px', color: '#666' }}>
                        구독자 {youtubeConnection.subscriber_count?.toLocaleString()}명 ·
                        동영상 {youtubeConnection.video_count}개
                      </div>
                    </div>
                    <div style={{ color: '#4CAF50', fontWeight: 'bold' }}>✓ 연동됨</div>
                  </div>
                </div>
              ) : (
                <button
                  onClick={handleYouTubeConnect}
                  disabled={youtubeConnectionLoading}
                  style={{
                    width: '100%',
                    padding: '16px',
                    backgroundColor: youtubeConnectionLoading ? '#ccc' : '#FF0000',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '16px',
                    fontWeight: 'bold',
                    cursor: youtubeConnectionLoading ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                  }}
                >
                  {youtubeConnectionLoading ? '연동 중...' : (
                    <>
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                      </svg>
                      YouTube 계정 연동
                    </>
                  )}
                </button>
              )}
              <small>YouTube 계정을 연동하면 채널 정보와 영상 스타일을 자동으로 분석합니다</small>
            </div>

            <div className="step-actions">
              <button
                onClick={() => setCurrentStep(0)}
                className="btn-secondary"
              >
                이전
              </button>
              <button
                onClick={() => setCurrentStep(3)}
                className="btn-secondary"
              >
                건너뛰기
              </button>
              <button
                onClick={analyzeMultiPlatform}
                disabled={!platformUrls.blog && !platformUrls.instagram && !platformUrls.youtube}
                className="btn-primary"
              >
                분석 시작
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: 콘텐츠 스타일 (수동 입력 경로만) */}
      {currentStep === 2 && onboardingPath === 'manual_input' && (
        <div className="onboarding-step fade-in">
          <h2>선호하는 콘텐츠 스타일</h2>

          {/* 조건부 설명 */}
          <p className="step-description">
            {!hasIdentityInfo() ? (
              <>
                ⚠️ <strong>최소 1개 콘텐츠 타입</strong>에서 <strong>2개 이상의 샘플</strong>을 업로드해주세요.
                <br />
                <small className="text-warning">
                  (Step 1에서 스타일/가치를 입력하지 않으셨기 때문에 샘플이 필수입니다)
                </small>
              </>
            ) : (
              <>
                샘플을 제공하시면 더 정확한 콘텐츠를 만들 수 있어요
                <br />
                <small className="text-success">
                  ✓ 스타일/가치 정보를 입력하셨으므로 샘플은 선택 사항입니다
                </small>
              </>
            )}
          </p>

          <div className="onboarding-form-section">
            {/* 글 스타일 */}
            <div className="style-card">
              <h3>
                📝 글 스타일
                {hasIdentityInfo() ? ' (선택)' : ' (필수 중 1개)'}
              </h3>
              <p className="style-hint">
                업로드 시 최소 2개의 글 샘플을 입력해주세요
              </p>

              {textSamples.map((sample, index) => (
                <div key={index} className="sample-item">
                  <label>글 샘플 {index + 1}</label>
                  <textarea
                    value={sample}
                    onChange={(e) => {
                      const newSamples = [...textSamples];
                      newSamples[index] = e.target.value;
                      setTextSamples(newSamples);
                    }}
                    placeholder="예: 안녕하세요! 오늘은 건강한 디저트 레시피를 소개해드릴게요 😊"
                    rows={4}
                  />
                  {textSamples.length > 0 && (
                    <button
                      type="button"
                      className="btn-remove-sample"
                      onClick={() => setTextSamples(textSamples.filter((_, i) => i !== index))}
                    >
                      삭제
                    </button>
                  )}
                </div>
              ))}

              <button
                type="button"
                className="btn-add-sample"
                onClick={() => setTextSamples([...textSamples, ''])}
              >
                + 글 샘플 추가
              </button>

              {textSamples.length > 0 && textSamples.length < 2 && (
                <small className="validation-warning">
                  최소 2개의 글 샘플이 필요합니다
                </small>
              )}
            </div>

            {/* 이미지 스타일 */}
            <div className="style-card">
              <h3>
                🎨 이미지 스타일
                {hasIdentityInfo() ? ' (선택)' : ' (필수 중 1개)'}
              </h3>
              <p className="style-hint">
                업로드 시 최소 2개의 이미지 샘플을 업로드해주세요
              </p>

              <div className="multiple-samples-container">
                {imageSamples.map((sample, index) => (
                  <div key={index} className="sample-preview">
                    <img src={URL.createObjectURL(sample)} alt={`이미지 샘플 ${index + 1}`} />
                    <button
                      type="button"
                      className="btn-remove-sample-mini"
                      onClick={() => setImageSamples(imageSamples.filter((_, i) => i !== index))}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>

              <input
                ref={imageInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={(e) => {
                  const files = Array.from(e.target.files);
                  setImageSamples([...imageSamples, ...files]);
                }}
                style={{ display: 'none' }}
              />

              <button
                type="button"
                className="btn-upload-sample"
                onClick={() => imageInputRef.current?.click()}
              >
                📸 이미지 추가
              </button>

              {imageSamples.length > 0 && imageSamples.length < 2 && (
                <small className="validation-warning">
                  최소 2개의 이미지 샘플이 필요합니다
                </small>
              )}
            </div>

            {/* 영상 스타일 */}
            <div className="style-card">
              <h3>
                🎥 영상 스타일
                {hasIdentityInfo() ? ' (선택)' : ' (필수 중 1개)'}
              </h3>
              <p className="style-hint">
                업로드 시 최소 2개의 영상 샘플을 업로드해주세요
              </p>

              <div className="multiple-samples-container">
                {videoSamples.map((sample, index) => (
                  <div key={index} className="sample-preview video-preview">
                    <video src={URL.createObjectURL(sample)} controls />
                    <button
                      type="button"
                      className="btn-remove-sample-mini"
                      onClick={() => setVideoSamples(videoSamples.filter((_, i) => i !== index))}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>

              <input
                ref={videoInputRef}
                type="file"
                accept="video/*"
                multiple
                onChange={(e) => {
                  const files = Array.from(e.target.files);
                  setVideoSamples([...videoSamples, ...files]);
                }}
                style={{ display: 'none' }}
              />

              <button
                type="button"
                className="btn-upload-sample"
                onClick={() => videoInputRef.current?.click()}
              >
                🎬 영상 추가
              </button>

              {videoSamples.length > 0 && videoSamples.length < 2 && (
                <small className="validation-warning">
                  최소 2개의 영상 샘플이 필요합니다
                </small>
              )}
            </div>

            {/* 조건부 안내 메시지 */}
            <div className={`sample-note ${!hasIdentityInfo() ? 'required' : 'optional'}`}>
              {!hasIdentityInfo() ? (
                <>
                  ⚠️ <strong>필수:</strong> 최소 1개 콘텐츠 타입(글/이미지/영상)을 선택하여 업로드해주세요.
                  <br />
                  각 타입별로 최소 2개의 샘플이 필요합니다.
                </>
              ) : (
                <>
                  ℹ️ <strong>선택:</strong> 샘플을 제공하지 않아도 되지만, 제공하시면 더 정확한 분석이 가능합니다.
                </>
              )}
            </div>

            <div className="step-actions">
              <button onClick={() => setCurrentStep(1)} className="btn-secondary">
                이전
              </button>
              <button
                onClick={async () => {
                  if (!hasIdentityInfo()) {
                    alert('스타일/가치를 입력하지 않으셨으므로 샘플이 필수입니다.');
                    return;
                  }
                  // 샘플 없이 건너뛰기 - 기본 프로필 생성
                  try {
                    await api.post('/api/brand-analysis/create-basic-profile', {
                      brand_name: businessInfo.brand_name,
                      business_type: businessInfo.business_type,
                      business_description: businessInfo.business_description,
                      target_audience: businessInfo.target_audience.age_range,
                      selected_styles: businessInfo.selected_styles,
                      brand_values: businessInfo.brand_values
                    });
                    setCurrentStep(3);
                  } catch (error) {
                    console.error('기본 프로필 생성 실패:', error);
                    alert('프로필 생성에 실패했습니다: ' + (error.response?.data?.detail || error.message));
                  }
                }}
                className="btn-secondary"
                disabled={!hasIdentityInfo()}
                title={!hasIdentityInfo() ? 'Step 1에서 스타일/가치를 입력하지 않으셨다면 샘플이 필수입니다' : ''}
              >
                건너뛰기 {!hasIdentityInfo() && '(비활성)'}
              </button>
              <button
                onClick={analyzeManualContent}
                disabled={isLoading}
                className="btn-primary"
              >
                {isLoading ? '분석 중...' : '분석 시작'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: SNS 분석 진행 중 (SNS 분석 경로만) */}
      {currentStep === 2 && onboardingPath === 'sns_analysis' && (
        <div className="onboarding-step fade-in">
          <h2>SNS 분석 중입니다...</h2>
          <p className="step-description">
            입력하신 플랫폼의 콘텐츠를 분석하고 있습니다.
            <br />
            잠시만 기다려주세요 (최대 5분 소요)
          </p>

          <div className="analysis-progress-container">
            <div className="spinner-large"></div>

            {/* 진행률 프로그래스바 */}
            {multiPlatformAnalysisStatus === 'analyzing' && (
              <div style={{ width: '100%', marginTop: '32px', marginBottom: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <span style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)' }}>
                    분석 진행률
                  </span>
                  <span style={{ fontSize: '16px', fontWeight: '700', color: '#D8BFD8' }}>
                    {Math.round(analysisProgress)}%
                  </span>
                </div>
                <div style={{
                  width: '100%',
                  height: '10px',
                  backgroundColor: '#F8F8FF',
                  borderRadius: '5px',
                  overflow: 'hidden',
                  boxShadow: 'inset 0 1px 3px rgba(0, 0, 0, 0.1)'
                }}>
                  <div style={{
                    width: `${analysisProgress}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #D8BFD8 0%, #E6E6FA 100%)',
                    transition: 'width 0.5s ease',
                    borderRadius: '5px'
                  }}></div>
                </div>
              </div>
            )}

            {multiPlatformAnalysisStatus === 'analyzing' && (
              <div className="progress-message">
                {analysisProgress < 20 && (
                  <p>🔍 플랫폼 콘텐츠 수집 중...</p>
                )}
                {analysisProgress >= 20 && analysisProgress < 40 && (
                  <p>📊 수집된 콘텐츠 분석 중...</p>
                )}
                {analysisProgress >= 40 && analysisProgress < 70 && (
                  <p>🤖 AI가 브랜드 특성을 분석 중...</p>
                )}
                {analysisProgress >= 70 && analysisProgress < 90 && (
                  <p>✨ 브랜드 프로필 생성 중...</p>
                )}
                {analysisProgress >= 90 && (
                  <p>✅ 거의 완료되었습니다!</p>
                )}
              </div>
            )}

            {multiPlatformAnalysisStatus === 'completed' && (
              <div className="analysis-complete fade-in">
                <div className="completion-icon">✅</div>
                <h3>분석 완료!</h3>
                <p>브랜드 특성 분석이 성공적으로 완료되었습니다.</p>
              </div>
            )}

            {multiPlatformAnalysisStatus === 'failed' && (
              <div className="analysis-failed">
                <div className="error-icon">❌</div>
                <h3>분석 실패</h3>
                <p>분석 중 오류가 발생했습니다. 다시 시도해주세요.</p>
                <button onClick={() => setCurrentStep(1)} className="btn-secondary">
                  다시 시도
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 3: 완료 */}
      {currentStep === 3 && (
        <div className="onboarding-step completion-step fade-in">
          <div className="completion-animation">
            <div className="completion-icon">🎉</div>
            <div className="confetti"></div>
          </div>
          <h2>모든 설정이 완료되었습니다!</h2>
          <p className="step-description">
            이제 AI가 {businessInfo.brand_name}만을 위한 맞춤 콘텐츠를 생성할 준비가 되었습니다
          </p>

          <div className="completion-summary">
            <h3>입력하신 정보</h3>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="summary-label">브랜드</span>
                <span className="summary-value">{businessInfo.brand_name}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">업종</span>
                <span className="summary-value">{businessInfo.business_type}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">타겟</span>
                <span className="summary-value">
                  {businessInfo.target_audience.age_range} {businessInfo.target_audience.gender === 'all' ? '전체' : businessInfo.target_audience.gender}
                </span>
              </div>
              {businessInfo.target_audience.interests.length > 0 && (
                <div className="summary-item full-width">
                  <span className="summary-label">관심사</span>
                  <span className="summary-value">{businessInfo.target_audience.interests.join(', ')}</span>
                </div>
              )}
            </div>
          </div>

          <div className="step-actions">
            <button
              onClick={() => setCurrentStep(0)}
              className="btn-secondary"
            >
              처음으로
            </button>
            <button
              onClick={() => {
                if (onboardingPath === 'sns_analysis') {
                  setCurrentStep(1);
                } else {
                  setCurrentStep(2);
                }
              }}
              className="btn-secondary"
            >
              이전
            </button>
            <button onClick={completeOnboarding} disabled={isLoading} className="btn-primary btn-large">
              {isLoading ? '처리 중...' : '🚀 대시보드로 이동'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default DynamicOnboarding;
