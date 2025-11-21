import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import './Onboarding.css';

function Onboarding() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);

  // Step 1: 비즈니스 정보
  const [businessInfo, setBusinessInfo] = useState({
    brand_name: '',
    business_type: '',
    business_description: '',
    target_audience: {
      age_range: '',
      gender: 'all',
      interests: []
    }
  });

  // Step 2: 콘텐츠 선호도
  const [preferences, setPreferences] = useState({
    text_style_sample: '',
    text_tone: 'casual',
    image_style_description: '',
    image_color_palette: [],
    video_style_description: '',
    video_duration_preference: 'short'
  });

  // 파일 업로드
  const [imageSample, setImageSample] = useState(null);
  const [videoSample, setVideoSample] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);

  // 관심사 입력
  const [interestInput, setInterestInput] = useState('');

  useEffect(() => {
    // 온보딩 상태 확인
    checkOnboardingStatus();
  }, []);

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

  const handleBusinessInfoChange = (e) => {
    const { name, value } = e.target;
    setBusinessInfo(prev => ({
      ...prev,
      [name]: value
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

  const handleAddInterest = () => {
    if (interestInput.trim() && businessInfo.target_audience.interests.length < 5) {
      setBusinessInfo(prev => ({
        ...prev,
        target_audience: {
          ...prev.target_audience,
          interests: [...prev.target_audience.interests, interestInput.trim()]
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

  const handleImageSampleChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageSample(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleVideoSampleChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setVideoSample(file);
      setVideoPreview(URL.createObjectURL(file));
    }
  };

  const saveBusinessInfo = async () => {
    setIsLoading(true);
    try {
      await api.put('/api/onboarding/business-info', businessInfo);
      setCurrentStep(2);
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
      // 텍스트 선호도 저장
      await api.post('/api/onboarding/preferences', preferences);

      // 이미지 샘플 업로드
      if (imageSample) {
        const formData = new FormData();
        formData.append('file', imageSample);
        formData.append('description', preferences.image_style_description);
        await api.post('/api/onboarding/upload-image-sample', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
      }

      // 영상 샘플 업로드
      if (videoSample) {
        const formData = new FormData();
        formData.append('file', videoSample);
        formData.append('description', preferences.video_style_description);
        formData.append('duration_preference', preferences.video_duration_preference);
        await api.post('/api/onboarding/upload-video-sample', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
      }

      setCurrentStep(3);
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
      navigate('/dashboard');
    } catch (error) {
      console.error('온보딩 완료 실패:', error);
      alert('온보딩 완료에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="onboarding-container">
      <div className="onboarding-header">
        <h1>환영합니다, {user?.full_name || user?.username}님!</h1>
        <p>맞춤형 콘텐츠 제작을 위해 몇 가지 정보가 필요합니다.</p>
      </div>

      {/* 진행 단계 표시 */}
      <div className="progress-steps">
        <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>
          <div className="step-number">1</div>
          <div className="step-label">비즈니스 정보</div>
        </div>
        <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
          <div className="step-number">2</div>
          <div className="step-label">콘텐츠 스타일</div>
        </div>
        <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>
          <div className="step-number">3</div>
          <div className="step-label">완료</div>
        </div>
      </div>

      {/* Step 1: 비즈니스 정보 */}
      {currentStep === 1 && (
        <div className="onboarding-step">
          <h2>비즈니스 정보를 알려주세요</h2>
          <p className="step-description">브랜드에 맞는 콘텐츠를 생성하기 위해 필요한 정보입니다.</p>

          <div className="form-group">
            <label>브랜드명 *</label>
            <input
              type="text"
              name="brand_name"
              value={businessInfo.brand_name}
              onChange={handleBusinessInfoChange}
              placeholder="예: 나의 카페"
              required
            />
          </div>

          <div className="form-group">
            <label>업종 *</label>
            <select
              name="business_type"
              value={businessInfo.business_type}
              onChange={handleBusinessInfoChange}
              required
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
          </div>

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

          <h3>타겟 고객 정보</h3>

          <div className="form-group">
            <label>연령대</label>
            <select
              name="age_range"
              value={businessInfo.target_audience.age_range}
              onChange={handleTargetAudienceChange}
            >
              <option value="">연령대 선택</option>
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

          <div className="form-group">
            <label>관심사 (최대 5개)</label>
            <div className="interest-input">
              <input
                type="text"
                value={interestInput}
                onChange={(e) => setInterestInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddInterest())}
                placeholder="예: 건강, 다이어트"
              />
              <button type="button" onClick={handleAddInterest} className="btn-add">
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
              disabled={isLoading || !businessInfo.brand_name || !businessInfo.business_type}
              className="btn-primary"
            >
              {isLoading ? '저장 중...' : '다음 단계'}
            </button>
          </div>
        </div>
      )}

      {/* Step 2: 콘텐츠 스타일 */}
      {currentStep === 2 && (
        <div className="onboarding-step">
          <h2>선호하는 콘텐츠 스타일을 알려주세요</h2>
          <p className="step-description">샘플을 제공하시면 더 정확한 콘텐츠를 생성할 수 있습니다.</p>

          {/* 글 스타일 */}
          <div className="style-section">
            <h3>📝 글 스타일</h3>

            <div className="form-group">
              <label>톤앤매너</label>
              <select
                name="text_tone"
                value={preferences.text_tone}
                onChange={handlePreferenceChange}
              >
                <option value="casual">캐주얼 (친근한 느낌)</option>
                <option value="professional">전문적 (공식적)</option>
                <option value="friendly">친근함 (따뜻한 느낌)</option>
                <option value="formal">격식있음 (정중한)</option>
              </select>
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
          <div className="style-section">
            <h3>🎨 이미지 스타일</h3>

            <div className="form-group">
              <label>샘플 이미지 업로드 (선택)</label>
              <input
                type="file"
                accept="image/*"
                onChange={handleImageSampleChange}
              />
              {imagePreview && (
                <div className="image-preview">
                  <img src={imagePreview} alt="이미지 샘플" />
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
          <div className="style-section">
            <h3>🎥 영상 스타일</h3>

            <div className="form-group">
              <label>샘플 영상 업로드 (선택)</label>
              <input
                type="file"
                accept="video/*"
                onChange={handleVideoSampleChange}
              />
              {videoPreview && (
                <div className="video-preview">
                  <video src={videoPreview} controls />
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
              <select
                name="video_duration_preference"
                value={preferences.video_duration_preference}
                onChange={handlePreferenceChange}
              >
                <option value="short">짧음 (15초)</option>
                <option value="medium">보통 (30초)</option>
                <option value="long">길게 (60초+)</option>
              </select>
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
      )}

      {/* Step 3: 완료 */}
      {currentStep === 3 && (
        <div className="onboarding-step completion-step">
          <div className="completion-icon">🎉</div>
          <h2>모든 설정이 완료되었습니다!</h2>
          <p className="step-description">
            이제 AI가 회원님만을 위한 맞춤형 콘텐츠를 생성할 준비가 되었습니다.
          </p>

          <div className="completion-summary">
            <h3>입력하신 정보</h3>
            <ul>
              <li>브랜드: {businessInfo.brand_name}</li>
              <li>업종: {businessInfo.business_type}</li>
              <li>타겟 고객: {businessInfo.target_audience.age_range} {businessInfo.target_audience.gender === 'all' ? '전체' : businessInfo.target_audience.gender}</li>
              {businessInfo.target_audience.interests.length > 0 && (
                <li>관심사: {businessInfo.target_audience.interests.join(', ')}</li>
              )}
            </ul>
          </div>

          <div className="step-actions">
            <button onClick={completeOnboarding} disabled={isLoading} className="btn-primary btn-large">
              {isLoading ? '처리 중...' : '대시보드로 이동'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Onboarding;
