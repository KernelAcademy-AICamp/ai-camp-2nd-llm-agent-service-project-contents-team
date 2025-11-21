import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './MyPage.css';

const MyPage = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/api/user/profile');
      setProfile(response.data);
    } catch (err) {
      console.error('프로필 조회 실패:', err);
      setError('프로필 정보를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="mypage-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>프로필 정보를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mypage-container">
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <p>{error}</p>
          <button onClick={fetchProfile} className="retry-button">
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="mypage-container">
        <div className="empty-state">
          <p>프로필 정보가 없습니다.</p>
        </div>
      </div>
    );
  }

  const { user, preferences } = profile;

  return (
    <div className="mypage-container">
      <div className="mypage-header">
        <h1>마이페이지</h1>
        <p className="subtitle">입력하신 정보를 확인하고 관리하세요</p>
      </div>

      {/* 기본 정보 섹션 */}
      <div className="profile-section">
        <div className="section-header">
          <h2>기본 정보</h2>
          <span className="provider-badge">{user.oauth_provider}</span>
        </div>

        <div className="profile-info-grid">
          <div className="info-card">
            <div className="info-label">이름</div>
            <div className="info-value">{user.full_name || user.username}</div>
          </div>

          <div className="info-card">
            <div className="info-label">이메일</div>
            <div className="info-value">{user.email}</div>
          </div>

          {user.profile_image && (
            <div className="info-card profile-image-card">
              <div className="info-label">프로필 이미지</div>
              <img
                src={user.profile_image}
                alt="프로필"
                className="profile-image"
              />
            </div>
          )}
        </div>
      </div>

      {/* 비즈니스 정보 섹션 */}
      {user.onboarding_completed && (
        <div className="profile-section">
          <div className="section-header">
            <h2>비즈니스 정보</h2>
            <span className="status-badge completed">온보딩 완료</span>
          </div>

          <div className="profile-info-grid">
            {user.brand_name && (
              <div className="info-card">
                <div className="info-label">브랜드명</div>
                <div className="info-value">{user.brand_name}</div>
              </div>
            )}

            {user.business_type && (
              <div className="info-card">
                <div className="info-label">업종</div>
                <div className="info-value business-type">
                  {getBusinessTypeLabel(user.business_type)}
                </div>
              </div>
            )}

            {user.business_description && (
              <div className="info-card full-width">
                <div className="info-label">비즈니스 설명</div>
                <div className="info-value description">
                  {user.business_description}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 타겟 고객 정보 섹션 */}
      {user.target_audience && (
        <div className="profile-section">
          <div className="section-header">
            <h2>타겟 고객</h2>
          </div>

          <div className="profile-info-grid">
            {user.target_audience.age_range && (
              <div className="info-card">
                <div className="info-label">연령대</div>
                <div className="info-value">{user.target_audience.age_range}</div>
              </div>
            )}

            {user.target_audience.gender && (
              <div className="info-card">
                <div className="info-label">성별</div>
                <div className="info-value">{getGenderLabel(user.target_audience.gender)}</div>
              </div>
            )}

            {user.target_audience.interests && user.target_audience.interests.length > 0 && (
              <div className="info-card full-width">
                <div className="info-label">관심사</div>
                <div className="interests-tags">
                  {user.target_audience.interests.map((interest, index) => (
                    <span key={index} className="interest-tag">
                      {interest}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 스타일 선호도 섹션 */}
      {preferences && (
        <div className="profile-section">
          <div className="section-header">
            <h2>스타일 선호도</h2>
          </div>

          <div className="preferences-grid">
            {/* 텍스트 스타일 */}
            {(preferences.text_style_sample || preferences.text_tone) && (
              <div className="preference-card">
                <h3>텍스트 스타일</h3>
                {preferences.text_tone && (
                  <div className="preference-item">
                    <span className="preference-label">톤</span>
                    <span className="preference-value tone-badge">
                      {getToneLabel(preferences.text_tone)}
                    </span>
                  </div>
                )}
                {preferences.text_style_sample && (
                  <div className="preference-item">
                    <span className="preference-label">샘플</span>
                    <div className="text-sample">
                      {preferences.text_style_sample}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 이미지 스타일 */}
            {(preferences.image_style_sample_url || preferences.image_style_description) && (
              <div className="preference-card">
                <h3>이미지 스타일</h3>
                {preferences.image_style_sample_url && (
                  <div className="preference-item">
                    <span className="preference-label">샘플 이미지</span>
                    <img
                      src={preferences.image_style_sample_url}
                      alt="이미지 스타일 샘플"
                      className="style-sample-image"
                    />
                  </div>
                )}
                {preferences.image_style_description && (
                  <div className="preference-item">
                    <span className="preference-label">설명</span>
                    <p className="preference-description">
                      {preferences.image_style_description}
                    </p>
                  </div>
                )}
                {preferences.image_color_palette && preferences.image_color_palette.length > 0 && (
                  <div className="preference-item">
                    <span className="preference-label">선호 색상</span>
                    <div className="color-palette">
                      {preferences.image_color_palette.map((color, index) => (
                        <div
                          key={index}
                          className="color-swatch"
                          style={{ backgroundColor: color }}
                          title={color}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 비디오 스타일 */}
            {(preferences.video_style_sample_url || preferences.video_style_description) && (
              <div className="preference-card">
                <h3>비디오 스타일</h3>
                {preferences.video_style_sample_url && (
                  <div className="preference-item">
                    <span className="preference-label">샘플 비디오</span>
                    <video
                      src={preferences.video_style_sample_url}
                      controls
                      className="style-sample-video"
                    />
                  </div>
                )}
                {preferences.video_style_description && (
                  <div className="preference-item">
                    <span className="preference-label">설명</span>
                    <p className="preference-description">
                      {preferences.video_style_description}
                    </p>
                  </div>
                )}
                {preferences.video_duration_preference && (
                  <div className="preference-item">
                    <span className="preference-label">선호 길이</span>
                    <span className="preference-value">
                      {getDurationLabel(preferences.video_duration_preference)}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 온보딩 미완료 상태 */}
      {!user.onboarding_completed && (
        <div className="profile-section onboarding-prompt">
          <div className="prompt-content">
            <h2>온보딩을 완료하지 않으셨네요!</h2>
            <p>비즈니스 정보를 입력하면 더 나은 콘텐츠 추천을 받을 수 있습니다.</p>
            <button
              onClick={() => window.location.href = '/onboarding'}
              className="onboarding-button"
            >
              온보딩 시작하기
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// 헬퍼 함수들
const getBusinessTypeLabel = (type) => {
  const labels = {
    'food': '음식점/카페',
    'fashion': '패션/의류',
    'health': '헬스/피트니스',
    'education': '교육',
    'tech': '기술/IT',
    'retail': '소매/유통',
    'service': '서비스업'
  };
  return labels[type] || type;
};

const getGenderLabel = (gender) => {
  const labels = {
    'all': '전체',
    'male': '남성',
    'female': '여성'
  };
  return labels[gender] || gender;
};

const getToneLabel = (tone) => {
  const labels = {
    'casual': '캐주얼',
    'professional': '전문적',
    'friendly': '친근한',
    'formal': '격식있는'
  };
  return labels[tone] || tone;
};

const getDurationLabel = (duration) => {
  const labels = {
    'short': '짧게 (15-30초)',
    'medium': '중간 (30-60초)',
    'long': '길게 (1분 이상)'
  };
  return labels[duration] || duration;
};

export default MyPage;
