// 콘텐츠 생성기 상수 정의

export const PLATFORMS = [
  { id: 'blog', label: '블로그' },
  { id: 'sns', label: 'Instagram/Facebook' },
  { id: 'x', label: 'X' },
  { id: 'threads', label: 'Threads' },
];

export const VIDEO_DURATION_OPTIONS = [
  { id: 'short', label: 'Short', duration: '15초', cuts: 3, description: '빠른 임팩트', credits: 10 },
  { id: 'standard', label: 'Standard', duration: '30초', cuts: 5, description: '균형잡힌 구성', credits: 20 },
  { id: 'premium', label: 'Premium', duration: '60초', cuts: 8, description: '상세한 스토리', credits: 35 },
];

// 크레딧 비용 상수
export const CREDIT_COSTS = {
  ai_image: 2,      // AI 이미지 1장당
  cardnews: 5,      // 카드뉴스 생성
};

export const CONTENT_TYPES = [
  { id: 'text', label: '글만', desc: '블로그, SNS 캡션', icon: '📝' },
  { id: 'image', label: '이미지만', desc: '썸네일, 배너', icon: '🖼️' },
  { id: 'both', label: '글 + 이미지', desc: '완성 콘텐츠', icon: '✨', recommended: true },
  { id: 'shortform', label: '숏폼 영상', desc: '마케팅 비디오', icon: '🎬' },
];

export const IMAGE_COUNTS = [1, 2, 3, 4, 5, 6, 7, 8];

export const IMAGE_FORMATS = [
  { id: 'ai-image', label: 'AI 이미지' },
  { id: 'cardnews', label: '카드뉴스' },
];

export const ASPECT_RATIOS = [
  { id: '1:1', label: '정사각형 (1:1)', desc: '인스타그램 피드' },
  { id: '4:5', label: '세로형 (4:5)', desc: '인스타그램 세로 피드' },
  { id: '1.91:1', label: '가로형 (1.91:1)', desc: '페이스북, 트위터' },
];

export const QUICK_TOPICS = ['신제품 출시', '이벤트 안내', '후기 소개', '브랜드 소개'];

// 플랫폼 설정
export const PLATFORM_CONFIG = {
  blog: { title: '네이버 블로그' },
  sns: { title: 'Instagram / Facebook' },
  x: { title: 'X' },
  threads: { title: 'Threads' },
};
