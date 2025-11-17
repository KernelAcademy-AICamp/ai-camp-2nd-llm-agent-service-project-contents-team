import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Login.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [localError, setLocalError] = useState('');

  // URL에서 OAuth 에러 확인
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('error') === 'oauth_failed') {
      setLocalError('소셜 로그인에 실패했습니다. 다시 시도해주세요.');
    }
  }, [location]);

  const handleSocialLogin = (provider) => {
    window.location.href = `${API_BASE_URL}/api/oauth/${provider}/login`;
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <h1>로그인</h1>
          <p>소셜 계정으로 간편하게 시작하세요</p>
        </div>

        {localError && (
          <div className="error-message">{localError}</div>
        )}

        <div className="social-login">
          <button
            className="social-btn google"
            onClick={() => handleSocialLogin('google')}
            type="button"
          >
            <svg width="18" height="18" viewBox="0 0 18 18">
              <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 0 0 2.38-5.88c0-.57-.05-.66-.15-1.18z"/>
              <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 0 1-7.18-2.54H1.83v2.07A8 8 0 0 0 8.98 17z"/>
              <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 0 1 0-3.04V5.41H1.83a8 8 0 0 0 0 7.18l2.67-2.07z"/>
              <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 0 0 1.83 5.4L4.5 7.49a4.77 4.77 0 0 1 4.48-3.3z"/>
            </svg>
            Google로 계속하기
          </button>

          <button
            className="social-btn kakao"
            onClick={() => handleSocialLogin('kakao')}
            type="button"
          >
            <svg width="18" height="18" viewBox="0 0 18 18">
              <path fill="#000000" d="M9 3C5.13 3 2 5.57 2 8.75c0 2.03 1.31 3.82 3.29 4.88-.14.5-.9 3.1-.9 3.1-.02.07-.03.14 0 .2.03.06.08.1.15.1.12 0 3.67-2.42 3.67-2.42.26.03.53.05.79.05 3.87 0 7-2.57 7-5.75S12.87 3 9 3z"/>
            </svg>
            카카오로 계속하기
          </button>

          <button
            className="social-btn facebook"
            onClick={() => handleSocialLogin('facebook')}
            type="button"
          >
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path fill="#1877F2" d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
            </svg>
            Facebook으로 계속하기
          </button>
        </div>
      </div>
    </div>
  );
}

export default Login;
