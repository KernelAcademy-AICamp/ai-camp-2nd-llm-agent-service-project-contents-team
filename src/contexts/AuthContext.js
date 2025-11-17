import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 초기 로드 시 로컬 스토리지에서 사용자 정보 확인
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      const savedUser = localStorage.getItem('user');

      if (token && savedUser) {
        try {
          // 토큰이 유효한지 확인
          const currentUser = await authAPI.getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          console.error('Token validation failed:', error);
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  // 참고: 회원가입과 로그인 함수는 OAuth2.0 소셜 로그인으로 대체되었습니다.
  // 모든 인증은 /oauth/callback 페이지에서 처리됩니다.

  // 회원가입 (현재 사용되지 않음 - OAuth2.0로 대체)
  const register = async (userData) => {
    try {
      setError(null);
      const newUser = await authAPI.register(userData);
      return { success: true, user: newUser };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || '회원가입에 실패했습니다.';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  // 로그인 (현재 사용되지 않음 - OAuth2.0로 대체)
  const login = async (username, password) => {
    try {
      setError(null);
      const data = await authAPI.login(username, password);

      // 토큰 저장
      localStorage.setItem('access_token', data.access_token);

      // 사용자 정보 가져오기
      const currentUser = await authAPI.getCurrentUser();
      setUser(currentUser);
      localStorage.setItem('user', JSON.stringify(currentUser));

      return { success: true, user: currentUser };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || '로그인에 실패했습니다.';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  // 로그아웃
  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // 로컬 스토리지 정리
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      setUser(null);
    }
  };

  // 사용자 정보 업데이트
  const updateUserProfile = async (userData) => {
    try {
      setError(null);
      const updatedUser = await authAPI.updateUser(userData);
      setUser(updatedUser);
      localStorage.setItem('user', JSON.stringify(updatedUser));
      return { success: true, user: updatedUser };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || '정보 수정에 실패했습니다.';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const value = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    register,
    login,
    logout,
    updateUserProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom Hook
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
