import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './Register.css';

function Register() {
  const navigate = useNavigate();
  const { register, error } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    full_name: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setLocalError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setLocalError('');
    setSuccessMessage('');

    // 유효성 검사
    if (!formData.email || !formData.username || !formData.password || !formData.confirmPassword) {
      setLocalError('필수 항목을 모두 입력해주세요.');
      setIsLoading(false);
      return;
    }

    if (formData.password.length < 6) {
      setLocalError('비밀번호는 6자 이상이어야 합니다.');
      setIsLoading(false);
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setLocalError('비밀번호가 일치하지 않습니다.');
      setIsLoading(false);
      return;
    }

    // 회원가입 요청
    const result = await register({
      email: formData.email,
      username: formData.username,
      password: formData.password,
      full_name: formData.full_name || null,
    });

    if (result.success) {
      setSuccessMessage('회원가입이 완료되었습니다! 로그인 페이지로 이동합니다...');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } else {
      setLocalError(result.error);
    }

    setIsLoading(false);
  };

  return (
    <div className="register-container">
      <div className="register-box">
        <div className="register-header">
          <h1>회원가입</h1>
          <p>계정을 생성하고 콘텐츠 크리에이터를 시작하세요</p>
        </div>

        {(localError || error) && (
          <div className="error-message">{localError || error}</div>
        )}

        {successMessage && (
          <div className="success-message">{successMessage}</div>
        )}

        <form onSubmit={handleSubmit} className="register-form">
          <div className="form-group">
            <label htmlFor="email">
              이메일 <span className="required">*</span>
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="example@email.com"
              disabled={isLoading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="username">
              사용자명 <span className="required">*</span>
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="사용자명 (3자 이상)"
              disabled={isLoading}
              required
              minLength={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="full_name">이름 (선택)</label>
            <input
              type="text"
              id="full_name"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="홍길동"
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">
              비밀번호 <span className="required">*</span>
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="비밀번호 (6자 이상)"
              disabled={isLoading}
              required
              minLength={6}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">
              비밀번호 확인 <span className="required">*</span>
            </label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="비밀번호를 다시 입력하세요"
              disabled={isLoading}
              required
            />
          </div>

          <button type="submit" className="register-button" disabled={isLoading}>
            {isLoading ? '가입 중...' : '회원가입'}
          </button>
        </form>

        <div className="register-footer">
          <p>
            이미 계정이 있으신가요? <Link to="/login">로그인</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Register;
