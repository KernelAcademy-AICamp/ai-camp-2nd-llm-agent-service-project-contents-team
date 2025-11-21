import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import './DynamicOnboarding.css';

function DynamicOnboarding() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

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

  // Step 2: 콘텐츠 선호도
  const [preferences, setPreferences] = useState({
    text_style_sample: '',
    text_tone: 'casual',
    image_style_description: '',
    video_style_description: '',
    video_duration_preference: 'short'
  });

  // 파일 업로드 (드래그 앤 드롭)
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
          <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>
            <div className="step-number">1</div>
            <div className="step-label">비즈니스</div>
          </div>
          <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
            <div className="step-number">2</div>
            <div className="step-label">스타일</div>
          </div>
          <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>
            <div className="step-number">3</div>
            <div className="step-label">완료</div>
          </div>
        </div>
      </div>

      {/* Step 1: 비즈니스 정보 */}
      {currentStep === 1 && (
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

            <div className="form-row">
              <div className="form-group">
                <label>연령대</label>
                <select
                  name="age_range"
                  value={businessInfo.target_audience.age_range}
                  onChange={handleTargetAudienceChange}
                >
                  <option value="">선택</option>
                  <option value="10-19">10대</option>
                  <option value="20-29">20대</option>
                  <option value="30-39">30대</option>
                  <option value="40-49">40대</option>
                  <option value="50+">50대 이상</option>
                </select>
              </div>

              <div className="form-group">
                <label>성별</label>
                <select
                  name="gender"
                  value={businessInfo.target_audience.gender}
                  onChange={handleTargetAudienceChange}
                >
                  <option value="all">전체</option>
                  <option value="male">남성</option>
                  <option value="female">여성</option>
                </select>
              </div>
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

      {/* Step 2: 콘텐츠 스타일 */}
      {currentStep === 2 && (
        <div className="onboarding-step fade-in">
          <h2>선호하는 콘텐츠 스타일</h2>
          <p className="step-description">샘플을 제공하시면 더 정확한 콘텐츠를 만들 수 있어요</p>

          <div className="form-section">
            {/* 글 스타일 */}
            <div className="style-card">
              <h3>📝 글 스타일</h3>

              <div className="form-group">
                <label>톤앤매너</label>
                <div className="tone-selector">
                  {[
                    { value: 'casual', label: '캐주얼', emoji: '😊' },
                    { value: 'professional', label: '전문적', emoji: '💼' },
                    { value: 'friendly', label: '친근함', emoji: '🤗' },
                    { value: 'formal', label: '격식있음', emoji: '🎩' }
                  ].map(tone => (
                    <button
                      key={tone.value}
                      type="button"
                      className={`tone-option ${preferences.text_tone === tone.value ? 'active' : ''}`}
                      onClick={() => setPreferences(prev => ({ ...prev, text_tone: tone.value }))}
                    >
                      <span className="tone-emoji">{tone.emoji}</span>
                      <span>{tone.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>선호하는 글 샘플 (선택)</label>
                <textarea
                  name="text_style_sample"
                  value={preferences.text_style_sample}
                  onChange={handlePreferenceChange}
                  placeholder="예: 안녕하세요! 오늘은 건강한 디저트 레시피를 소개해드릴게요 😊"
                  rows={4}
                />
                <small>이런 스타일의 글을 원하신다면 샘플을 입력해주세요.</small>
              </div>
            </div>

            {/* 이미지 스타일 */}
            <div className="style-card">
              <h3>🎨 이미지 스타일</h3>

              <div
                className={`drag-drop-zone ${dragActive.image ? 'drag-active' : ''} ${imagePreview ? 'has-file' : ''}`}
                onDragEnter={(e) => handleDrag(e, 'image')}
                onDragLeave={(e) => handleDrag(e, 'image')}
                onDragOver={(e) => handleDrag(e, 'image')}
                onDrop={(e) => handleDrop(e, 'image')}
                onClick={() => imageInputRef.current?.click()}
              >
                <input
                  ref={imageInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageInputChange}
                  style={{ display: 'none' }}
                />
                {imagePreview ? (
                  <div className="file-preview">
                    <img src={imagePreview} alt="이미지 샘플" />
                    <button
                      type="button"
                      className="btn-remove-file"
                      onClick={(e) => {
                        e.stopPropagation();
                        setImageSample(null);
                        setImagePreview(null);
                      }}
                    >
                      ×
                    </button>
                  </div>
                ) : (
                  <div className="drag-drop-content">
                    <div className="upload-icon">📸</div>
                    <p>이미지를 드래그하거나 클릭하여 업로드</p>
                    <small>선호하는 이미지 스타일을 보여주세요</small>
                  </div>
                )}
              </div>

              <div className="form-group">
                <label>원하는 이미지 스타일 설명</label>
                <textarea
                  name="image_style_description"
                  value={preferences.image_style_description}
                  onChange={handlePreferenceChange}
                  placeholder="예: 밝고 화사한 느낌, 파스텔 톤"
                  rows={3}
                />
              </div>
            </div>

            {/* 영상 스타일 */}
            <div className="style-card">
              <h3>🎥 영상 스타일</h3>

              <div
                className={`drag-drop-zone ${dragActive.video ? 'drag-active' : ''} ${videoPreview ? 'has-file' : ''}`}
                onDragEnter={(e) => handleDrag(e, 'video')}
                onDragLeave={(e) => handleDrag(e, 'video')}
                onDragOver={(e) => handleDrag(e, 'video')}
                onDrop={(e) => handleDrop(e, 'video')}
                onClick={() => videoInputRef.current?.click()}
              >
                <input
                  ref={videoInputRef}
                  type="file"
                  accept="video/*"
                  onChange={handleVideoInputChange}
                  style={{ display: 'none' }}
                />
                {videoPreview ? (
                  <div className="file-preview">
                    <video src={videoPreview} controls />
                    <button
                      type="button"
                      className="btn-remove-file"
                      onClick={(e) => {
                        e.stopPropagation();
                        setVideoSample(null);
                        setVideoPreview(null);
                      }}
                    >
                      ×
                    </button>
                  </div>
                ) : (
                  <div className="drag-drop-content">
                    <div className="upload-icon">🎬</div>
                    <p>영상을 드래그하거나 클릭하여 업로드</p>
                    <small>선호하는 영상 스타일을 보여주세요</small>
                  </div>
                )}
              </div>

              <div className="form-group">
                <label>원하는 영상 스타일 설명</label>
                <textarea
                  name="video_style_description"
                  value={preferences.video_style_description}
                  onChange={handlePreferenceChange}
                  placeholder="예: 역동적이고 빠른 편집, ASMR 느낌"
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label>선호하는 영상 길이</label>
                <div className="duration-selector">
                  {[
                    { value: 'short', label: '짧음', time: '15초' },
                    { value: 'medium', label: '보통', time: '30초' },
                    { value: 'long', label: '길게', time: '60초+' }
                  ].map(duration => (
                    <button
                      key={duration.value}
                      type="button"
                      className={`duration-option ${preferences.video_duration_preference === duration.value ? 'active' : ''}`}
                      onClick={() => setPreferences(prev => ({ ...prev, video_duration_preference: duration.value }))}
                    >
                      <span className="duration-label">{duration.label}</span>
                      <span className="duration-time">{duration.time}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="step-actions">
              <button onClick={() => setCurrentStep(1)} className="btn-secondary">
                이전
              </button>
              <button onClick={savePreferences} disabled={isLoading} className="btn-primary">
                {isLoading ? '저장 중...' : '다음 단계'}
              </button>
            </div>
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
