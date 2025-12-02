import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import './DynamicOnboarding.css';

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
    custom_fields: {} // 업종별 맞춤 필드
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
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('온보딩 상태 확인 실패:', error);
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
        navigate('/dashboard');
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

          <div className="form-section">
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

          <div className="form-section">
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
              <input
                type="text"
                value={platformUrls.youtube}
                onChange={(e) => setPlatformUrls(prev => ({ ...prev, youtube: e.target.value }))}
                placeholder="예: https://youtube.com/@your_channel"
                className="platform-url-input"
              />
              <small>유튜브 URL을 입력하시면 영상 스타일과 콘텐츠 특성을 분석합니다</small>
            </div>

            <div className="platform-note">
              ℹ️ 최소 1개 이상의 플랫폼 URL을 입력해주세요
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
          <p className="step-description">샘플을 제공하시면 더 정확한 콘텐츠를 만들 수 있어요</p>

          <div className="form-section">
            {/* 글 스타일 */}
            <div className="style-card">
              <h3>📝 글 스타일 (선택)</h3>
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
              <h3>🎨 이미지 스타일 (선택)</h3>
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
              <h3>🎥 영상 스타일 (선택)</h3>
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

            <div className="sample-note">
              ℹ️ 최소 1개 콘텐츠 타입(글/이미지/영상)을 선택하여 업로드해주세요.
              <br />
              각 타입별로 최소 2개의 샘플이 필요합니다.
            </div>

            <div className="step-actions">
              <button onClick={() => setCurrentStep(1)} className="btn-secondary">
                이전
              </button>
              <button
                onClick={() => setCurrentStep(3)}
                className="btn-secondary"
              >
                건너뛰기
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

            {multiPlatformAnalysisStatus === 'analyzing' && (
              <div className="progress-message">
                <p>🔍 플랫폼 콘텐츠 수집 중...</p>
                <p>🤖 AI가 브랜드 특성을 분석 중...</p>
                {platformUrls.blog && <p>📝 블로그 분석 진행 중</p>}
                {platformUrls.instagram && <p>📸 인스타그램 분석 진행 중</p>}
                {platformUrls.youtube && <p>🎥 유튜브 분석 진행 중</p>}
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
