import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authAPI } from '../services/api';
import './OAuthCallback.css';

function OAuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const params = new URLSearchParams(location.search);
        const token = params.get('token');
        const provider = params.get('provider');

        if (!token) {
          setStatus('error');
          setTimeout(() => navigate('/login'), 2000);
          return;
        }

        // 토큰 저장
        localStorage.setItem('access_token', token);

        // 사용자 정보 가져오기
        const userInfo = await authAPI.getCurrentUser();
        localStorage.setItem('user', JSON.stringify(userInfo));

        setStatus('success');

        // 대시보드로 리다이렉트
        setTimeout(() => {
          window.location.href = '/';
        }, 1000);

      } catch (error) {
        console.error('OAuth callback error:', error);
        setStatus('error');
        setTimeout(() => navigate('/login'), 2000);
      }
    };

    handleCallback();
  }, [location, navigate]);

  return (
    <div className="oauth-callback-container">
      <div className="oauth-callback-box">
        {status === 'loading' && (
          <>
            <div className="spinner"></div>
            <p>로그인 처리 중...</p>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="success-icon">✓</div>
            <p>로그인 성공! 리다이렉트 중...</p>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="error-icon">✗</div>
            <p>로그인 실패. 다시 시도해주세요.</p>
          </>
        )}
      </div>
    </div>
  );
}

export default OAuthCallback;
