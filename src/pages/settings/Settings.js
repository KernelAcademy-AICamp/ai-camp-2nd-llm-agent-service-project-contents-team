import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import './Settings.css';

// ==================== 상수 정의 ====================
const BUSINESS_TYPES = [
  { value: 'food', label: '음식점/카페' },
  { value: 'fashion', label: '패션/의류' },
  { value: 'health', label: '헬스/피트니스' },
  { value: 'education', label: '교육' },
  { value: 'tech', label: '기술/IT' },
  { value: 'retail', label: '소매/유통' },
  { value: 'service', label: '서비스업' },
];

const AGE_RANGES = ['10대', '20대', '30대', '40대', '50대 이상', '전체'];

const GENDERS = [
  { value: 'all', label: '전체' },
  { value: 'male', label: '남성' },
  { value: 'female', label: '여성' },
];

const TEXT_TONES = [
  { value: 'casual', label: '캐주얼' },
  { value: 'professional', label: '전문적' },
  { value: 'friendly', label: '친근한' },
  { value: 'formal', label: '격식체' },
  { value: 'trendy', label: '트렌디' },
  { value: 'luxurious', label: '럭셔리' },
  { value: 'cute', label: '귀여운' },
  { value: 'minimal', label: '미니멀' },
];

const VIDEO_DURATIONS = [
  { value: 'short', label: '짧게 (15-30초)' },
  { value: 'medium', label: '중간 (30-60초)' },
  { value: 'long', label: '길게 (1분 이상)' },
];

const MODAL_TITLES = {
  business: '비즈니스 정보 수정',
  target: '타겟 고객 수정',
  style: '스타일 선호도 수정',
};

// ==================== 헬퍼 함수 ====================
const parseBusinessDescription = (description) => {
  const [mainDescription] = description.split('추가 정보:');
  return { mainDescription: mainDescription.trim() };
};

const getLabel = (options, value) =>
  options.find(opt => opt.value === value)?.label || value;

// ==================== 서브 컴포넌트 ====================
const InfoCard = ({ label, value, className = '' }) => (
  <div className={`info-card ${className}`}>
    <div className="info-label">{label}</div>
    <div className="info-value">{value}</div>
  </div>
);

const FormGroup = ({ label, children }) => (
  <div className="form-group">
    <label>{label}</label>
    {children}
  </div>
);

const SelectField = ({ name, value, options, onChange, placeholder = '선택하세요' }) => (
  <select name={name} value={value || ''} onChange={onChange}>
    <option value="">{placeholder}</option>
    {options.map(opt => (
      <option key={opt.value || opt} value={opt.value || opt}>
        {opt.label || opt}
      </option>
    ))}
  </select>
);

const TextareaField = ({ name, value, onChange, placeholder, rows = 3 }) => (
  <textarea
    name={name}
    value={value || ''}
    onChange={onChange}
    placeholder={placeholder}
    rows={rows}
  />
);

// 비즈니스 정보 수정 폼
const BusinessForm = ({ editData, onChange }) => (
  <>
    <FormGroup label="브랜드명">
      <input
        type="text"
        name="brand_name"
        value={editData.brand_name || ''}
        onChange={onChange}
        placeholder="브랜드명을 입력하세요"
      />
    </FormGroup>
    <FormGroup label="업종">
      <SelectField name="business_type" value={editData.business_type} options={BUSINESS_TYPES} onChange={onChange} />
    </FormGroup>
    <FormGroup label="비즈니스 설명">
      <TextareaField name="business_description" value={editData.business_description} onChange={onChange} placeholder="비즈니스에 대해 설명해주세요" rows={4} />
    </FormGroup>
  </>
);

// 타겟 고객 수정 폼
const TargetForm = ({ editData, onChange, onAddInterest, onRemoveInterest }) => (
  <>
    <FormGroup label="연령대">
      <SelectField name="age_range" value={editData.age_range} options={AGE_RANGES.map(v => ({ value: v, label: v }))} onChange={onChange} />
    </FormGroup>
    <FormGroup label="성별">
      <SelectField name="gender" value={editData.gender} options={GENDERS} onChange={onChange} />
    </FormGroup>
    <FormGroup label="관심사">
      <div className="interest-input-row">
        <input
          type="text"
          name="newInterest"
          value={editData.newInterest || ''}
          onChange={onChange}
          placeholder="관심사 입력"
          onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), onAddInterest())}
        />
        <button type="button" className="btn-add-interest" onClick={onAddInterest}>추가</button>
      </div>
      <div className="edit-interests-tags">
        {(editData.interests || []).map((interest, index) => (
          <span key={index} className="edit-interest-tag">
            {interest}
            <button onClick={() => onRemoveInterest(index)}>×</button>
          </span>
        ))}
      </div>
    </FormGroup>
  </>
);

