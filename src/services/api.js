import axios from 'axios';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
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

// ==========================================
// 인증 API
// ==========================================
export const authAPI = {
  // 현재 사용자 정보 조회
  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  // 사용자 정보 업데이트
  updateUser: async (userData) => {
    const response = await api.put('/api/auth/me', userData);
    return response.data;
  },

  // 로그아웃
  logout: async () => {
    const response = await api.post('/api/auth/logout');
    return response.data;
  },

  // 회원가입 (현재 사용 안 함 - OAuth로 대체)
  register: async (userData) => {
    const response = await api.post('/api/auth/register', userData);
    return response.data;
  },

  // 로그인 (현재 사용 안 함 - OAuth로 대체)
  login: async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },
};

// ==========================================
// 이미지 생성 API
// ==========================================
export const imageAPI = {
  // AI 이미지 생성
  generateImage: async (data) => {
    const response = await api.post('/api/generate-image', data);
    return response.data;
  },
};

// ==========================================
// YouTube API
// ==========================================
export const youtubeAPI = {
  // 연동 상태 확인
  getStatus: async () => {
    const response = await api.get('/api/youtube/status');
    return response.data;
  },

  // 연동 해제
  disconnect: async () => {
    const response = await api.delete('/api/youtube/disconnect');
    return response.data;
  },

  // 채널 정보 새로고침
  refreshChannel: async () => {
    const response = await api.post('/api/youtube/refresh-channel');
    return response.data;
  },

  // 동영상 목록 조회
  getVideos: async (skip = 0, limit = 20) => {
    const response = await api.get(`/api/youtube/videos?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // 동영상 동기화
  syncVideos: async () => {
    const response = await api.post('/api/youtube/videos/sync');
    return response.data;
  },

  // 동영상 상세 조회
  getVideoDetail: async (videoId) => {
    const response = await api.get(`/api/youtube/videos/${videoId}`);
    return response.data;
  },

  // 동영상 업로드
  uploadVideo: async (formData) => {
    const response = await api.post('/api/youtube/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000, // 10분 타임아웃
    });
    return response.data;
  },

  // 동영상 수정
  updateVideo: async (videoId, data) => {
    const response = await api.put(`/api/youtube/videos/${videoId}`, data);
    return response.data;
  },

  // 동영상 삭제
  deleteVideo: async (videoId) => {
    const response = await api.delete(`/api/youtube/videos/${videoId}`);
    return response.data;
  },

  // 채널 분석 데이터
  getChannelAnalytics: async (startDate, endDate) => {
    const response = await api.get(`/api/youtube/analytics/channel?start_date=${startDate}&end_date=${endDate}`);
    return response.data;
  },

  // 동영상 분석 데이터
  getVideoAnalytics: async (videoId, startDate, endDate) => {
    const response = await api.get(`/api/youtube/analytics/video/${videoId}?start_date=${startDate}&end_date=${endDate}`);
    return response.data;
  },

  // 트래픽 소스
  getTrafficSources: async (startDate, endDate, videoId = null) => {
    let url = `/api/youtube/analytics/traffic?start_date=${startDate}&end_date=${endDate}`;
    if (videoId) url += `&video_id=${videoId}`;
    const response = await api.get(url);
    return response.data;
  },

  // 인구통계
  getDemographics: async (startDate, endDate) => {
    const response = await api.get(`/api/youtube/analytics/demographics?start_date=${startDate}&end_date=${endDate}`);
    return response.data;
  },

  // 인기 동영상
  getTopVideos: async (startDate, endDate, maxResults = 10) => {
    const response = await api.get(`/api/youtube/analytics/top-videos?start_date=${startDate}&end_date=${endDate}&max_results=${maxResults}`);
    return response.data;
  },

  // 분석 요약 (최근 30일)
  getAnalyticsSummary: async () => {
    const response = await api.get('/api/youtube/analytics/summary');
    return response.data;
  },
};

// ==========================================
// Facebook API
// ==========================================
export const facebookAPI = {
  // 연동 상태 확인
  getStatus: async () => {
    const response = await api.get('/api/facebook/status');
    return response.data;
  },

  // 연동 해제
  disconnect: async () => {
    const response = await api.delete('/api/facebook/disconnect');
    return response.data;
  },

  // 관리하는 페이지 목록
  getPages: async () => {
    const response = await api.get('/api/facebook/pages');
    return response.data;
  },

  // 페이지 선택
  selectPage: async (pageId) => {
    const response = await api.post(`/api/facebook/select-page/${pageId}`);
    return response.data;
  },

  // 페이지 정보 새로고침
  refreshPage: async () => {
    const response = await api.post('/api/facebook/refresh-page');
    return response.data;
  },

  // 게시물 목록 조회
  getPosts: async (skip = 0, limit = 20) => {
    const response = await api.get(`/api/facebook/posts?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // 게시물 동기화
  syncPosts: async () => {
    const response = await api.post('/api/facebook/posts/sync');
    return response.data;
  },

  // 게시물 작성
  createPost: async (data) => {
    const response = await api.post('/api/facebook/posts/create', data);
    return response.data;
  },

  // 사진 게시물 작성
  createPhotoPost: async (data) => {
    const response = await api.post('/api/facebook/posts/create-photo', data);
    return response.data;
  },

  // 게시물 삭제
  deletePost: async (postId) => {
    const response = await api.delete(`/api/facebook/posts/${postId}`);
    return response.data;
  },

  // 페이지 인사이트
  getInsights: async (period = 'day', datePreset = 'last_30d') => {
    const response = await api.get(`/api/facebook/insights?period=${period}&date_preset=${datePreset}`);
    return response.data;
  },
};

// ==========================================
// Instagram API
// ==========================================
export const instagramAPI = {
  // 연동 상태 확인
  getStatus: async () => {
    const response = await api.get('/api/instagram/status');
    return response.data;
  },

  // 연동 해제
  disconnect: async () => {
    const response = await api.delete('/api/instagram/disconnect');
    return response.data;
  },

  // 연결 가능한 Instagram 계정 목록
  getAccounts: async (refresh = false) => {
    const response = await api.get(`/api/instagram/accounts?refresh=${refresh}`);
    return response.data;
  },

  // 계정 선택
  selectAccount: async (instagramUserId) => {
    const response = await api.post(`/api/instagram/select-account/${instagramUserId}`);
    return response.data;
  },

  // 계정 정보 새로고침
  refresh: async () => {
    const response = await api.post('/api/instagram/refresh');
    return response.data;
  },

  // 게시물 목록 조회
  getPosts: async (skip = 0, limit = 20) => {
    const response = await api.get(`/api/instagram/posts?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // 게시물 동기화
  syncPosts: async () => {
    const response = await api.post('/api/instagram/posts/sync');
    return response.data;
  },

  // 계정 인사이트
  getInsights: async (period = 'day') => {
    const response = await api.get(`/api/instagram/insights?period=${period}`);
    return response.data;
  },
};

// ==========================================
// AI 콘텐츠 API
// ==========================================
export const aiContentAPI = {
  // AI 콘텐츠 저장
  save: async (data) => {
    const response = await api.post('/api/ai-content/save', data);
    return response.data;
  },

  // 콘텐츠 목록 조회
  list: async (skip = 0, limit = 20) => {
    const response = await api.get(`/api/ai-content/list?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // 특정 콘텐츠 조회
  get: async (contentId) => {
    const response = await api.get(`/api/ai-content/${contentId}`);
    return response.data;
  },

  // 콘텐츠 삭제
  delete: async (contentId) => {
    const response = await api.delete(`/api/ai-content/${contentId}`);
    return response.data;
  },
};

export default api;
