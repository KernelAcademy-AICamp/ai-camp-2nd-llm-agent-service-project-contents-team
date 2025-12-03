import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api, { youtubeAPI, facebookAPI, instagramAPI, twitterAPI } from '../../services/api';
import './Settings.css';

function Settings() {
  const navigate = useNavigate();
  const [youtubeConnection, setYoutubeConnection] = useState(null);
  const [facebookConnection, setFacebookConnection] = useState(null);
  const [instagramConnection, setInstagramConnection] = useState(null);
  const [twitterConnection, setTwitterConnection] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editModal, setEditModal] = useState({ open: false, type: null });
  const [editData, setEditData] = useState({});
  const [saving, setSaving] = useState(false);

  // 로그아웃 처리
  const handleLogout = () => {
    if (window.confirm('로그아웃 하시겠습니까?')) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      navigate('/login');
    }
  };

  useEffect(() => {
    const fetchYoutubeStatus = async () => {
      try {
        const data = await youtubeAPI.getStatus();
        setYoutubeConnection(data);
      } catch (err) {
        console.error('Failed to fetch YouTube status:', err);
      }
    };

    const fetchFacebookStatus = async () => {
      try {
        const data = await facebookAPI.getStatus();
        setFacebookConnection(data);
      } catch (err) {
        console.error('Failed to fetch Facebook status:', err);
      }
    };

    const fetchInstagramStatus = async () => {
      try {
        const data = await instagramAPI.getStatus();
        setInstagramConnection(data);
      } catch (err) {
        console.error('Failed to fetch Instagram status:', err);
      }
    };

    const fetchTwitterStatus = async () => {
      try {
        const data = await twitterAPI.getStatus();
        setTwitterConnection(data);
      } catch (err) {
        console.error('Failed to fetch X status:', err);
      }
    };

    const fetchProfile = async () => {
      try {
        const response = await api.get('/api/user/profile');
        setProfile(response.data);
      } catch (err) {
        console.error('Failed to fetch profile:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchYoutubeStatus();
    fetchFacebookStatus();
    fetchInstagramStatus();
    fetchTwitterStatus();
    fetchProfile();
  }, []);

  // 프로필 새로고침
  const refreshProfile = async () => {
    try {
      const response = await api.get('/api/user/profile');
      setProfile(response.data);
    } catch (err) {
      console.error('Failed to refresh profile:', err);
    }
  };

  // 수정 모달 열기
  const openEditModal = (type) => {
    if (!profile) return;
    const { user, preferences } = profile;

    if (type === 'business') {
      const parsed = parseBusinessDescription(user.business_description || '');
      setEditData({
        brand_name: user.brand_name || '',
        business_type: user.business_type || '',
        business_description: parsed.mainDescription || '',
      });
    } else if (type === 'target') {
      setEditData({
        age_range: user.target_audience?.age_range || '',
        gender: user.target_audience?.gender || 'all',
        interests: user.target_audience?.interests || [],
        newInterest: '',
      });
    } else if (type === 'style') {
      setEditData({
        text_tone: preferences?.text_tone || '',
        text_style_sample: preferences?.text_style_sample || '',
        image_style_description: preferences?.image_style_description || '',
        video_style_description: preferences?.video_style_description || '',
        video_duration_preference: preferences?.video_duration_preference || '',
      });
    }

    setEditModal({ open: true, type });
  };

  // 모달 닫기
  const closeEditModal = () => {
    setEditModal({ open: false, type: null });
    setEditData({});
  };

  // 입력값 변경
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEditData(prev => ({ ...prev, [name]: value }));
  };

  // 관심사 추가
  const addInterest = () => {
    if (editData.newInterest?.trim()) {
      setEditData(prev => ({
        ...prev,
        interests: [...(prev.interests || []), prev.newInterest.trim()],
        newInterest: '',
      }));
    }
  };

  // 관심사 삭제
  const removeInterest = (index) => {
    setEditData(prev => ({
      ...prev,
      interests: prev.interests.filter((_, i) => i !== index),
    }));
  };

  // 저장
  const handleSave = async () => {
    setSaving(true);
    try {
      let updateData = {};

      if (editModal.type === 'business') {
        updateData = {
          brand_name: editData.brand_name,
          business_type: editData.business_type,
          business_description: editData.business_description,
        };
      } else if (editModal.type === 'target') {
        updateData = {
          target_audience: {
            age_range: editData.age_range,
            gender: editData.gender,
            interests: editData.interests,
          },
        };
      } else if (editModal.type === 'style') {
        updateData = {
          preferences: {
            text_tone: editData.text_tone,
            text_style_sample: editData.text_style_sample,
            image_style_description: editData.image_style_description,
            video_style_description: editData.video_style_description,
            video_duration_preference: editData.video_duration_preference,
          },
        };
      }

      await api.put('/api/user/profile', updateData);
      await refreshProfile();
      closeEditModal();
    } catch (err) {
      console.error('프로필 수정 실패:', err);
      alert('저장에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setSaving(false);
    }
  };

  const user = profile?.user;
  const preferences = profile?.preferences;

  return (
    <div className="settings-page">
      <div className="settings-header">
        <div className="header-left">
          <h2>설정</h2>
          <p className="header-subtitle">플랫폼 연동 및 계정 설정을 관리하세요</p>
        </div>
      </div>

      {/* 계정 정보 바로가기 */}
      <div className="settings-section">
        <div className="section-header">
          <h3>계정</h3>
        </div>
        <div className="account-actions">
          <Link to="/mypage" className="account-link-card">
            <div className="account-link-content">
              <div className="account-link-title">계정 정보</div>
              <div className="account-link-description">이름, 이메일, 프로필 이미지 등 기본 정보를 확인하세요</div>
            </div>
            <span className="account-link-arrow">→</span>
          </Link>
          <button className="logout-button" onClick={handleLogout}>
            로그아웃
          </button>
        </div>
      </div>

      {/* 비즈니스 정보 */}
      {!loading && user?.onboarding_completed && (
        <div className="settings-section">
          <div className="section-header">
            <h3>비즈니스 정보</h3>
            <button className="btn-edit" onClick={() => openEditModal('business')}>
              수정
            </button>
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
                  {parseBusinessDescription(user.business_description).mainDescription}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 타겟 고객 */}
      {!loading && user?.target_audience && (
        <div className="settings-section">
          <div className="section-header">
            <h3>타겟 고객</h3>
            <button className="btn-edit" onClick={() => openEditModal('target')}>
              수정
            </button>
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

      {/* 스타일 선호도 */}
      {!loading && preferences && (
        <div className="settings-section">
          <div className="section-header">
            <h3>스타일 선호도</h3>
            <button className="btn-edit" onClick={() => openEditModal('style')}>
              수정
            </button>
          </div>
          <div className="preferences-grid">
            {(preferences.text_style_sample || preferences.text_tone) && (
              <div className="preference-card">
                <h4>텍스트 스타일</h4>
                {preferences.text_tone && (
                  <div className="preference-item">
                    <span className="preference-label">톤</span>
                    <span className="tone-badge">
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
            {(preferences.image_style_sample_url || preferences.image_style_description) && (
              <div className="preference-card">
                <h4>이미지 스타일</h4>
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
              </div>
            )}
            {(preferences.video_style_sample_url || preferences.video_style_description) && (
              <div className="preference-card">
                <h4>비디오 스타일</h4>
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

      {/* 온보딩 미완료 */}
      {!loading && user && !user.onboarding_completed && (
        <div className="settings-section onboarding-prompt">
          <div className="prompt-content">
            <h3>온보딩을 완료하지 않으셨네요!</h3>
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

      {/* 소셜 미디어 플랫폼 */}
      <div className="settings-section">
        <div className="section-header">
          <h3>소셜 미디어 플랫폼</h3>
          <span className="section-count">4개 플랫폼</span>
        </div>
        <p className="section-description">소셜 미디어 플랫폼을 연동하여 콘텐츠를 관리하세요.</p>
        <div className="platform-list">
          <Link to="/youtube" className={`platform-item ${youtubeConnection ? 'connected' : ''}`}>
            <div className="platform-info">
              <div className="platform-name">YouTube</div>
              <div className="platform-status">
                {youtubeConnection
                  ? `연동됨 - ${youtubeConnection.channel_title}`
                  : '연동 가능'}
              </div>
            </div>
            <span className="btn-connect">
              {youtubeConnection ? '관리하기' : '연동하기'}
            </span>
          </Link>
          <Link to="/facebook" className={`platform-item ${facebookConnection ? 'connected' : ''}`}>
            <div className="platform-info">
              <div className="platform-name">Facebook</div>
              <div className="platform-status">
                {facebookConnection
                  ? `연동됨 - ${facebookConnection.page_name || facebookConnection.facebook_user_name}`
                  : '연동 가능'}
              </div>
            </div>
            <span className="btn-connect">
              {facebookConnection ? '관리하기' : '연동하기'}
            </span>
          </Link>
          <Link to="/instagram" className={`platform-item ${instagramConnection ? 'connected' : ''}`}>
            <div className="platform-info">
              <div className="platform-name">Instagram</div>
              <div className="platform-status">
                {instagramConnection
                  ? `연동됨 - @${instagramConnection.instagram_username}`
                  : '연동 가능'}
              </div>
            </div>
            <span className="btn-connect">
              {instagramConnection ? '관리하기' : '연동하기'}
            </span>
          </Link>
          <Link to="/x" className={`platform-item ${twitterConnection ? 'connected' : ''}`}>
            <div className="platform-info">
              <div className="platform-name">X</div>
              <div className="platform-status">
                {twitterConnection
                  ? `연동됨 - @${twitterConnection.username}`
                  : '연동 가능'}
              </div>
            </div>
            <span className="btn-connect">
              {twitterConnection ? '관리하기' : '연동하기'}
            </span>
          </Link>
        </div>
      </div>

      {/* AI API 설정 */}
      <div className="settings-section">
        <div className="section-header">
          <h3>AI 설정</h3>
        </div>
        <div className="api-info">
          <p>현재 지원되는 AI 기능:</p>
          <ul>
            <li>AI 이미지 생성 (Google Gemini, Stable Diffusion)</li>
            <li>프롬프트 최적화 (Claude, Gemini)</li>
            <li>AI 동영상 제작 (개발 중)</li>
          </ul>
          <p className="mt-3">API 키는 <code>.env</code> 파일에서 관리됩니다.</p>
        </div>
      </div>

      {/* 수정 모달 */}
      {editModal.open && (
        <div className="modal-overlay" onClick={closeEditModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {editModal.type === 'business' && '비즈니스 정보 수정'}
                {editModal.type === 'target' && '타겟 고객 수정'}
                {editModal.type === 'style' && '스타일 선호도 수정'}
              </h3>
              <button className="modal-close" onClick={closeEditModal}>×</button>
            </div>

            <div className="modal-body">
              {/* 비즈니스 정보 수정 폼 */}
              {editModal.type === 'business' && (
                <>
                  <div className="form-group">
                    <label>브랜드명</label>
                    <input
                      type="text"
                      name="brand_name"
                      value={editData.brand_name || ''}
                      onChange={handleInputChange}
                      placeholder="브랜드명을 입력하세요"
                    />
                  </div>
                  <div className="form-group">
                    <label>업종</label>
                    <select
                      name="business_type"
                      value={editData.business_type || ''}
                      onChange={handleInputChange}
                    >
                      <option value="">선택하세요</option>
                      <option value="food">음식점/카페</option>
                      <option value="fashion">패션/의류</option>
                      <option value="health">헬스/피트니스</option>
                      <option value="education">교육</option>
                      <option value="tech">기술/IT</option>
                      <option value="retail">소매/유통</option>
                      <option value="service">서비스업</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>비즈니스 설명</label>
                    <textarea
                      name="business_description"
                      value={editData.business_description || ''}
                      onChange={handleInputChange}
                      placeholder="비즈니스에 대해 설명해주세요"
                      rows={4}
                    />
                  </div>
                </>
              )}

              {/* 타겟 고객 수정 폼 */}
              {editModal.type === 'target' && (
                <>
                  <div className="form-group">
                    <label>연령대</label>
                    <select
                      name="age_range"
                      value={editData.age_range || ''}
                      onChange={handleInputChange}
                    >
                      <option value="">선택하세요</option>
                      <option value="10대">10대</option>
                      <option value="20대">20대</option>
                      <option value="30대">30대</option>
                      <option value="40대">40대</option>
                      <option value="50대 이상">50대 이상</option>
                      <option value="전체">전체</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>성별</label>
                    <select
                      name="gender"
                      value={editData.gender || 'all'}
                      onChange={handleInputChange}
                    >
                      <option value="all">전체</option>
                      <option value="male">남성</option>
                      <option value="female">여성</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>관심사</label>
                    <div className="interest-input-row">
                      <input
                        type="text"
                        name="newInterest"
                        value={editData.newInterest || ''}
                        onChange={handleInputChange}
                        placeholder="관심사 입력"
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addInterest())}
                      />
                      <button type="button" className="btn-add-interest" onClick={addInterest}>
                        추가
                      </button>
                    </div>
                    <div className="edit-interests-tags">
                      {(editData.interests || []).map((interest, index) => (
                        <span key={index} className="edit-interest-tag">
                          {interest}
                          <button onClick={() => removeInterest(index)}>×</button>
                        </span>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* 스타일 선호도 수정 폼 */}
              {editModal.type === 'style' && (
                <>
                  <div className="form-group">
                    <label>텍스트 톤</label>
                    <select
                      name="text_tone"
                      value={editData.text_tone || ''}
                      onChange={handleInputChange}
                    >
                      <option value="">선택하세요</option>
                      <option value="casual">캐주얼</option>
                      <option value="professional">전문적</option>
                      <option value="friendly">친근한</option>
                      <option value="formal">격식있는</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>텍스트 샘플</label>
                    <textarea
                      name="text_style_sample"
                      value={editData.text_style_sample || ''}
                      onChange={handleInputChange}
                      placeholder="선호하는 텍스트 스타일 예시를 입력하세요"
                      rows={3}
                    />
                  </div>
                  <div className="form-group">
                    <label>이미지 스타일 설명</label>
                    <textarea
                      name="image_style_description"
                      value={editData.image_style_description || ''}
                      onChange={handleInputChange}
                      placeholder="선호하는 이미지 스타일을 설명해주세요"
                      rows={3}
                    />
                  </div>
                  <div className="form-group">
                    <label>비디오 스타일 설명</label>
                    <textarea
                      name="video_style_description"
                      value={editData.video_style_description || ''}
                      onChange={handleInputChange}
                      placeholder="선호하는 비디오 스타일을 설명해주세요"
                      rows={3}
                    />
                  </div>
                  <div className="form-group">
                    <label>선호 비디오 길이</label>
                    <select
                      name="video_duration_preference"
                      value={editData.video_duration_preference || ''}
                      onChange={handleInputChange}
                    >
                      <option value="">선택하세요</option>
                      <option value="short">짧게 (15-30초)</option>
                      <option value="medium">중간 (30-60초)</option>
                      <option value="long">길게 (1분 이상)</option>
                    </select>
                  </div>
                </>
              )}
            </div>

            <div className="modal-footer">
              <button className="btn-cancel" onClick={closeEditModal}>
                취소
              </button>
              <button className="btn-save" onClick={handleSave} disabled={saving}>
                {saving ? '저장 중...' : '저장'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 헬퍼 함수들
const parseBusinessDescription = (description) => {
  const parts = description.split('추가 정보:');
  const mainDescription = parts[0].trim();
  return { mainDescription };
};

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

export default Settings;