// 스타일 선호도 수정 폼
const StyleForm = ({ editData, onChange }) => (
  <>
    <FormGroup label="텍스트 톤">
      <SelectField name="text_tone" value={editData.text_tone} options={TEXT_TONES} onChange={onChange} />
    </FormGroup>
    <FormGroup label="텍스트 샘플">
      <TextareaField name="text_style_sample" value={editData.text_style_sample} onChange={onChange} placeholder="선호하는 텍스트 스타일 예시를 입력하세요" />
    </FormGroup>
    <FormGroup label="이미지 스타일 설명">
      <TextareaField name="image_style_description" value={editData.image_style_description} onChange={onChange} placeholder="선호하는 이미지 스타일을 설명해주세요" />
    </FormGroup>
    <FormGroup label="비디오 스타일 설명">
      <TextareaField name="video_style_description" value={editData.video_style_description} onChange={onChange} placeholder="선호하는 비디오 스타일을 설명해주세요" />
    </FormGroup>
    <FormGroup label="선호 비디오 길이">
      <SelectField name="video_duration_preference" value={editData.video_duration_preference} options={VIDEO_DURATIONS} onChange={onChange} />
    </FormGroup>
  </>
);

// ==================== 메인 컴포넌트 ====================
function Settings() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editModal, setEditModal] = useState({ open: false, type: null });
  const [editData, setEditData] = useState({});
  const [saving, setSaving] = useState(false);

  const user = profile?.user;
  const preferences = profile?.preferences;

  // 프로필 조회
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

  useEffect(() => { fetchProfile(); }, []);

  // 로그아웃
  const handleLogout = () => {
    if (window.confirm('로그아웃 하시겠습니까?')) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      navigate('/login');
    }
  };

  // 모달 열기
  const openEditModal = (type) => {
    if (!profile) return;

    const initialData = {
      business: () => ({
        brand_name: user.brand_name || '',
        business_type: user.business_type || '',
        business_description: parseBusinessDescription(user.business_description || '').mainDescription,
      }),
      target: () => ({
        age_range: user.target_audience?.age_range || '',
        gender: user.target_audience?.gender || 'all',
        interests: user.target_audience?.interests || [],
        newInterest: '',
      }),
      style: () => ({
        text_tone: preferences?.text_tone || '',
        text_style_sample: preferences?.text_style_sample || '',
        image_style_description: preferences?.image_style_description || '',
        video_style_description: preferences?.video_style_description || '',
        video_duration_preference: preferences?.video_duration_preference || '',
      }),
    };

    setEditData(initialData[type]?.() || {});
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

  // 관심사 추가/삭제
  const addInterest = () => {
    if (editData.newInterest?.trim()) {
      setEditData(prev => ({
        ...prev,
        interests: [...(prev.interests || []), prev.newInterest.trim()],
        newInterest: '',
      }));
    }
  };

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
      const updatePayload = {
        business: {
          brand_name: editData.brand_name,
          business_type: editData.business_type,
          business_description: editData.business_description,
        },
        target: {
          target_audience: {
            age_range: editData.age_range,
            gender: editData.gender,
            interests: editData.interests,
          },
        },
        style: {
          preferences: {
            text_tone: editData.text_tone,
            text_style_sample: editData.text_style_sample,
            image_style_description: editData.image_style_description,
            video_style_description: editData.video_style_description,
            video_duration_preference: editData.video_duration_preference,
          },
        },
      };

      await api.put('/api/user/profile', updatePayload[editModal.type]);
      await fetchProfile();
      closeEditModal();
    } catch (err) {
      console.error('프로필 수정 실패:', err);
      alert('저장에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setSaving(false);
    }
  };

  // 모달 폼 렌더링
  const renderModalForm = () => {
    const forms = {
      business: <BusinessForm editData={editData} onChange={handleInputChange} />,
      target: <TargetForm editData={editData} onChange={handleInputChange} onAddInterest={addInterest} onRemoveInterest={removeInterest} />,
      style: <StyleForm editData={editData} onChange={handleInputChange} />,
    };
    return forms[editModal.type] || null;
  };

  return (
    <div className="settings-page">
      {/* 헤더 */}
      <div className="settings-header">
        <div className="header-left">
          <h2>설정</h2>
          <p className="header-subtitle">플랫폼 연동 및 계정 설정을 관리하세요</p>
        </div>
      </div>

      {/* 계정 섹션 */}
      <div className="settings-section">
        <div className="section-header"><h3>계정</h3></div>
        <div className="account-actions">
          <Link to="/mypage" className="account-link-card">
            <div className="account-link-content">
              <div className="account-link-title">계정 정보</div>
              <div className="account-link-description">이름, 이메일, 프로필 이미지 등 기본 정보를 확인하세요</div>
            </div>
            <span className="account-link-arrow">→</span>
          </Link>
          <button className="logout-button" onClick={handleLogout}>로그아웃</button>
        </div>
      </div>

      {/* 비즈니스 정보 */}
      {!loading && user?.onboarding_completed && (
        <div className="settings-section">
          <div className="section-header">
            <h3>비즈니스 정보</h3>
            <button className="btn-edit" onClick={() => openEditModal('business')}>수정</button>
          </div>
          <div className="profile-info-grid">
            {user.brand_name && <InfoCard label="브랜드명" value={user.brand_name} />}
            {user.business_type && <InfoCard label="업종" value={getLabel(BUSINESS_TYPES, user.business_type)} className="business-type" />}
            {user.business_description && (
              <InfoCard label="비즈니스 설명" value={parseBusinessDescription(user.business_description).mainDescription} className="full-width description" />
            )}
          </div>
        </div>
      )}

      {/* 타겟 고객 */}
      {!loading && user?.target_audience && (
        <div className="settings-section">
          <div className="section-header">
            <h3>타겟 고객</h3>
            <button className="btn-edit" onClick={() => openEditModal('target')}>수정</button>
          </div>
          <div className="profile-info-grid">
            {user.target_audience.age_range && <InfoCard label="연령대" value={user.target_audience.age_range} />}
            {user.target_audience.gender && <InfoCard label="성별" value={getLabel(GENDERS, user.target_audience.gender)} />}
            {user.target_audience.interests?.length > 0 && (
              <div className="info-card full-width">
                <div className="info-label">관심사</div>
                <div className="interests-tags">
                  {user.target_audience.interests.map((interest, idx) => (
                    <span key={idx} className="interest-tag">{interest}</span>
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
            <button className="btn-edit" onClick={() => openEditModal('style')}>수정</button>
          </div>
          <div className="preferences-grid">
            {(preferences.text_style_sample || preferences.text_tone) && (
              <div className="preference-card">
                <h4>텍스트 스타일</h4>
                {preferences.text_tone && (
                  <div className="preference-item">
                    <span className="preference-label">톤</span>
                    <span className="tone-badge">{getLabel(TEXT_TONES, preferences.text_tone)}</span>
                  </div>
                )}
                {preferences.text_style_sample && (
                  <div className="preference-item">
                    <span className="preference-label">샘플</span>
                    <div className="text-sample">{preferences.text_style_sample}</div>
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
                    <img src={preferences.image_style_sample_url} alt="이미지 스타일 샘플" className="style-sample-image" />
                  </div>
                )}
                {preferences.image_style_description && (
                  <div className="preference-item">
                    <span className="preference-label">설명</span>
                    <p className="preference-description">{preferences.image_style_description}</p>
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
                    <p className="preference-description">{preferences.video_style_description}</p>
                  </div>
                )}
                {preferences.video_duration_preference && (
                  <div className="preference-item">
                    <span className="preference-label">선호 길이</span>
                    <span className="preference-value">{getLabel(VIDEO_DURATIONS, preferences.video_duration_preference)}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 온보딩 미완료 안내 */}
      {!loading && user && !user.onboarding_completed && (
        <div className="settings-section onboarding-prompt">
          <div className="prompt-content">
            <h3>온보딩을 완료하지 않으셨네요!</h3>
            <p>비즈니스 정보를 입력하면 더 나은 콘텐츠 추천을 받을 수 있습니다.</p>
            <button onClick={() => navigate('/onboarding')} className="onboarding-button">온보딩 시작하기</button>
          </div>
        </div>
      )}

      {/* 수정 모달 */}
      {editModal.open && (
        <div className="modal-overlay" onClick={closeEditModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{MODAL_TITLES[editModal.type]}</h3>
              <button className="modal-close" onClick={closeEditModal}>×</button>
            </div>
            <div className="modal-body">{renderModalForm()}</div>
            <div className="modal-footer">
              <button className="btn-cancel" onClick={closeEditModal}>취소</button>
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

export default Settings;
