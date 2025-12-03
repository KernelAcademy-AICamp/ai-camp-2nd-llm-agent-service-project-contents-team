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

  const { user } = profile;

  return (
    <div className="mypage-container">
      <div className="mypage-header">
        <h1>계정 정보</h1>
        <p className="subtitle">계정 정보를 확인하고 관리하세요</p>
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
    </div>
  );
};

export default MyPage;
