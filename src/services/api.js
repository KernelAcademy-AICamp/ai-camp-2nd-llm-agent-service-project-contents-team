import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터: 모든 요청에 토큰 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터: 401 에러 시 로그아웃 처리
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 인증 API
export const authAPI = {
  // 회원가입
  register: async (userData) => {
    const response = await api.post('/api/auth/register', userData);
    return response.data;
  },

  // 로그인
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  // 로그아웃
  logout: async () => {
    const response = await api.post('/api/auth/logout');
    return response.data;
  },

  // 현재 사용자 정보 조회
  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  // 사용자 정보 수정
  updateUser: async (userData) => {
    const response = await api.put('/api/auth/me', userData);
    return response.data;
  },
};

// Instagram API
export const instagramAPI = {
  // Instagram 계정 연동
  connectAccount: async (accessToken) => {
    const response = await api.post('/api/instagram/connect', null, {
      params: { access_token: accessToken }
    });
    return response.data;
  },

  // 연동된 계정 목록 조회
  getAccounts: async () => {
    const response = await api.get('/api/instagram/accounts');
    return response.data;
  },

  // 게시물 발행
  publishPost: async (postData) => {
    const response = await api.post('/api/instagram/publish', postData);
    return response.data;
  },

  // 발행 이력 조회
  getPosts: async (skip = 0, limit = 20) => {
    const response = await api.get('/api/instagram/posts', {
      params: { skip, limit }
    });
    return response.data;
  },

  // 예약된 게시물 조회
  getScheduledPosts: async (skip = 0, limit = 20) => {
    const response = await api.get('/api/instagram/scheduled', {
      params: { skip, limit }
    });
    return response.data;
  },

  // 계정 연동 해제
  disconnectAccount: async (accountId) => {
    const response = await api.delete(`/api/instagram/accounts/${accountId}`);
    return response.data;
  },
};

export default api;
