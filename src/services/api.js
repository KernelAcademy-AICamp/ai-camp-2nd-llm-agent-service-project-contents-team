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

  // 토큰 갱신 (세션 연장)
  refreshToken: async () => {
    const response = await api.post('/api/auth/refresh-token');
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
// X API
// ==========================================
export const xAPI = {
  // 연동 상태 확인
  getStatus: async () => {
    const response = await api.get('/api/x/status');
    return response.data;
  },

  // 연동 해제
  disconnect: async () => {
    const response = await api.delete('/api/x/disconnect');
    return response.data;
  },

  // 계정 정보 새로고침
  refresh: async () => {
    const response = await api.post('/api/x/refresh');
    return response.data;
  },

  // 포스트 목록 조회
  getPosts: async (skip = 0, limit = 20) => {
    const response = await api.get(`/api/x/posts?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // 포스트 동기화
  syncPosts: async () => {
    const response = await api.post('/api/x/posts/sync');
    return response.data;
  },

  // 포스트 작성
  createPost: async (data) => {
    const response = await api.post('/api/x/posts/create', data);
    return response.data;
  },

  // 이미지 포스트 작성
  createMediaPost: async (formData) => {
    const response = await api.post('/api/x/posts/create-media', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // 포스트 삭제
  deletePost: async (postId) => {
    const response = await api.delete(`/api/x/posts/${postId}`);
    return response.data;
  },

  // 계정 분석 데이터
  getAnalytics: async () => {
    const response = await api.get('/api/x/analytics');
    return response.data;
  },
};

// ==========================================
// Threads API
// ==========================================
export const threadsAPI = {
  // 연동 상태 확인
  getStatus: async () => {
    const response = await api.get('/api/threads/status');
    return response.data;
  },

  // 연동 해제
  disconnect: async () => {
    const response = await api.delete('/api/threads/disconnect');
    return response.data;
  },

  // 계정 정보 새로고침
  refresh: async () => {
    const response = await api.post('/api/threads/refresh');
    return response.data;
  },

  // 포스트 목록 조회
  getPosts: async (skip = 0, limit = 20) => {
    const response = await api.get(`/api/threads/posts?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // 포스트 동기화
  syncPosts: async () => {
    const response = await api.post('/api/threads/posts/sync');
    return response.data;
  },

  // 포스트 작성
  createPost: async (data) => {
    const response = await api.post('/api/threads/posts/create', data);
    return response.data;
  },

  // 계정 분석 데이터
  getAnalytics: async () => {
    const response = await api.get('/api/threads/analytics');
    return response.data;
  },
};

// ==========================================
// TikTok API
// ==========================================
export const tiktokAPI = {
  // 연동 상태 확인
  getStatus: async () => {
    const response = await api.get('/api/tiktok/status');
    return response.data;
  },

  // 연동 해제
  disconnect: async () => {
    const response = await api.delete('/api/tiktok/disconnect');
    return response.data;
  },

  // 계정 정보 새로고침
  refresh: async () => {
    const response = await api.post('/api/tiktok/refresh');
    return response.data;
  },

  // 동영상 목록 조회
  getVideos: async (skip = 0, limit = 20) => {
    const response = await api.get(`/api/tiktok/videos?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // 동영상 동기화
  syncVideos: async () => {
    const response = await api.post('/api/tiktok/videos/sync');
    return response.data;
  },

  // 동영상 업로드
  uploadVideo: async (data) => {
    const response = await api.post('/api/tiktok/videos/upload', data);
    return response.data;
  },

  // 분석 데이터
  getAnalytics: async () => {
    const response = await api.get('/api/tiktok/analytics');
    return response.data;
  },
};

// ==========================================
// WordPress API
// ==========================================
export const wordpressAPI = {
  // 연동
  connect: async (data) => {
    const response = await api.post('/api/wordpress/connect', data);
    return response.data;
  },

  // 연동 상태 확인
  getStatus: async () => {
    const response = await api.get('/api/wordpress/status');
    return response.data;
  },

  // 연동 해제
  disconnect: async () => {
    const response = await api.delete('/api/wordpress/disconnect');
    return response.data;
  },

  // 사이트 정보 새로고침
  refresh: async () => {
    const response = await api.post('/api/wordpress/refresh');
    return response.data;
  },

  // 카테고리 목록
  getCategories: async () => {
    const response = await api.get('/api/wordpress/categories');
    return response.data;
  },

  // 글 목록 조회
  getPosts: async (skip = 0, limit = 20) => {
    const response = await api.get(`/api/wordpress/posts?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // 글 동기화
  syncPosts: async () => {
    const response = await api.post('/api/wordpress/posts/sync');
    return response.data;
  },

  // 글 작성
  createPost: async (data) => {
    const response = await api.post('/api/wordpress/posts/create', data);
    return response.data;
  },

  // 글 수정
  updatePost: async (postId, data) => {
    const response = await api.put(`/api/wordpress/posts/${postId}`, data);
    return response.data;
  },

  // 글 삭제
  deletePost: async (postId) => {
    const response = await api.delete(`/api/wordpress/posts/${postId}`);
    return response.data;
  },

  // 미디어 업로드
  uploadMedia: async (formData) => {
    const response = await api.post('/api/wordpress/media/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // 분석 데이터
  getAnalytics: async () => {
    const response = await api.get('/api/wordpress/analytics');
    return response.data;
  },

  // 통계 API 가용 여부 확인 (Jetpack/WP Statistics)
  checkStatsAvailability: async () => {
    const response = await api.get('/api/wordpress/stats/check');
    return response.data;
  },

  // 사이트 통계 조회
  getStats: async (period = 'week') => {
    const response = await api.get(`/api/wordpress/stats?period=${period}`);
    return response.data;
  },

  // 인기 게시물 통계
  getPostStats: async (limit = 10) => {
    const response = await api.get(`/api/wordpress/stats/posts?limit=${limit}`);
    return response.data;
  },
};

// ==========================================
// AI 콘텐츠 API (레거시)
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

// ==========================================
// AI 콘텐츠 API v2 (플랫폼별 분리 저장)
// ==========================================
export const contentSessionAPI = {
  // 콘텐츠 세션 저장
  save: async (data) => {
    const response = await api.post('/api/ai-content/v2/save', data);
    return response.data;
  },

  // 세션 목록 조회
  list: async (skip = 0, limit = 20) => {
    const response = await api.get(`/api/ai-content/v2/list?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // 특정 세션 조회
  get: async (sessionId) => {
    const response = await api.get(`/api/ai-content/v2/${sessionId}`);
    return response.data;
  },

  // 세션 삭제
  delete: async (sessionId) => {
    const response = await api.delete(`/api/ai-content/v2/${sessionId}`);
    return response.data;
  },
};

// ==========================================
// 카드뉴스 API
// ==========================================
export const cardnewsAPI = {
  // 디자인 템플릿 목록 조회 (기존 + 새 템플릿 통합)
  getDesignTemplates: async () => {
    const response = await api.get('/api/cardnews/design-templates');
    return response.data;
  },

  // 카테고리별 그룹화된 개선된 템플릿 목록 조회
  getDesignTemplatesV2: async () => {
    const response = await api.get('/api/cardnews/design-templates-v2');
    return response.data;
  },

  // 특정 템플릿 상세 정보 조회
  getTemplateDetail: async (templateId) => {
    const response = await api.get(`/api/cardnews/design-templates/${templateId}`);
    return response.data;
  },

  // 템플릿 카테고리 목록 조회
  getTemplateCategories: async () => {
    const response = await api.get('/api/cardnews/template-categories');
    return response.data;
  },
};

// ==========================================
// SNS 발행 콘텐츠 API
// ==========================================
export const snsContentAPI = {
  // SNS 콘텐츠 저장
  save: async (data) => {
    const response = await api.post('/api/sns-content/save', data);
    return response.data;
  },

  // 콘텐츠 목록 조회 (플랫폼 필터 가능)
  list: async (platform = null, skip = 0, limit = 20) => {
    let url = `/api/sns-content/list?skip=${skip}&limit=${limit}`;
    if (platform) url += `&platform=${platform}`;
    const response = await api.get(url);
    return response.data;
  },

  // 특정 콘텐츠 조회
  get: async (contentId) => {
    const response = await api.get(`/api/sns-content/${contentId}`);
    return response.data;
  },

  // 콘텐츠 삭제
  delete: async (contentId) => {
    const response = await api.delete(`/api/sns-content/${contentId}`);
    return response.data;
  },
};

// ==========================================
// 발행 콘텐츠 API (임시저장, 예약발행, 발행)
// ==========================================
export const publishedContentAPI = {
  // 임시저장
  saveDraft: async (data) => {
    const response = await api.post('/api/published-contents/draft', data);
    return response.data;
  },

  // 예약발행
  schedule: async (data) => {
    const response = await api.post('/api/published-contents/schedule', data);
    return response.data;
  },

  // 즉시 발행
  publish: async (contentId) => {
    const response = await api.post(`/api/published-contents/publish/${contentId}`);
    return response.data;
  },

  // 목록 조회 (상태/플랫폼 필터 가능)
  list: async (status = null, platform = null, skip = 0, limit = 20) => {
    let url = `/api/published-contents?skip=${skip}&limit=${limit}`;
    if (status) url += `&status=${status}`;
    if (platform) url += `&platform=${platform}`;
    const response = await api.get(url);
    return response.data;
  },

  // 상태별 통계
  getStats: async () => {
    const response = await api.get('/api/published-contents/stats');
    return response.data;
  },

  // 상세 조회
  get: async (contentId) => {
    const response = await api.get(`/api/published-contents/${contentId}`);
    return response.data;
  },

  // 수정
  update: async (contentId, data) => {
    const response = await api.put(`/api/published-contents/${contentId}`, data);
    return response.data;
  },

  // 삭제
  delete: async (contentId) => {
    const response = await api.delete(`/api/published-contents/${contentId}`);
    return response.data;
  },

  // 예약 취소
  cancelSchedule: async (contentId) => {
    const response = await api.post(`/api/published-contents/${contentId}/cancel-schedule`);
    return response.data;
  },

  // 세션에서 발행 콘텐츠 생성 (편집하기)
  createFromSession: async (sessionId, platform) => {
    const response = await api.post(`/api/published-contents/from-session/${sessionId}?platform=${platform}`);
    return response.data;
  },

  // 이미지 업로드 (Instagram/SNS 발행용)
  uploadImage: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/published-contents/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 카드뉴스 SNS 발행 (Instagram/Facebook/Threads)
  publishCardnews: async (data) => {
    const response = await api.post('/api/published-contents/publish-cardnews', data);
    return response.data;
  },
};

// ==========================================
// Dashboard API (통합 상태 조회)
// ==========================================
export const dashboardAPI = {
  // 모든 플랫폼 상태 한 번에 조회
  getAllStatus: async () => {
    const response = await api.get('/api/dashboard/status');
    return response.data;
  },
};

// ==========================================
// 크레딧 API
// ==========================================
export const creditsAPI = {
  // 잔액 조회
  getBalance: async () => {
    const response = await api.get('/api/credits/balance');
    return response.data;
  },

  // 잔액 충분한지 확인
  checkBalance: async (amount) => {
    const response = await api.get(`/api/credits/check/${amount}`);
    return response.data;
  },

  // 패키지 목록 조회
  getPackages: async () => {
    const response = await api.get('/api/credits/packages');
    return response.data;
  },

  // 거래 내역 조회
  getTransactions: async (limit = 50, offset = 0, type = null) => {
    let url = `/api/credits/transactions?limit=${limit}&offset=${offset}`;
    if (type) url += `&transaction_type=${type}`;
    const response = await api.get(url);
    return response.data;
  },

  // 크레딧 충전 (테스트용)
  charge: async (packageId) => {
    const response = await api.post('/api/credits/charge', { package_id: packageId });
    return response.data;
  },

  // 크레딧 사용
  use: async (amount, description, referenceType = null, referenceId = null) => {
    const response = await api.post('/api/credits/use', {
      amount,
      description,
      reference_type: referenceType,
      reference_id: referenceId,
    });
    return response.data;
  },

  // 회원가입 보너스 받기
  claimSignupBonus: async () => {
    const response = await api.post('/api/credits/bonus/signup');
    return response.data;
  },

  // 크레딧 비용 조회
  getCosts: async () => {
    const response = await api.get('/api/credits/costs');
    return response.data;
  },
};

// ==========================================
// 사용자 API
// ==========================================
export const userAPI = {
  // 프로필 조회 (기본)
  getProfile: async () => {
    const response = await api.get('/api/user/profile');
    return response.data;
  },

  // 콘텐츠 생성용 컨텍스트 조회 (브랜드 분석 포함)
  getContext: async () => {
    const response = await api.get('/api/user/context');
    return response.data;
  },

  // 프로필 업데이트
  updateProfile: async (data) => {
    const response = await api.put('/api/user/profile', data);
    return response.data;
  },
};

// ==========================================
// Generated Videos API
// ==========================================
export const generatedVideoAPI = {
  // 생성된 비디오 목록 조회
  list: async (skip = 0, limit = 20) => {
    const response = await api.get(`/api/generated-videos?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // 특정 세션의 비디오 조회
  get: async (sessionId) => {
    const response = await api.get(`/api/generated-videos/${sessionId}`);
    return response.data;
  },
};

// 호환성을 위한 별칭 (기존 코드에서 twitterAPI 사용하는 경우)
export const twitterAPI = xAPI;

// ==========================================
// 템플릿 갤러리 API
// ==========================================
export const templatesAPI = {
  // 탭 목록 조회
  getTabs: async () => {
    const response = await api.get('/templates/tabs');
    return response.data;
  },

  // 탭 생성
  createTab: async (data) => {
    const response = await api.post('/templates/tabs', data);
    return response.data;
  },

  // 탭 수정
  updateTab: async (tabId, data) => {
    const response = await api.put(`/templates/tabs/${tabId}`, data);
    return response.data;
  },

  // 탭 삭제
  deleteTab: async (tabId) => {
    const response = await api.delete(`/templates/tabs/${tabId}`);
    return response.data;
  },

  // 템플릿 목록 조회 (탭별 필터링 가능)
  getTemplates: async (tabId = null) => {
    const params = tabId ? { tab_id: tabId } : {};
    const response = await api.get('/templates/', { params });
    return response.data;
  },

  // 템플릿 생성
  createTemplate: async (data) => {
    const response = await api.post('/templates/', data);
    return response.data;
  },

  // 템플릿 수정
  updateTemplate: async (templateId, data) => {
    const response = await api.put(`/templates/${templateId}`, data);
    return response.data;
  },

  // 템플릿 삭제
  deleteTemplate: async (templateId) => {
    const response = await api.delete(`/templates/${templateId}`);
    return response.data;
  },

  // 템플릿 사용 (사용 횟수 증가)
  useTemplate: async (templateId) => {
    const response = await api.post(`/templates/${templateId}/use`);
    return response.data;
  },

  // 템플릿 복제
  duplicateTemplate: async (templateId) => {
    const response = await api.post(`/templates/${templateId}/duplicate`);
    return response.data;
  },
};

export default api;
