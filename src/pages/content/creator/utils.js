// 콘텐츠 생성기 유틸리티 함수

/**
 * 클립보드에 텍스트 복사
 */
export const copyToClipboard = (text, message) => {
  navigator.clipboard.writeText(text);
  alert(message);
};

/**
 * 점수에 따른 색상 반환
 */
export const getScoreColor = (score) => {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#f59e0b';
  return '#ef4444';
};

/**
 * SNS 플랫폼 평균 점수 계산
 */
export const calcSnsAverageScore = (critique) => {
  if (!critique) return null;
  const scores = [critique.sns?.score, critique.x?.score, critique.threads?.score].filter(s => s != null);
  if (scores.length === 0) return null;
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
};

/**
 * 모든 플랫폼에서 태그를 모아서 중복 제거 (통합)
 */
export const collectAllTags = (textResult) => {
  if (!textResult) return [];

  const allTags = new Set();

  // 블로그 태그 (# 붙여서 통합)
  if (textResult.blog?.tags) {
    textResult.blog.tags.forEach(tag => {
      const normalizedTag = tag.startsWith('#') ? tag : `#${tag}`;
      allTags.add(normalizedTag);
    });
  }

  // SNS 해시태그
  const snsData = [textResult.sns, textResult.x, textResult.threads];
  snsData.forEach(data => {
    const tags = data?.hashtags || data?.tags || [];
    tags.forEach(tag => {
      const normalizedTag = tag.startsWith('#') ? tag : `#${tag}`;
      allTags.add(normalizedTag);
    });
  });

  return Array.from(allTags);
};

/**
 * 복사 핸들러 생성 함수
 */
export const createCopyHandler = (getData, message) => (item) => {
  const data = getData(item);
  if (data) copyToClipboard(data, message);
};

/**
 * 블로그 콘텐츠 복사 핸들러
 */
export const handleCopyBlog = createCopyHandler(
  (item) => item?.blog ? `${item.blog.title}\n\n${item.blog.content}\n\n태그: ${(item.blog.tags || []).join(', ')}` : null,
  '블로그 콘텐츠가 복사되었습니다.'
);

/**
 * SNS 콘텐츠 복사 핸들러
 */
export const handleCopySNS = createCopyHandler(
  (item) => item?.sns ? `${item.sns.content}\n\n${(item.sns.hashtags || item.sns.tags || []).join(' ')}` : null,
  'SNS 콘텐츠가 복사되었습니다.'
);

/**
 * X 콘텐츠 복사 핸들러
 */
export const handleCopyX = createCopyHandler(
  (item) => item?.x ? `${item.x.content}\n\n${(item.x.hashtags || item.x.tags || []).join(' ')}` : null,
  'X 콘텐츠가 복사되었습니다.'
);

/**
 * Threads 콘텐츠 복사 핸들러
 */
export const handleCopyThreads = createCopyHandler(
  (item) => item?.threads ? `${item.threads.content}\n\n${(item.threads.hashtags || item.threads.tags || []).join(' ')}` : null,
  'Threads 콘텐츠가 복사되었습니다.'
);
